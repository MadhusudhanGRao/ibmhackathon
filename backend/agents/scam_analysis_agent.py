"""
Agent 3 — Scam Analysis Agent
LLM: IBM Granite 3.3 2B Instruct (via watsonx.ai)
Fallback: deterministic rule-based indicator analysis

DISCLAIMER: Identifies POTENTIAL indicators only.
Never declares criminal activity or verified fraud.
"""
import json
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.services.granite_service import call_granite, granite_available

_INDICATORS = {
    "urgency_tactic": {
        "keywords": ["urgent", "immediately", "within 24 hours", "account will be blocked",
                     "last chance", "expire", "suspended", "act now"],
        "label": "Urgency / Pressure Tactic", "weight": 3,
    },
    "impersonation": {
        "keywords": ["rbi", "sbi", "hdfc", "icici", "axis bank", "income tax", "police",
                     "government", "cbi", "sebi", "irdai", "nsdl"],
        "label": "Potential Authority Impersonation", "weight": 3,
    },
    "suspicious_link": {
        "keywords": ["http://", "bit.ly", "tinyurl", "goo.gl", "click here",
                     "verify now", "update kyc", "login link", "open link"],
        "label": "Suspicious Link or URL", "weight": 3,
    },
    "credential_request": {
        "keywords": ["otp", "pin", "password", "cvv", "card number", "account number",
                     "netbanking", "share your", "enter your"],
        "label": "Credential / Sensitive Data Request", "weight": 4,
    },
    "payment_request": {
        "keywords": ["send money", "transfer", "pay now", "refund", "cashback",
                     "advance fee", "registration fee", "upi id"],
        "label": "Suspicious Payment Request", "weight": 3,
    },
    "reward_lure": {
        "keywords": ["won", "winner", "prize", "lottery", "selected", "reward",
                     "offer", "free", "congratulations", "lucky"],
        "label": "Reward / Lottery Lure", "weight": 2,
    },
    "job_scam": {
        "keywords": ["work from home", "easy money", "per day", "job offer",
                     "recruitment", "salary", "part time"],
        "label": "Potential Job Scam Indicator", "weight": 2,
    },
    "fake_kyc": {
        "keywords": ["kyc", "know your customer", "kyc update", "document upload", "rekyc"],
        "label": "Fake KYC Request", "weight": 3,
    },
}

_RISK_THRESHOLDS = {"Critical": 10, "High": 6, "Medium": 3, "Low": 0}


def _deterministic_analysis(text: str) -> dict:
    text_lower = text.lower()
    found, weight = [], 0
    for key, rule in _INDICATORS.items():
        matched = [kw for kw in rule["keywords"] if kw in text_lower]
        if matched:
            found.append({"indicator": rule["label"], "matched_terms": matched[:3]})
            weight += rule["weight"]
    risk = "Low"
    for level, threshold in _RISK_THRESHOLDS.items():
        if weight >= threshold:
            risk = level
            break
    return {"indicators": found, "risk_level": risk, "indicator_count": len(found), "weight": weight}


def run(incident_data: dict, intake_result: dict) -> dict:
    description = incident_data.get("description", "")
    category    = intake_result.get("incident_category", "")
    det         = _deterministic_analysis(description)
    ai_powered  = False

    _risk_map = {
        "Critical": "Critical Urgency", "High": "High Concern",
        "Medium": "Medium Concern",     "Low":  "Low Concern",
    }
    _explanations = {
        "Critical": "Multiple strong indicators of fraud detected including potential credential theft, payment pressure and impersonation.",
        "High":     "Several suspicious indicators found. The incident description contains common scam patterns.",
        "Medium":   "Some suspicious elements detected. Exercise caution and verify through official channels.",
        "Low":      "Limited suspicious indicators. Monitor the situation and preserve any evidence.",
    }

    risk_level  = _risk_map.get(det["risk_level"], "Low Concern")
    indicators  = [i["indicator"] for i in det["indicators"]]
    explanation = _explanations.get(det["risk_level"], _explanations["Low"])
    immediate   = (
        "Call 1930 immediately and block UPI/banking access through your bank's official app."
        if det["risk_level"] in ("Critical", "High")
        else "Preserve all evidence and report at cybercrime.gov.in."
    )

    if granite_available("scam"):
        prompt = f"""You are CyberRakshak AI's Scam Analysis Agent for cybercrime in Bengaluru, India.

IMPORTANT: Identify POTENTIAL indicators only. You cannot verify crimes or identify criminals.

Analyze and return ONLY valid JSON:
{{
  "potential_scam_category": "<specific scam type>",
  "risk_level": "<Low Concern|Medium Concern|High Concern|Critical Urgency>",
  "suspicious_indicators": ["<indicator 1>", "<indicator 2>", "<indicator 3>"],
  "explanation": "<2-3 sentences explaining why this appears suspicious>",
  "immediate_action": "<single most important immediate action>",
  "uncertainty_note": "<note about limitations of this AI analysis>"
}}

Incident category: {category}
Incident description: {description}
Platform: {incident_data.get('platform', 'Unknown')}
Financial loss: Rs {incident_data.get('financial_loss', 0)}

Return only the JSON object, no markdown, no explanation."""

        result = call_granite("scam", prompt)
        if result.get("success"):
            try:
                parsed     = json.loads(result["text"])
                risk_level = parsed.get("risk_level", risk_level)
                indicators = parsed.get("suspicious_indicators", indicators)
                explanation= parsed.get("explanation", explanation)
                immediate  = parsed.get("immediate_action", immediate)
                category   = parsed.get("potential_scam_category", category)
                ai_powered = True
            except (json.JSONDecodeError, KeyError):
                pass

    return {
        "agent":                   "Scam Analysis Agent",
        "llm":                     "IBM Granite 3.3 2B Instruct",
        "ai_powered":              ai_powered,
        "potential_scam_category": category,
        "risk_level":              risk_level,
        "suspicious_indicators":   indicators,
        "explanation":             explanation,
        "immediate_action":        immediate,
        "uncertainty_note": (
            "NOTE: This analysis identifies potential indicators only and does not verify criminal activity. "
            "IBM Granite AI-enhanced analysis." if ai_powered
            else "NOTE: Rule-based preliminary analysis only. Add IBM Granite credentials for AI-enhanced analysis."
        ),
        "deterministic_indicators": det["indicators"],
        "indicator_count":          det["indicator_count"],
    }
