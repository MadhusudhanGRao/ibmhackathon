"""
Agent 4 — Evidence Organization Agent
LLM: IBM Granite 3.1 8B Instruct (via watsonx.ai)
Fallback: deterministic metadata extraction + timeline building
"""
import os
import json
import datetime
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.services.granite_service import call_granite, granite_available

SUPPORTED_TYPES = {
    "image": ["png", "jpg", "jpeg", "gif", "bmp", "webp"],
    "document": ["pdf", "doc", "docx", "txt"],
}

_MISSING_EVIDENCE_CHECKLIST = [
    "Screenshot of the suspicious SMS or message",
    "Screenshot of the suspicious website or link",
    "Screenshot of the unauthorized transaction",
    "Bank statement showing the debit",
    "Any email communication from the scammer",
    "Screenshot of the fraudulent phone number or caller ID",
    "Any social media profile of the impersonator",
]

_EVIDENCE_CATEGORIES = {
    "sms":          ["sms", "message", "text", "notification"],
    "transaction":  ["transaction", "transfer", "debit", "credit", "upi", "payment", "receipt"],
    "website":      ["website", "link", "url", "page", "portal", "login"],
    "email":        ["email", "mail", "inbox"],
    "social_media": ["instagram", "facebook", "whatsapp", "twitter", "profile", "account"],
    "call":         ["call", "caller", "phone", "number", "voice"],
}


def _categorize_evidence(filename: str, extracted_text: str = "") -> str:
    combined = (filename + " " + extracted_text).lower()
    for category, keywords in _EVIDENCE_CATEGORIES.items():
        if any(kw in combined for kw in keywords):
            return category
    return "general"


def _build_missing_checklist(evidence_list: list) -> list:
    missing = []
    for item in _MISSING_EVIDENCE_CHECKLIST:
        item_lower = item.lower()
        is_covered = any(
            any(kw in item_lower for kw in _EVIDENCE_CATEGORIES.get(e.get("evidence_category", "general"), []))
            for e in evidence_list
        )
        if not is_covered:
            missing.append(item)
    return missing[:5]


def _build_timeline(incident_data: dict, evidence_list: list) -> list:
    timeline = []
    inc_date = incident_data.get("incident_date", "")
    inc_time = incident_data.get("incident_time", "")
    if inc_date:
        dt_str = f"{inc_date} {inc_time}" if inc_time else f"{inc_date} 00:00:00"
        timeline.append({"event": "Incident occurred", "timestamp": dt_str, "source": "user_reported"})
    for ev in evidence_list:
        timeline.append({
            "event": f"Evidence uploaded: {ev.get('file_name', 'unknown')}",
            "timestamp": ev.get("upload_timestamp", datetime.datetime.now().isoformat()),
            "source": "evidence_upload",
        })
    timeline.append({
        "event": "Incident reported to CyberRakshak AI",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "system",
    })
    return sorted(timeline, key=lambda x: x.get("timestamp", ""))


def run(incident_data: dict, evidence_files: list) -> dict:
    inventory = []
    for ef in evidence_files:
        filename = ef.get("file_name", "")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
        file_category = ("image" if ext in SUPPORTED_TYPES["image"]
                         else "document" if ext in SUPPORTED_TYPES["document"] else "unsupported")
        ev_category = _categorize_evidence(filename)
        inventory.append({
            "file_name":         filename,
            "file_type":         ext,
            "file_category":     file_category,
            "evidence_category": ev_category,
            "storage_reference": ef.get("storage_reference", ""),
            "size_bytes":        ef.get("size_bytes", 0),
            "extracted_text":    ef.get("extracted_text", ""),
            "description":       f"{ev_category.replace('_', ' ').title()} evidence: {filename}",
            "upload_timestamp":  ef.get("upload_timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        })

    timeline = _build_timeline(incident_data, inventory)
    missing_checklist = _build_missing_checklist(inventory)

    ai_summary = ""
    ai_powered = False

    if granite_available("evidence") and inventory:
        evidence_names = [e["file_name"] for e in inventory]
        prompt = f"""You are CyberRakshak AI's Evidence Organization Agent for cybercrime in Bengaluru, India.

Return ONLY valid JSON:
{{
  "evidence_summary": "<2-3 sentences summarizing available evidence>",
  "key_evidence": ["<most important piece 1>", "<most important piece 2>"],
  "timeline_note": "<note about chronological sequence>"
}}

Incident: {incident_data.get('description', '')[:300]}
Evidence files: {', '.join(evidence_names)}

Return only the JSON object."""

        result = call_granite("evidence", prompt)
        if result.get("success"):
            try:
                parsed = json.loads(result["text"])
                ai_summary = parsed.get("evidence_summary", "")
                ai_powered = True
            except Exception:
                pass

    return {
        "agent":                    "Evidence Organization Agent",
        "llm":                      "IBM Granite 3.1 8B Instruct",
        "ai_powered":               ai_powered,
        "evidence_count":           len(inventory),
        "evidence_inventory":       inventory,
        "evidence_summary":         ai_summary or (
            f"{len(inventory)} piece(s) of evidence submitted." if inventory
            else "No evidence files submitted."
        ),
        "incident_timeline":        timeline,
        "missing_evidence_checklist": missing_checklist,
        "note": (
            "IBM Granite 3.1 8B enhanced analysis. Original files preserved unmodified." if ai_powered
            else "Deterministic evidence organization. Original files preserved unmodified."
        ),
    }
