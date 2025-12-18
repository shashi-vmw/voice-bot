# ipo_mcp_server.py
import asyncio
import json
from typing import List, Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
import ipo_data

# Initialize FastMCP Server
mcp = FastMCP("Groww-IPO-Service")

# --- TOOLS (Function Calling) ---

@mcp.tool()
def get_user_applications(user_id: str = "u123") -> Dict[str, Any]:
    """
    Fetches the COMPLETE list of IPO applications for the current user.
    Returns a dictionary containing a list of ALL applications found with status, amount, and dates.
    """
    # Force return ALL applications wrapped in a dict to ensure list structure is preserved
    return {"applications": ipo_data.USER_APPLICATIONS}

@mcp.tool()
def get_active_ipos() -> Dict[str, Any]:
    """
    Fetches a list of ALL currently OPEN (Active) IPOs available for bidding.
    Returns a dictionary containing a list of active IPOs.
    """
    return {"active_ipos": ipo_data.ACTIVE_IPOS}

@mcp.tool()
def get_upcoming_ipos() -> Dict[str, Any]:
    """
    Fetches a list of Upcoming IPOs that are not yet open for bidding.
    Returns a dictionary containing a list of upcoming IPOs.
    """
    return {"upcoming_ipos": ipo_data.UPCOMING_IPOS}

@mcp.tool()
def get_closed_ipos() -> Dict[str, Any]:
    """
    Fetches a list of Closed IPOs to check past listing or allotment dates.
    Returns a dictionary containing a list of closed IPOs.
    """
    return {"closed_ipos": ipo_data.CLOSED_IPOS}

@mcp.tool()
def get_ipo_specific_details(symbol: str) -> str:
    """
    Fetches detailed information (lot size, price range, dates, SME status) for a specific IPO.
    Args:
        symbol: The IPO symbol (e.g., INTERARCH)
    """
    ipo = next((i for i in ipo_data.ACTIVE_IPOS + ipo_data.UPCOMING_IPOS if i['symbol'].upper() == symbol.upper()), None)
    if not ipo:
        return f"Error: IPO {symbol} not found in active or upcoming list."
    
    # Check for SME specific rule (min 2 lots)
    if ipo.get('isSme'):
        sme_rule = f"NOTE: This is an SME IPO. Minimum application is 2 lots (Shares: {ipo.get('minBidQuantity', ipo['lotSize'] * 2)})."
    else:
        sme_rule = "This is a regular IPO."

    return json.dumps({
        "IPO": ipo.get("growwShortName"),
        "Status": ipo.get("status"),
        "BiddingDates": ipo.get("biddingDates"),
        "PriceRange": ipo.get("priceRange"),
        "LotSize": ipo.get("lotSize"),
        "SmeRule": sme_rule,
        "AllotmentDate": ipo.get("allotmentDate"),
        "ListingDate": ipo.get("listingDate")
    })

@mcp.tool()
def get_common_query_answer(query_key: str) -> str:
    """
    Retrieves detailed, narrative answers for common procedural queries (e.g., cancellation, mandate approval).
    Args:
        query_key: Key representing the query type (e.g., 'cancel_application', 'allotment_announced').
    """
    return ipo_data.COMMON_QUERY_ANSWERS.get(query_key, "Query not classified or answer not available.")

@mcp.tool()
def escalate_to_agent(reason: str) -> str:
    """
    Triggers a handover to a human Customer Support Champion.
    Use this if the user is angry, abusive, or the query is outside IPO context.
    """
    return f"ESCALATION_TRIGGERED: {reason}. Transferring call to Groww's Customer Support Champion."

# --- RESOURCES (Context) ---

@mcp.resource("ipo://compliance/guardrails")
def get_compliance_rules() -> str:
    """Returns strict behavioral guardrails."""
    return ipo_data.COMPLIANCE_GUARDRAILS

@mcp.resource("ipo://logic/business_rules")
def get_business_rules() -> str:
    """Returns core business logic."""
    return ipo_data.BUSINESS_LOGIC

@mcp.resource("ipo://procedure/pre_apply")
def get_pre_apply_journey() -> str:
    """Returns the step-by-step process for the pre-apply and general IPO journey on the app."""
    return ipo_data.USER_JOURNEY_PRE_APPLY

@mcp.resource("ipo://procedure/application_upi")
def get_application_procedure():
    """Returns the step-by-step process for placing an IPO application using UPI."""
    return ipo_data.APPLICATION_PROCEDURE_UPI

@mcp.resource("ipo://procedure/post_apply")
def get_post_apply_procedure():
    """Returns the step-by-step process for mandate approval and tracking status."""
    return ipo_data.POST_APPLY_PROCEDURE

if __name__ == "__main__":
    mcp.run()