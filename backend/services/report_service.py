"""
CyberRakshak AI — Report Service
Generates a downloadable plain-text/HTML incident report.
"""
import datetime
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.config import Config


def generate_report(incident_id: str, dashboard: dict) -> str:
    """Generate and save a text report. Returns the file path."""
    os.makedirs(Config.REPORTS_FOLDER, exist_ok=True)
    filename = f"CyberRakshak_{incident_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(Config.REPORTS_FOLDER, filename)

    lines = [
        "=" * 65,
        "         CyberRakshak AI — Incident Response Report",
        "   SYNTHETIC/DEMO DATA — NOT FOR OFFICIAL SUBMISSION",
        "=" * 65,
        f"Incident ID    : {incident_id}",
        f"Generated At   : {dashboard.get('generated_at', '')}",
        f"Report Version : 1.0",
        "",
        "--- INCIDENT SUMMARY ---",
        f"Category       : {dashboard['incident_summary']['category']}",
        f"Platform       : {dashboard['incident_summary']['platform']}",
        f"Date           : {dashboard['incident_summary']['incident_date']}",
        f"Financial Loss : ₹{dashboard['incident_summary']['financial_loss']:.2f}",
        f"Ongoing        : {'Yes' if dashboard['incident_summary']['ongoing'] else 'No'}",
        "",
        dashboard["incident_summary"].get("executive_summary", ""),
        "",
        "--- RISK ASSESSMENT ---",
        f"Risk Level     : {dashboard['risk_assessment']['risk_level']}",
        f"Scam Category  : {dashboard['risk_assessment']['potential_scam_category']}",
        "",
        "Suspicious Indicators:",
    ]
    for ind in dashboard["risk_assessment"].get("suspicious_indicators", []):
        lines.append(f"  • {ind}")

    lines += [
        "",
        dashboard["risk_assessment"].get("uncertainty_note", ""),
        "",
        "--- PRIVACY STATUS ---",
        f"Status         : {dashboard['privacy_status']['status']}",
    ]
    for w in dashboard["privacy_status"].get("warnings", []):
        lines.append(f"  ⚠ {w}")

    lines += [
        "",
        "--- EVIDENCE SUMMARY ---",
        dashboard["evidence_summary"].get("summary", "No evidence submitted."),
        "",
        "Missing Evidence Checklist:",
    ]
    for item in dashboard["evidence_summary"].get("missing_checklist", []):
        lines.append(f"  ☐ {item}")

    lines += [
        "",
        "--- INCIDENT TIMELINE ---",
    ]
    for event in dashboard.get("incident_timeline", []):
        lines.append(f"  {event.get('timestamp', '')}  |  {event.get('event', '')}")

    lines += [
        "",
        "--- IMMEDIATE ACTIONS ---",
    ]
    for i, action in enumerate(dashboard["reporting"].get("immediate_actions", []), 1):
        lines.append(f"  {i}. {action}")

    lines += [
        "",
        "--- OFFICIAL REPORTING RESOURCES ---",
        "  National Cyber Crime Portal : https://cybercrime.gov.in/",
        "  Financial Fraud Helpline    : 1930",
        "  I4C (MHA)                   : https://i4c.mha.gov.in/",
        "",
        "--- DISCLAIMER ---",
        dashboard["reporting"].get("disclaimer", ""),
        "",
        "=" * 65,
        "CyberRakshak AI — Detect. Understand. Organize. Report. Protect.",
        "Developed for the IBM Bob Hackathon with IBM SkillsBuild",
        "=" * 65,
    ]

    content = "\n".join(lines)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath
