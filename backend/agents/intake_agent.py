"""
Agent 2 — Incident Intake Agent
LLM: IBM Granite 3.3 8B Instruct (via watsonx.ai)
Fallback: deterministic keyword classification
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.services.granite_service import call_granite, granite_available

SUPPORTED_CATEGORIES = [
    "UPI Fraud", "Banking Fraud", "Phishing", "Fake KYC", "OTP Scam",
    "Social Media Impersonation", "Account Takeover", "Fake Customer Care",
    "Online Shopping Fraud", "Job Scam", "Investment Scam",
    "Identity Theft", "Other Suspicious Activity",
]

_CATEGORY_KEYWORDS = {
    "UPI Fraud":                  ["upi", "gpay", "phonepe", "paytm", "bhim", "upi fraud"],
    "Banking Fraud":              ["bank", "netbanking", "banking", "account debit", "unauthorized transaction"],
    "Phishing":                   ["phishing", "fake link", "suspicious link", "clicked link", "credential"],
    "Fake KYC":                   ["kyc", "know your customer", "kyc update", "kyc verification"],
    "OTP Scam":                   ["otp", "one time password", "verification code", "share otp"],
    "Social Media Impersonation": ["instagram", "facebook", "twitter", "whatsapp", "impersonation", "fake account"],
    "Account Takeover":           ["account takeover", "hacked", "account hack", "password changed", "login"],
    "Fake Customer Care":         ["customer care", "helpline", "toll free", "support number", "fake number"],
    "Online Shopping Fraud":      ["amazon", "flipkart", "meesho", "shopping", "order", "product", "delivery"],
    "Job Scam":                   ["job", "employment", "salary", "work from home", "recruitment"],
    "Investment Scam":            ["invest", "investment", "returns", "profit", "stock", "crypto", "trading"],
    "Identity Theft":             ["identity", "aadhaar", "pan card", "documents stolen"],
}


def _classify_deterministic(description: str) -> str:
    desc_lower = description.lower()
    best, best_count = "Other Suspicious Activity", 0
    for category, keywords in _CATEGORY_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in desc_lower)
        if count > best_count:
            best_count = count
            best = category
    return best


def _identify_missing(data: dict) -> list:
    missing = []
    if not data.get("incident_date"):
        missing.append("Incident date")
    if not data.get("incident_time"):
        missing.append("Approximate time")
    if not data.get("platform"):
        missing.append("Platform or app involved")
    if not data.get("description") or len(data.get("description", "")) < 20:
        missing.append("More detailed incident description")
    return missing


def run(incident_data: dict) -> dict:
    description = incident_data.get("description", "")
    user_category = incident_data.get("incident_category", "")
    ai_powered = False
    category = user_category or _classify_deterministic(description)
    platform  = incident_data.get("platform", "Not specified")
    summary   = f"Incident reported: {description[:200]}"
    key_facts = [f"Category: {category}", f"Platform: {platform}"]
    confidence = "MEDIUM"

    if granite_available("intake"):
        prompt = f"""You are CyberRakshak AI's Incident Intake Agent for cybercrime incidents in Bengaluru, India.

Analyze this cybercrime incident and return ONLY valid JSON with these exact fields:
{{
  "incident_category": "<one of the supported categories>",
  "platform": "<platform or app involved>",
  "is_ongoing": <true or false>,
  "key_facts": ["<fact 1>", "<fact 2>", "<fact 3>"],
  "incident_summary": "<2-3 sentence structured summary>",
  "confidence": "<HIGH|MEDIUM|LOW>"
}}

Supported categories: {', '.join(SUPPORTED_CATEGORIES)}

Incident description: {description}
User-provided category: {user_category}
Platform provided: {incident_data.get('platform', 'Not specified')}
Financial loss: {incident_data.get('financial_loss', 0)}

Return only the JSON object, no markdown, no explanation."""

        result = call_granite("intake", prompt)
        if result.get("success"):
            try:
                parsed = json.loads(result["text"])
                category   = parsed.get("incident_category", category)
                platform   = parsed.get("platform", platform)
                summary    = parsed.get("incident_summary", summary)
                key_facts  = parsed.get("key_facts", key_facts)
                confidence = parsed.get("confidence", "MEDIUM")
                ai_powered = True
            except (json.JSONDecodeError, KeyError):
                pass

    return {
        "agent":             "Incident Intake Agent",
        "llm":               "IBM Granite 3.3 8B Instruct",
        "ai_powered":        ai_powered,
        "incident_category": category,
        "description":       description,
        "incident_date":     incident_data.get("incident_date", ""),
        "incident_time":     incident_data.get("incident_time", ""),
        "platform":          platform,
        "financial_loss":    float(incident_data.get("financial_loss", 0) or 0),
        "ongoing_status":    bool(incident_data.get("ongoing_status", False)),
        "incident_summary":  summary,
        "key_facts":         key_facts,
        "missing_information": _identify_missing(incident_data),
        "confidence":        confidence,
    }
