"""
Agent 5 — Reporting Guidance Agent
LLM: Google Gemini 2.0 Flash
Fallback: static official Indian cybercrime reporting guidance
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.services.gemini_service import call_gemini, gemini_available

OFFICIAL_RESOURCES = {
    "national_cyber_crime_portal": {
        "name": "National Cyber Crime Reporting Portal",
        "url": "https://cybercrime.gov.in/",
        "description": "Government of India's official portal for reporting all types of cybercrime.",
        "type": "official",
    },
    "financial_helpline": {
        "name": "Financial Cyber Fraud Helpline",
        "number": "1930",
        "description": "Call 1930 IMMEDIATELY for ongoing financial cyber fraud. Available 24/7.",
        "type": "emergency_helpline",
        "priority": "HIGH",
    },
    "i4c": {
        "name": "Indian Cyber Crime Coordination Centre (I4C)",
        "url": "https://i4c.mha.gov.in/",
        "description": "Ministry of Home Affairs cybercrime coordination body.",
        "type": "official",
    },
    "ceir": {
        "name": "CEIR — Lost/Stolen Phone Blocking",
        "url": "https://www.ceir.gov.in/",
        "description": "Block lost or stolen mobile devices used in fraud.",
        "type": "official",
    },
    "sachet": {
        "name": "Sachet — Financial Fraud Reporting (RBI)",
        "url": "https://sachet.rbi.org.in/",
        "description": "RBI portal for reporting financial fraud.",
        "type": "official",
    },
}

_CATEGORY_GUIDANCE = {
    "UPI Fraud": [
        "Call 1930 immediately to report financial fraud.",
        "Open your UPI app and block/freeze the account from app settings.",
        "Contact your bank's official helpline (number on back of card) to freeze transactions.",
        "File a complaint at cybercrime.gov.in selecting 'Financial Fraud'.",
        "Preserve all UPI transaction screenshots and reference numbers.",
    ],
    "Banking Fraud": [
        "Call 1930 immediately.",
        "Call your bank's 24/7 helpline to block your account.",
        "Visit your nearest bank branch with ID proof.",
        "File a complaint at cybercrime.gov.in.",
        "Change your netbanking password from a secure device.",
    ],
    "Phishing": [
        "Do NOT click any further links in the suspicious message.",
        "Change passwords for all accounts you may have accessed.",
        "Report the phishing URL at cybercrime.gov.in.",
        "Alert your bank if banking credentials may have been exposed.",
        "Enable two-factor authentication on your accounts.",
    ],
    "Fake KYC": [
        "Call 1930 immediately if any financial loss occurred.",
        "Report at cybercrime.gov.in selecting 'Online and Social Media'.",
        "Contact your bank to verify if any KYC-related changes were made.",
        "Do NOT share documents with unknown parties.",
    ],
    "default": [
        "File a complaint at the National Cyber Crime Reporting Portal: cybercrime.gov.in",
        "If financial loss occurred, call 1930 immediately.",
        "Preserve all evidence: screenshots, messages, emails.",
        "Do not share any personal information with unknown parties.",
        "Contact your bank if financial credentials may be compromised.",
    ],
}

_EVIDENCE_TO_PRESERVE = [
    "Screenshots of all suspicious messages (SMS, WhatsApp, email)",
    "Screenshot of any unauthorized transactions",
    "Name or number of the person/entity that contacted you",
    "Any website URLs you visited",
    "Date and time of each incident event",
    "Any transaction reference numbers or UTR numbers",
    "Copies of any documents you may have shared",
]


def run(incident_data: dict, intake_result: dict, scam_result: dict) -> dict:
    category      = intake_result.get("incident_category", "default")
    risk_level    = scam_result.get("risk_level", "Low Concern")
    financial_loss = float(incident_data.get("financial_loss", 0) or 0)
    ongoing       = bool(incident_data.get("ongoing_status", False))

    is_financial_emergency = (
        financial_loss > 0 or ongoing or
        "Critical" in risk_level or "High" in risk_level or
        any(kw in category.lower() for kw in ["upi", "banking", "fraud"])
    )

    steps     = _CATEGORY_GUIDANCE.get(category, _CATEGORY_GUIDANCE["default"])
    ai_steps  = None
    ai_powered = False

    if gemini_available():
        prompt = f"""You are CyberRakshak AI's Reporting Guidance Agent for cybercrime in Bengaluru, India.

Provide official reporting guidance. Return ONLY valid JSON:
{{
  "immediate_actions": ["<action 1>", "<action 2>", "<action 3>"],
  "reporting_steps": ["<step 1>", "<step 2>", "<step 3>", "<step 4>"],
  "bank_contact_guidance": "<specific guidance about contacting bank safely>",
  "complaint_checklist": ["<item 1>", "<item 2>", "<item 3>", "<item 4>"]
}}

Incident category: {category}
Risk level: {risk_level}
Financial loss: Rs {financial_loss}
Is ongoing: {ongoing}

IMPORTANT: Only reference official Indian government portals (cybercrime.gov.in, 1930, i4c.mha.gov.in).
Return only the JSON object."""

        result = call_gemini(prompt)
        if result.get("success"):
            try:
                ai_steps  = json.loads(result["text"])
                ai_powered = True
            except Exception:
                ai_steps = None

    return {
        "agent":               "Reporting Guidance Agent",
        "llm":                 "Google Gemini 2.0 Flash",
        "ai_powered":          ai_powered,
        "is_financial_emergency": is_financial_emergency,
        "emergency_guidance": {
            "show_emergency_banner": is_financial_emergency,
            "message": "IMMEDIATE ACTION REQUIRED: Call 1930 now to report financial cyber fraud.",
            "helpline": "1930",
        } if is_financial_emergency else None,
        "immediate_actions": (
            ai_steps.get("immediate_actions", steps[:3]) if ai_steps else steps[:3]
        ),
        "reporting_steps": (
            ai_steps.get("reporting_steps", steps) if ai_steps else steps
        ),
        "bank_contact_guidance": (
            ai_steps.get("bank_contact_guidance") if ai_steps
            else "Contact your bank ONLY through the official number printed on your card or the bank's official website. Do NOT use numbers received in SMS or WhatsApp."
        ),
        "complaint_checklist": (
            ai_steps.get("complaint_checklist") if ai_steps else _EVIDENCE_TO_PRESERVE
        ),
        "evidence_to_preserve": _EVIDENCE_TO_PRESERVE,
        "official_resources": OFFICIAL_RESOURCES,
        "disclaimer": (
            "CyberRakshak AI has NOT submitted any complaint on your behalf. "
            "You must submit your complaint directly at cybercrime.gov.in or by calling 1930."
        ),
    }
