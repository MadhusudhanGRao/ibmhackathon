"""
CyberRakshak AI — Central Agent Orchestrator
Coordinates all six specialized agents in the correct sequence.
Privacy protection always runs BEFORE any external AI processing.
"""
import datetime
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.agents import (
    privacy_agent,
    intake_agent,
    scam_analysis_agent,
    evidence_agent,
    reporting_agent,
    dashboard_agent,
)
from backend.services.report_service import generate_report
from backend.services.security_service import generate_incident_id

# Progress message labels (shown to users, never internal prompts)
PROGRESS_MESSAGES = {
    "start":          "Starting CyberRakshak AI analysis…",
    "privacy":        "🔒 Protecting sensitive information…",
    "intake":         "📋 Collecting and structuring incident information…",
    "scam_analysis":  "🔍 Analyzing suspicious activity indicators…",
    "evidence":       "🗂️ Organizing digital evidence…",
    "reporting":      "📢 Preparing official reporting guidance…",
    "dashboard":      "📊 Generating your incident response report…",
    "saving":         "💾 Saving incident record…",
    "complete":       "✅ Analysis complete.",
}


def _log_step(workflow_id: str, agent_name: str, status: str, message: str = ""):
    """Persist workflow log to DB (non-fatal if DB unavailable)."""
    try:
        from backend.database import execute_query
        execute_query(
            "INSERT INTO workflow_logs (workflow_id, agent_name, execution_status, message) VALUES (%s, %s, %s, %s)",
            (workflow_id, agent_name, status, message[:500] if message else ""),
        )
    except Exception:
        pass  # Logging failure must never block the workflow


def run_workflow(incident_data: dict, evidence_files: list = None) -> dict:
    """
    Execute the full six-agent workflow.

    incident_data keys: description, incident_category, incident_date,
                        incident_time, platform, financial_loss,
                        ongoing_status, consent
    evidence_files: list of dicts {file_name, file_type, storage_reference, size_bytes}
    """
    evidence_files = evidence_files or []
    workflow_id = generate_incident_id()
    execution_log = []
    errors = []

    def _step(label, fn, *args):
        """Run one agent step, capture status, never let one failure kill the workflow."""
        _log_step(workflow_id, label, "RUNNING")
        try:
            result = fn(*args)
            _log_step(workflow_id, label, "SUCCESS")
            execution_log.append({"agent": label, "status": "success"})
            return result
        except Exception as e:
            err_msg = str(e)
            errors.append(f"{label}: {err_msg}")
            _log_step(workflow_id, label, "ERROR", err_msg)
            execution_log.append({"agent": label, "status": "error", "error": err_msg})
            return {}

    # ── Step 1: Privacy Protection (MUST run before AI) ──────────────────────
    privacy_result = _step(
        "Privacy Protection Agent",
        privacy_agent.scan_dict,
        incident_data,
    )
    # Use redacted data for all subsequent AI processing
    safe_data = privacy_result.get("redacted_data", incident_data)

    # ── Step 2: Incident Intake ───────────────────────────────────────────────
    intake_result = _step(
        "Incident Intake Agent",
        intake_agent.run,
        safe_data,
    )

    # ── Step 3: Scam Analysis ─────────────────────────────────────────────────
    scam_result = _step(
        "Scam Analysis Agent",
        scam_analysis_agent.run,
        safe_data,
        intake_result,
    )

    # ── Step 4: Evidence Organization ────────────────────────────────────────
    evidence_result = _step(
        "Evidence Organization Agent",
        evidence_agent.run,
        safe_data,
        evidence_files,
    )

    # ── Step 5: Reporting Guidance ────────────────────────────────────────────
    reporting_result = _step(
        "Reporting Guidance Agent",
        reporting_agent.run,
        safe_data,
        intake_result,
        scam_result,
    )

    # ── Step 6: Guidance Dashboard ────────────────────────────────────────────
    dashboard_result = _step(
        "Guidance Dashboard Agent",
        dashboard_agent.run,
        workflow_id,
        safe_data,
        privacy_result,
        intake_result,
        scam_result,
        evidence_result,
        reporting_result,
    )

    # ── Persist to MySQL ──────────────────────────────────────────────────────
    _persist_incident(workflow_id, incident_data, intake_result, scam_result, evidence_result, evidence_files)

    # ── Generate downloadable report ─────────────────────────────────────────
    report_path = ""
    try:
        report_path = generate_report(workflow_id, dashboard_result)
    except Exception as e:
        errors.append(f"Report generation: {e}")

    _log_step(workflow_id, "Orchestrator", "COMPLETE")

    return {
        "workflow_id": workflow_id,
        "status": "complete" if not errors else "complete_with_warnings",
        "errors": errors,
        "execution_log": execution_log,
        "privacy": privacy_result,
        "intake": intake_result,
        "scam_analysis": scam_result,
        "evidence": evidence_result,
        "reporting": reporting_result,
        "dashboard": dashboard_result,
        "report_path": report_path,
    }


def _persist_incident(workflow_id, incident_data, intake_result, scam_result, evidence_result, evidence_files):
    """Save incident + analysis to MySQL. Non-fatal."""
    try:
        from backend.database import execute_query

        # incidents
        execute_query(
            """INSERT IGNORE INTO incidents
               (incident_id, incident_category, description, incident_date, incident_time,
                platform, financial_loss, ongoing_status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                workflow_id,
                intake_result.get("incident_category", "Unknown"),
                str(incident_data.get("description", ""))[:5000],
                incident_data.get("incident_date") or None,
                incident_data.get("incident_time") or None,
                intake_result.get("platform", ""),
                float(incident_data.get("financial_loss", 0) or 0),
                1 if intake_result.get("ongoing_status") else 0,
            ),
        )

        # scam_analysis
        execute_query(
            """INSERT IGNORE INTO scam_analysis
               (incident_id, potential_category, risk_level, indicators, explanation, recommendations)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (
                workflow_id,
                scam_result.get("potential_scam_category", ""),
                scam_result.get("risk_level", ""),
                json.dumps(scam_result.get("suspicious_indicators", [])),
                scam_result.get("explanation", ""),
                scam_result.get("immediate_action", ""),
            ),
        )

        # timeline
        for event in evidence_result.get("incident_timeline", []):
            execute_query(
                """INSERT INTO incident_timeline
                   (incident_id, event_description, event_timestamp, source_type)
                   VALUES (%s,%s,%s,%s)""",
                (
                    workflow_id,
                    event.get("event", ""),
                    event.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    event.get("source", "system"),
                ),
            )

        # evidence records
        for ev in evidence_result.get("evidence_inventory", []):
            execute_query(
                """INSERT INTO evidence
                   (incident_id, file_name, file_type, storage_reference, extracted_text)
                   VALUES (%s,%s,%s,%s,%s)""",
                (
                    workflow_id,
                    ev.get("file_name", ""),
                    ev.get("file_type", ""),
                    ev.get("storage_reference", ""),
                    ev.get("extracted_text", ""),
                ),
            )
    except Exception as e:
        print(f"[Orchestrator] DB persist error (non-fatal): {e}")
