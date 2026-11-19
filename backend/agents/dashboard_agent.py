"""
Agent 6 — Guidance Dashboard Agent
LLM: Groq (Llama 3.3 70B Versatile) — fast executive summary writing
Fallback: deterministic template-based summary
Consolidates outputs of all five agents into a unified incident response summary.
"""
import json
import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.services.groq_service import call_groq, groq_available


_RISK_COLORS = {
    "Critical Urgency": "#EF4444",
    "High Concern":     "#F59E0B",
    "Medium Concern":   "#06B6D4",
    "Low Concern":      "#10B981",
}

_AWARENESS_TIPS = {
    "UPI Fraud": [
        "Never share your UPI PIN with anyone, including bank officials.",
        "Banks never ask for OTP or PIN over calls or SMS.",
        "Always verify the receiver's UPI ID before transferring money.",
        "Use only official UPI apps (GPay, PhonePe, Paytm, BHIM).",
    ],
    "Phishing": [
        "Check the sender's email address carefully for misspellings.",
        "Hover over links to see the actual URL before clicking.",
        "Official banks and government portals use .gov.in or .co.in domains.",
        "Enable two-factor authentication on all accounts.",
    ],
    "Fake KYC": [
        "Banks never ask for KYC updates via SMS links.",
        "KYC updates are done only at your bank branch or verified app.",
        "Report fake KYC SMS to your bank and cybercrime.gov.in.",
        "Never click links in KYC-related SMS messages.",
    ],
    "default": [
        "Never share OTPs, PINs, or passwords with anyone.",
        "Verify the identity of callers before sharing any information.",
        "Use strong, unique passwords and enable two-factor authentication.",
        "Report all cybercrime incidents at cybercrime.gov.in.",
    ],
}


def run(
    incident_id: str,
    incident_data: dict,
    privacy_result: dict,
    intake_result: dict,
    scam_result: dict,
    evidence_result: dict,
    reporting_result: dict,
) -> dict:
    category      = intake_result.get("incident_category", "Unknown")
    risk_level    = scam_result.get("risk_level", "Low Concern")
    financial_loss = float(incident_data.get("financial_loss", 0) or 0)
    tips          = _AWARENESS_TIPS.get(category, _AWARENESS_TIPS["default"])

    # Consolidated recommended actions (deduplicated, emergency first)
    actions = []
    if reporting_result.get("is_financial_emergency"):
        actions.append("CALL 1930 IMMEDIATELY — Financial Cyber Fraud Helpline")
    actions.extend(reporting_result.get("immediate_actions", [])[:3])
    actions.append("File a complaint at cybercrime.gov.in")
    actions.append("Preserve all evidence screenshots")
    seen, unique_actions = set(), []
    for a in actions:
        if a not in seen:
            seen.add(a)
            unique_actions.append(a)

    # Groq-powered executive summary
    exec_summary = ""
    ai_powered   = False

    if groq_available():
        prompt = f"""You are CyberRakshak AI's Guidance Dashboard Agent for cybercrime in Bengaluru, India.

Write a clear, empathetic 3-4 sentence executive summary of this cybercrime incident for a victim.
Explain what likely happened, the risk level, and the single most important next step.
Write only the summary paragraph — no JSON, no headers, no bullet points.

Incident category: {category}
Risk level: {risk_level}
Financial loss: Rs {financial_loss}
Key indicators: {', '.join(scam_result.get('suspicious_indicators', [])[:3])}
Incident summary: {intake_result.get('incident_summary', '')[:200]}"""

        result = call_groq(prompt, max_tokens=300)
        if result.get("success"):
            exec_summary = result.get("text", "").strip()
            ai_powered   = True

    if not exec_summary:
        exec_summary = (
            f"Based on your report, this incident has been classified as "
            f"'{category}' with a {risk_level} assessment. "
            f"{intake_result.get('incident_summary', '')} "
            f"Please follow the recommended actions below and report to official channels immediately."
        )

    # Collect which LLM powered each agent
    ai_powered_agents = {
        "privacy":      False,  # always deterministic
        "intake":       intake_result.get("ai_powered", False),
        "scam_analysis": scam_result.get("ai_powered", False),
        "evidence":     evidence_result.get("ai_powered", False),
        "reporting":    reporting_result.get("ai_powered", False),
        "dashboard":    ai_powered,
    }
    llm_map = {
        "privacy":       "Deterministic (regex)",
        "intake":        intake_result.get("llm", "IBM Granite 3.3 8B"),
        "scam_analysis": scam_result.get("llm", "IBM Granite 3.3 2B"),
        "evidence":      evidence_result.get("llm", "IBM Granite 3.1 8B"),
        "reporting":     reporting_result.get("llm", "Google Gemini 2.0 Flash"),
        "dashboard":     "Groq Llama 3.3 70B",
    }

    return {
        "agent":        "Guidance Dashboard Agent",
        "llm":          "Groq Llama 3.3 70B Versatile",
        "ai_powered":   ai_powered,
        "incident_id":  incident_id,
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "incident_summary": {
            "incident_id":      incident_id,
            "category":         category,
            "platform":         intake_result.get("platform", ""),
            "incident_date":    incident_data.get("incident_date", ""),
            "financial_loss":   financial_loss,
            "ongoing":          intake_result.get("ongoing_status", False),
            "executive_summary": exec_summary,
            "key_facts":        intake_result.get("key_facts", []),
        },

        "risk_assessment": {
            "risk_level":              risk_level,
            "risk_color":              _RISK_COLORS.get(risk_level, "#94A3B8"),
            "potential_scam_category": scam_result.get("potential_scam_category", category),
            "suspicious_indicators":   scam_result.get("suspicious_indicators", []),
            "explanation":             scam_result.get("explanation", ""),
            "uncertainty_note":        scam_result.get("uncertainty_note", ""),
            "indicator_count":         scam_result.get("indicator_count", 0),
        },

        "privacy_status": {
            "status":             privacy_result.get("privacy_status", "CLEAN"),
            "sensitive_data_found": privacy_result.get("sensitive_data_found", False),
            "warnings":           privacy_result.get("warnings", []),
        },

        "evidence_summary": {
            "evidence_count":   evidence_result.get("evidence_count", 0),
            "summary":          evidence_result.get("evidence_summary", ""),
            "inventory":        evidence_result.get("evidence_inventory", []),
            "missing_checklist": evidence_result.get("missing_evidence_checklist", []),
        },

        "incident_timeline": evidence_result.get("incident_timeline", []),

        "reporting": {
            "is_emergency":          reporting_result.get("is_financial_emergency", False),
            "emergency_guidance":    reporting_result.get("emergency_guidance"),
            "immediate_actions":     unique_actions,
            "reporting_steps":       reporting_result.get("reporting_steps", []),
            "bank_contact_guidance": reporting_result.get("bank_contact_guidance", ""),
            "complaint_checklist":   reporting_result.get("complaint_checklist", []),
            "official_resources":    reporting_result.get("official_resources", {}),
            "disclaimer":            reporting_result.get("disclaimer", ""),
        },

        "awareness_tips": tips,

        "ai_powered_agents": ai_powered_agents,
        "llm_map":           llm_map,
    }
