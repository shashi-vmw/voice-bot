# main.py
import asyncio
import os
import sys
import json
import base64
import logging
import numpy as np
from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# VAD Imports
import torch

# Google GenAI & ADK Imports
from google import genai
from google.genai import types
from google.adk.agents import Agent

# MCP Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GrowwBot")

# Configuration
MCP_SERVER_SCRIPT = "ipo_mcp_server.py"
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

if not GOOGLE_CLOUD_PROJECT:
    logger.error("CRITICAL: GOOGLE_CLOUD_PROJECT must be set for Vertex AI")

# --- VAD Setup (Silero) ---
# Load model globally to avoid reloading on every connection
try:
    logger.info("Loading Silero VAD Model...")
    model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                  model='silero_vad',
                                  force_reload=False,
                                  trust_repo=True)
    (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils
    logger.info("✅ Silero VAD Loaded")
except Exception as e:
    logger.error(f"Failed to load Silero VAD: {e}")
    model = None

# --- FastAPI Setup ---
templates = Jinja2Templates(directory="templates")
app = FastAPI()

# --- Helper: Audio Conversion ---
def int2float(sound):
    """
    Convert Int16 byte array to Float32 Tensor normalized between -1 and 1
    Required for Silero VAD input.
    """
    # Convert bytes to numpy int16
    audio_int16 = np.frombuffer(sound, dtype=np.int16)
    # Normalize to float32
    audio_float32 = audio_int16.astype('float32')
    
    abs_max = np.abs(audio_int16).max()
    if abs_max > 0:
        audio_float32 *= 1 / 32768.0 # Normalize to [-1, 1]
    
    audio_float32 = audio_float32.squeeze()
    return torch.from_numpy(audio_float32)

# --- Helper: Build ADK Agent & Tool Config ---
async def build_agent_and_tools(session):
    """
    1. Fetches tools/resources from MCP.
    2. Constructs a google.adk.agents.Agent object.
    3. Returns the raw tool declarations for the Live API.
    """
    logger.info("Initializing MCP Session...")
    await session.initialize()
    
    logger.info("Listing MCP Tools...")
    mcp_tools = await session.list_tools()
    
    function_declarations = []
    for tool in mcp_tools.tools:
        schema = tool.inputSchema.copy()
        if "type" not in schema:
            schema["type"] = "object"
            
        function_declarations.append({
            "name": tool.name,
            "description": tool.description,
            "parameters": schema
        })
    
    logger.info("Reading MCP Resources...")
    try:
        compliance = await session.read_resource("ipo://compliance/guardrails")
        logic = await session.read_resource("ipo://logic/business_rules")
        pre_apply_proc = await session.read_resource("ipo://procedure/pre_apply")
        app_proc_upi = await session.read_resource("ipo://procedure/application_upi")
        post_apply_proc = await session.read_resource("ipo://procedure/post_apply")
        
        context_text = f"--- COMPLIANCE ---\n{compliance.contents[0].text}\n--- PROCEDURES ---\n{logic.contents[0].text}\n{pre_apply_proc.contents[0].text}\n{app_proc_upi.contents[0].text}\n{post_apply_proc.contents[0].text}"
    except Exception as e:
        logger.warning(f"Resources unavailable: {e}")
        context_text = "Follow standard IPO guidelines."

    system_prompt = f"""
    IMPORTANT: Use clear Indian English (en-IN) to start with.
    You are the official Groww IPO Voice Assistant. Use clear Indian English (en-IN)and you should sound as human as possible to the extent that noone should be able to figure out that you are an AI bot. 
    Your persona must be calm, polite, empathetic, not too formal and non-argumentative at all times.
    
    CORE CONTEXT & RULES:
    {context_text}
    
    GUIDELINES:
    1. DATA SOURCE TRUTH: You must ONLY use the data provided via the Tools. Do NOT hallucinate.
    2. TOOL USAGE: Call tools like `get_user_applications` without arguments unless specific filters are requested.
    3. LIST HANDLING: If a tool returns multiple items, speak details of EVERY SINGLE ITEM.
    4. RESPONSE STYLE: Keep general conversational responses concise. When fetching data, always inform the customer to wait while you are processing.
    5. HINDI GRAMMAR: When speaking in English, use clear Indian English (en-IN). When speaking in Hindi, you MUST strictly use correct grammatical forms.
    6. ESCALATION: Use the 'escalate_to_agent' tool if necessary.
    """

    agent = Agent(
        name="groww_ipo_bot",
        model="gemini-live-2.5-flash-native-audio",
        instruction=system_prompt
    )
    
    return agent, function_declarations

# --- WebSocket Endpoint ---
@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("✅ Client Connected to WebSocket")

    server_params = StdioServerParameters(command=sys.executable, args=[MCP_SERVER_SCRIPT])
    
    # Initialize VAD Iterator for this session
    vad_iterator = VADIterator(model) if model else None
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as mcp_session:
                
                try:
                    adk_agent, func_declarations = await build_agent_and_tools(mcp_session)
                except Exception as e:
                    logger.error(f"Failed to build ADK Agent: {e}")
                    await websocket.close(code=1011)
                    return

                client = genai.Client(
                    vertexai=True,
                    project=GOOGLE_CLOUD_PROJECT,
                    location=GOOGLE_CLOUD_LOCATION,
                    http_options={'api_version': 'v1beta1'}
                )
                
                config = {
                    "tools": [{"function_declarations": func_declarations}],
                    "response_modalities": ["AUDIO"],
                    "system_instruction": adk_agent.instruction,
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {
                                "voice_name": "Alnilam"
                            }
                        }
                    }
                }

                MODEL_ID = adk_agent.model
                logger.info(f"Connecting to Agent Model: {MODEL_ID}...")
                
                try:
                    async with client.aio.live.connect(model=MODEL_ID, config=config) as gemini_session:
                        logger.info("✅ Connected to Gemini Live API (Vertex)")
                        
                        # --- Task A: Gemini -> User ---
                        async def receive_from_gemini():
                            try:
                                while True:
                                    async for response in gemini_session.receive():
                                        if response.server_content:
                                            model_turn = response.server_content.model_turn
                                            if model_turn:
                                                for part in model_turn.parts:
                                                    if part.inline_data:
                                                        b64_audio = base64.b64encode(part.inline_data.data).decode("utf-8")
                                                        await websocket.send_json({"type": "audio", "data": b64_audio})

                                        if response.tool_call:
                                            for call in response.tool_call.function_calls:
                                                name = call.name
                                                args = call.args
                                                call_id = call.id
                                                logger.info(f"🛠️ TOOL CALL: {name} {args}")
                                                
                                                try:
                                                    result = await mcp_session.call_tool(name, arguments=args)
                                                    tool_output = result.content[0].text if result.content else str(result)
                                                    logger.info(f"✅ TOOL RESULT: {tool_output[:100]}...")

                                                    await gemini_session.send(input={"function_responses": [{
                                                        "name": name,
                                                        "response": {"result": tool_output},
                                                        "id": call_id
                                                    }]})
                                                except Exception as tool_err:
                                                    logger.error(f"❌ TOOL ERROR: {tool_err}")
                                                    await gemini_session.send(input={"function_responses": [{
                                                        "name": name,
                                                        "response": {"error": str(tool_err)},
                                                        "id": call_id
                                                    }]})

                            except Exception as e:
                                logger.error(f"Gemini Receive Error: {e}")

                        # --- Task B: User -> Gemini ---
                        async def receive_from_client():
                            if vad_iterator:
                                vad_iterator.reset_states()

                            try:
                                logger.info("Sending initial greeting...")
                                await gemini_session.send(input="Hello. Introduce yourself.", end_of_turn=True)
                                
                                # FIX: Smaller buffer for VAD (must be exactly 512 samples / 1024 bytes)
                                # But Gemini prefers larger chunks. So we keep a separate buffer for Gemini.
                                vad_chunk_size = 512 # Samples
                                vad_buffer = [] # Float32 samples
                                
                                while True:
                                    message = await websocket.receive_json()
                                    if message["type"] == "audio":
                                        try:
                                            audio_data = base64.b64decode(message["data"])
                                            
                                            # 1. Convert to Float32 Tensor for VAD
                                            tensor_audio = int2float(audio_data)
                                            
                                            # 2. Chunking for Silero (Must be exactly 512 samples)
                                            # Accumulate new samples
                                            vad_buffer.extend(tensor_audio.tolist())
                                            
                                            # Process in 512-sample blocks
                                            while len(vad_buffer) >= vad_chunk_size:
                                                chunk = torch.tensor(vad_buffer[:vad_chunk_size])
                                                vad_buffer = vad_buffer[vad_chunk_size:]
                                                
                                                if vad_iterator:
                                                    speech_dict = vad_iterator(chunk, return_seconds=True)
                                                    if speech_dict:
                                                        logger.info(f"🗣️ VAD: Speech Detected {speech_dict}")

                                            # 3. Forward original bytes to Gemini (Gemini handles buffering internally or thrives on ~4KB)
                                            # We send data immediately to minimize latency, Gemini VAD handles the rest.
                                            await gemini_session.send(input={"mime_type": "audio/pcm;rate=16000", "data": audio_data}, end_of_turn=False)

                                        except Exception as decode_err:
                                            logger.error(f"Audio Processing Error: {decode_err}")
                                            continue
                                        
                            except WebSocketDisconnect:
                                logger.info("Client Disconnected")
                            except Exception as e:
                                logger.error(f"Client Receive Error: {e}")

                        await asyncio.gather(receive_from_gemini(), receive_from_client())
                
                except Exception as e:
                    logger.error(f"Failed to connect to Gemini Live: {e}")
                    await websocket.close(code=1011)

    except Exception as e:
        logger.error(f"CRITICAL SERVER ERROR: {e}")
        await websocket.close()

@app.get("/", response_class=HTMLResponse)
async def get_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)