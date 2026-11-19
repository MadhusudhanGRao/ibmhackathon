"""
CyberRakshak AI — Agent & Service Unit Tests
Run: python -m pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


# ── Privacy Agent ─────────────────────────────────────────────────────────────

from backend.agents.privacy_agent import run as privacy_run, scan_dict


def test_privacy_clean():
    result = privacy_run("I lost money via a fake KYC SMS")
    assert result["privacy_status"] == "CLEAN"
    assert result["sensitive_data_found"] is False
    assert result["safe_for_ai_processing"] is True


def test_privacy_redacts_otp():
    result = privacy_run("My OTP is 456789 — please do not share")
    assert result["sensitive_data_found"] is True
    assert "***OTP-REDACTED***" in result["redacted_text"]


def test_privacy_redacts_cvv():
    result = privacy_run("CVV: 123 — card number 4111111111111111")
    assert result["sensitive_data_found"] is True


def test_privacy_scan_dict():
    data = {"description": "My UPI PIN is 7890 and I lost money", "platform": "GPay"}
    result = scan_dict(data)
    assert result["sensitive_data_found"] is True
    assert "***UPI-PIN-REDACTED***" in result["redacted_data"]["description"]
    assert result["redacted_data"]["platform"] == "GPay"  # unaffected field preserved


# ── Security Service ──────────────────────────────────────────────────────────

from backend.services.security_service import (
    allowed_file, safe_filename, sanitize_text,
    validate_incident_input, generate_incident_id,
)


def test_allowed_file_valid():
    assert allowed_file("screenshot.png") is True
    assert allowed_file("document.pdf") is True
    assert allowed_file("note.txt") is True


def test_allowed_file_invalid():
    assert allowed_file("malware.exe") is False
    assert allowed_file("script.sh") is False
    assert allowed_file("noextension") is False


def test_sanitize_text_strips_html():
    result = sanitize_text("<script>alert('xss')</script>Hello")
    assert "<script>" not in result
    assert "Hello" in result


def test_validate_incident_input_valid():
    data = {
        "description": "I received a fake KYC SMS and lost ₹5000 via UPI",
        "incident_category": "Fake KYC",
        "consent": "true",
    }
    is_valid, errors = validate_incident_input(data)
    assert is_valid is True
    assert errors == []


def test_validate_incident_input_missing_description():
    data = {"description": "", "incident_category": "Phishing", "consent": "true"}
    is_valid, errors = validate_incident_input(data)
    assert is_valid is False
    assert any("description" in e.lower() for e in errors)


def test_validate_incident_input_missing_consent():
    data = {"description": "I was scammed via UPI payment", "incident_category": "UPI Fraud"}
    is_valid, errors = validate_incident_input(data)
    assert is_valid is False
    assert any("consent" in e.lower() for e in errors)


def test_generate_incident_id_format():
    id1 = generate_incident_id()
    id2 = generate_incident_id()
    assert id1.startswith("INC-")
    assert id1 != id2  # unique


# ── Intake Agent ──────────────────────────────────────────────────────────────

from backend.agents.intake_agent import run as intake_run


def test_intake_classifies_upi():
    result = intake_run({
        "description": "Someone asked me to send money via GPay UPI and I lost money",
        "incident_category": "",
        "platform": "Google Pay",
        "financial_loss": 2000,
    })
    assert result["incident_category"] == "UPI Fraud"
    assert result["financial_loss"] == 2000.0
    assert "ai_powered" in result


def test_intake_uses_user_category():
    result = intake_run({
        "description": "Something suspicious happened online",
        "incident_category": "Investment Scam",
        "platform": "Telegram",
        "financial_loss": 0,
    })
    assert result["incident_category"] == "Investment Scam"


# ── Scam Analysis Agent ───────────────────────────────────────────────────────

from backend.agents.scam_analysis_agent import run as scam_run


def test_scam_detects_high_risk():
    intake = {"incident_category": "Fake KYC"}
    result = scam_run({
        "description": "RBI sent urgent message: account blocked, share OTP to verify KYC now. Send money via UPI.",
        "platform": "SMS",
        "financial_loss": 5000,
    }, intake)
    assert result["risk_level"] in ("Critical Urgency", "High Concern")
    assert len(result["suspicious_indicators"]) > 0
    assert result["indicator_count"] > 0


def test_scam_low_risk_description():
    intake = {"incident_category": "Other Suspicious Activity"}
    result = scam_run({"description": "I think something might be wrong", "financial_loss": 0}, intake)
    assert "risk_level" in result
    assert "suspicious_indicators" in result


# ── Full Workflow ─────────────────────────────────────────────────────────────

from backend.orchestrator.agent_orchestrator import run_workflow


def test_full_workflow_runs():
    result = run_workflow({
        "description": "Received fake KYC SMS from SBI and lost ₹3000 via UPI on Google Pay",
        "incident_category": "Fake KYC",
        "incident_date": "2025-01-10",
        "incident_time": "10:00",
        "platform": "Google Pay",
        "financial_loss": 3000,
        "ongoing_status": False,
        "consent": True,
    }, [])

    assert result["status"] in ("complete", "complete_with_warnings")
    assert result["workflow_id"].startswith("INC-")
    assert result["intake"]["incident_category"] == "Fake KYC"
    assert result["scam_analysis"]["risk_level"] in (
        "Low Concern", "Medium Concern", "High Concern", "Critical Urgency"
    )
    assert result["dashboard"]["incident_summary"]["category"] == "Fake KYC"
    assert result["report_path"] != "" or "Report generation" in str(result.get("errors", []))
