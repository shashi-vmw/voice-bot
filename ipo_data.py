# ipo_data.py
"""
This file contains the MOCK DATA derived strictly from the 'For Vendor _ IPO Context Doc.pdf'.
It serves as the 'database' for the MCP Server.
"""

from typing import List, Dict, Any

# --- MOCK DATABASE (Derived from PDF Pages 8-26) ---

# API 1: User's Applied IPOs
USER_APPLICATIONS: List[Dict[str, Any]] = [
    {
        "symbol": "INTERARCH",
        "companyName": "Interarch Building Products",
        "status": "PAYMENT_PENDING", # Case 1: Mandate waiting
        "paymentStatus": "PENDING",
        "title": "Approve request on Groww UPI",
        "remark": "Please wait for UPI request.",
        "category": "IND",
        "appliedAsLabel": "Regular",
        "amount": 14400,
        "canCancel": True,
        "upiId": "8942052094@yesg"
    },
    {
        "symbol": "SUNTECHELEC",
        "companyName": "Suntech Electronics",
        "status": "NOT_ALLOTED", # Case 2: Failed/Not Allotted - Refund due
        "paymentStatus": "SUCCESS",
        "title": "IPO Not Allotted",
        "remark": "Amount will be released by the bank.",
        "category": "IND",
        "appliedAsLabel": "Regular",
        "amount": 5500,
        "canCancel": False,
        "refundInitiationDate": "2024-08-26",
        "upiId": "9123000001@upi"
    },
    {
        "symbol": "URBANGREEN",
        "companyName": "Urban Green Infra (SME)",
        "status": "APPROVED", # Case 3: In Progress, Mandate approved
        "paymentStatus": "SUCCESS",
        "title": "Application Accepted by Exchange",
        "remark": "Waiting for allotment date.",
        "category": "HNI",
        "appliedAsLabel": "HNI",
        "amount": 250000,
        "canCancel": False, # HNI cannot be cancelled
        "upiId": "9988776655@icici"
    }
]

# API 3: Active IPOs (Including SME)
ACTIVE_IPOS: List[Dict[str, Any]] = [
    {
        "symbol": "INTERARCH",
        "growwShortName": "Interarch Building Products",
        "status": "ACTIVE",
        "biddingDates": "Aug 19 - Aug 21, 2024",
        "priceRange": "₹850 - ₹900",
        "lotSize": 16,
        "isSme": False,
        "allotmentDate": "2024-08-22",
        "listingDate": "2024-08-26"
    },
    {
        "symbol": "RURALFIN",
        "growwShortName": "Rural Finserve Limited (SME)",
        "status": "ACTIVE",
        "biddingDates": "Aug 18 - Aug 20, 2024",
        "priceRange": "₹160 - ₹165",
        "lotSize": 35,
        "minBidQuantity": 70, # 2 lots minimum for SME
        "isSme": True,
        "allotmentDate": "2024-08-21",
        "listingDate": "2024-08-26"
    }
]

# API 2: Upcoming IPOs
UPCOMING_IPOS: List[Dict[str, Any]] = [
    {
        "symbol": "NOVAFOODS",
        "growwShortName": "Nova Foods Limited",
        "status": "UPCOMING",
        "biddingDates": "Dec 02 - Dec 04, 2024",
        "priceRange": "₹95 - ₹100",
        "lotSize": 40,
        "preApplyOpen": True
    }
]

# API 4: Closed IPOs
CLOSED_IPOS: List[Dict[str, Any]] = [
    {
        "symbol": "HEALTHPLUS",
        "growwShortName": "HealthPlus Hospitals",
        "status": "CLOSED",
        "listingStatus": "LISTED",
        "allotmentDate": "2024-06-10"
    }
]

# --- STATIC CONTENT RESOURCES (PDF Text/Compliance) ---

COMPLIANCE_GUARDRAILS = """
*** CRITICAL COMPLIANCE RULES ***
1. MANDATORY INTRODUCTION: Always start in clear Indian English (en-IN) with "Hi, I'm IPO Advisor from Groww and I will try my best to provide solution to your question. How can I help you today? Please also let me know the language in which you would like to communicate."
2. TONE: Maintain a calm, polite, empathetic, and non-argumentative tone.
3. ADVISORY: Never give investment advice or opinions on individual companies.
4. TECHNICAL BLAME: Never mention phrases like 'technical issue', 'glitch', or 'technical problem in App'.
5. ESCALATION: If user shows agitation/anger/abusive language, transfer call to human agent.
"""

BUSINESS_LOGIC = """
*** IPO BUSINESS LOGIC ***
1. ALLOTMENT: IPO allotment is done on a lottery basis by the RTA. Groww cannot guarantee allotment.
2. FUNDS: Amount is only BLOCKED (lien/hold) by the bank, not deducted until allotment. For details about lien/hold, ask the user to contact their bank.
3. TIMINGS: 
   - Application Window: 10:00 am to 5:00 pm (Exchange). Groww keeps a 10 min buffer (4:50 pm cut-off).
   - Pre-Apply: Applications are placed on the exchange on the bidding start day.
4. MANDATE: UPI mandate request is facilitated by NPCI via the Exchange. Check your UPI app. Groww UPI mandate approval can be done within the Groww App.
5. CANCELLATION:
   - Allowed only during the bidding period.
   - HNI Category applications CANNOT be cancelled.
   - If cancelled post-mandate approval: The amount is released by the bank on the mandate expiry date. User can manually cancel the mandate from UPI App or contact the bank for early release.
6. SME IPO: User must apply for a minimum of 2 lots.
7. STATUS UPDATE: IPO application status on Groww is updated at the 'End of the Day' based on updates from the exchange.
"""

# New Resource: User Journey (Page 1)
USER_JOURNEY_PRE_APPLY = """
The Pre-Apply Journey is: 
1. Open Groww App. 
2. Go to 'Explore' under 'Stocks'. 
3. Scroll down to 'Product and tools'. 
4. Select 'IPO'. 
5. Browse the sections: Open (Active), Applied, Closed, and Upcoming.
"""

# New Resource: Application Procedure (Page 1)
APPLICATION_PROCEDURE_UPI = """
The steps for Placing an Application using UPI are: 
1. Go to the 'Open' section. 
2. Choose the company and click 'Apply for IPO'. 
3. Verify the category (default is 'Regular'). 
4. Set the number of 'Shares' or 'Lots' you want to apply for. 
5. You can click 'Add Bid' to add up to 3 bids. 
6. Click on 'Apply'. You will then receive a UPI mandate request.
"""

# New Resource: Post-Apply Procedure (Page 2)
POST_APPLY_PROCEDURE = """
The Post-Apply Journey (Tracking and Mandate Approval) is:
1. Go to the 'Applied' section.
2. Choose the application to Track the Application Status.
3. Once processed by the Exchange, you will receive a mandate request.
4. Approve the mandate: If your UPI ID ends in "@yesg", approve it from the Groww App UPI section. If not, approve it from your respective UPI App.
5. Wait for the allotment announcement.
"""

# New Resource: Common Query Answers (Page 5)
COMMON_QUERY_ANSWERS = {
    "cancel_application": "To cancel your IPO application, go to the 'Applied' section, select the application, and click 'Cancel'. Remember, cancellation is only possible during the bidding period, and HNI applications cannot be cancelled. [Image of the IPO cancellation process flow chart]",
    "mandate_not_come": "If your mandate hasn't arrived, please wait till the end of the bidding day. Mandates are issued by NPCI via the Exchange. If the bidding period has closed, you will not receive a mandate.",
    "allotment_announced": "The allotment date is specific to each IPO. You can check the details on the IPO listing page. For example, for INTERARCH, the allotment date is 2024-08-22.",
    "status_pending": "If the status shows 'Payment Pending' but the amount is blocked, this means the mandate was accepted by your bank, but the exchange status update is delayed. Please wait till the 'End of the Day' for the status to reflect the update from the exchange.",
    "approved_old_mandate": "If you approved the mandate for a cancelled application by mistake, you can manually cancel the mandate from your UPI App or contact your bank immediately. The blocked amount will be released by the bank on the mandate expiry date.",
    "rejected_reason": "IPO applications are typically rejected due to reasons like: incorrect Demat ID, UPI mandate failure, or a name mismatch between your bank account and Groww account (though name mismatch usually affects MF, not IPO). Allotment itself is a lottery and not guaranteed."
}