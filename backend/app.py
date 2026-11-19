"""
CyberRakshak AI — Flask Application Entry Point
All API endpoints are defined here.
"""
import os
import sys
import json
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env from the project root regardless of working directory
_project_root = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(_project_root, ".env"))

from backend.config import Config
from backend.services.security_service import (
    allowed_file, safe_filename, sanitize_text,
    validate_incident_input, generate_incident_id,
)
from backend.orchestrator.agent_orchestrator import run_workflow, PROGRESS_MESSAGES
from backend.services.granite_service import get_all_status as granite_status
from backend.services.gemini_service import get_status as gemini_status
from backend.services.groq_service import get_status as groq_status

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend"),
    static_url_path="",
)
app.config["SECRET_KEY"] = Config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
CORS(app, resources={r"/api/*": {"origins": "*"}})

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.REPORTS_FOLDER, exist_ok=True)


# ── Frontend routes ────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/dashboard.html")
def dashboard():
    return send_from_directory(app.static_folder, "dashboard.html")


# ── Health ─────────────────────────────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    db_ok = False
    try:
        from backend.database import test_connection
        db_ok = test_connection()
    except Exception:
        pass

    return jsonify({
        "status":    "ok",
        "service":   "CyberRakshak AI",
        "timestamp": datetime.datetime.now().isoformat(),
        "database":  "connected" if db_ok else "unavailable",
        "ai_services": {
            "granite": granite_status(),
            "gemini":  gemini_status(),
            "groq":    groq_status(),
        },
        "llm_routing": {
            "privacy_agent":   "Deterministic (regex — no LLM)",
            "intake_agent":    "Llama 3.3 70B via IBM watsonx",
            "scam_agent":      "Llama 3.1 8B via IBM watsonx",
            "evidence_agent":  "IBM Granite 4 Small via watsonx",
            "reporting_agent": "Google Gemini 2.0 Flash",
            "dashboard_agent": "Groq Llama 3.3 70B Versatile",
        },
    })


# ── Submit incident ────────────────────────────────────────────────────────────
@app.route("/api/incidents", methods=["POST"])
def submit_incident():
    # Accept both JSON and form data
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form.to_dict()

    # Sanitize text fields
    for field in ("description", "platform", "incident_category"):
        if field in data:
            data[field] = sanitize_text(str(data.get(field, "")))

    # Validate
    is_valid, errors = validate_incident_input(data)
    if not is_valid:
        return jsonify({"success": False, "errors": errors}), 400

    # Handle file uploads
    evidence_files = []
    if request.files:
        for file_key in request.files:
            file = request.files[file_key]
            if file and file.filename and allowed_file(file.filename):
                fname = safe_filename(file.filename)
                fpath = os.path.join(Config.UPLOAD_FOLDER, fname)
                file.save(fpath)
                evidence_files.append({
                    "file_name": fname,
                    "file_type": fname.rsplit(".", 1)[-1].lower() if "." in fname else "unknown",
                    "storage_reference": fpath,
                    "size_bytes": os.path.getsize(fpath),
                    "upload_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
            elif file and file.filename and not allowed_file(file.filename):
                return jsonify({
                    "success": False,
                    "errors": [f"File type not supported: {file.filename}"],
                }), 400

    # Run orchestrator
    try:
        result = run_workflow(data, evidence_files)
        return jsonify({
            "success": True,
            "incident_id": result["workflow_id"],
            "data": result,
            "progress_messages": PROGRESS_MESSAGES,
        })
    except Exception as e:
        return jsonify({"success": False, "errors": [str(e)]}), 500


# ── List incidents ─────────────────────────────────────────────────────────────
@app.route("/api/incidents", methods=["GET"])
def list_incidents():
    try:
        from backend.database import execute_query
        rows = execute_query(
            "SELECT * FROM incidents ORDER BY created_at DESC LIMIT 50",
            fetch=True,
        )
        # Serialize datetime objects
        for row in rows:
            for k, v in row.items():
                if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
                    row[k] = str(v)
        return jsonify({"success": True, "incidents": rows})
    except Exception as e:
        return jsonify({"success": False, "incidents": [], "error": str(e)}), 200


# ── Get incident detail ────────────────────────────────────────────────────────
@app.route("/api/incidents/<incident_id>", methods=["GET"])
def get_incident(incident_id):
    try:
        from backend.database import execute_query
        rows = execute_query(
            "SELECT * FROM incidents WHERE incident_id=%s", (incident_id,), fetch=True
        )
        if not rows:
            return jsonify({"success": False, "error": "Incident not found"}), 404
        row = rows[0]
        for k, v in row.items():
            if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
                row[k] = str(v)

        analysis = execute_query(
            "SELECT * FROM scam_analysis WHERE incident_id=%s", (incident_id,), fetch=True
        )
        timeline = execute_query(
            "SELECT * FROM incident_timeline WHERE incident_id=%s ORDER BY event_timestamp",
            (incident_id,), fetch=True,
        )
        evidence = execute_query(
            "SELECT * FROM evidence WHERE incident_id=%s", (incident_id,), fetch=True
        )
        for t in timeline:
            for k, v in t.items():
                if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
                    t[k] = str(v)
        return jsonify({
            "success": True,
            "incident": row,
            "analysis": analysis[0] if analysis else {},
            "timeline": timeline,
            "evidence": evidence,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── Upload additional evidence ─────────────────────────────────────────────────
@app.route("/api/incidents/<incident_id>/evidence", methods=["POST"])
def upload_evidence(incident_id):
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400
    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"success": False, "error": "Empty file"}), 400
    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "File type not supported"}), 400

    fname = safe_filename(file.filename)
    fpath = os.path.join(Config.UPLOAD_FOLDER, fname)
    file.save(fpath)

    try:
        from backend.database import execute_query
        execute_query(
            """INSERT INTO evidence (incident_id, file_name, file_type, storage_reference)
               VALUES (%s,%s,%s,%s)""",
            (incident_id, fname, fname.rsplit(".", 1)[-1].lower(), fpath),
        )
    except Exception:
        pass

    return jsonify({"success": True, "file_name": fname})


# ── Download report ────────────────────────────────────────────────────────────
@app.route("/api/incidents/<incident_id>/report", methods=["GET"])
def download_report(incident_id):
    report_dir = Config.REPORTS_FOLDER
    # Find latest report for this incident
    try:
        files = [f for f in os.listdir(report_dir) if f.startswith(f"CyberRakshak_{incident_id}_")]
        if not files:
            return jsonify({"success": False, "error": "Report not found"}), 404
        files.sort(reverse=True)
        return send_file(
            os.path.join(report_dir, files[0]),
            as_attachment=True,
            download_name=files[0],
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── Re-analyze ─────────────────────────────────────────────────────────────────
@app.route("/api/incidents/<incident_id>/analyze", methods=["POST"])
def reanalyze(incident_id):
    try:
        from backend.database import execute_query
        rows = execute_query(
            "SELECT * FROM incidents WHERE incident_id=%s", (incident_id,), fetch=True
        )
        if not rows:
            return jsonify({"success": False, "error": "Incident not found"}), 404
        row = rows[0]
        for k, v in row.items():
            if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
                row[k] = str(v)
        row["consent"] = True
        result = run_workflow(row, [])
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  CyberRakshak AI — Starting Server")
    print("  Detect. Understand. Organize. Report. Protect.")
    print("=" * 60)

    # Try to initialize DB
    try:
        from backend.database import init_db, test_connection
        print("[DB] Initializing database schema…")
        init_db()
        if test_connection():
            print("[DB] MySQL connection OK")
        else:
            print("[DB] MySQL unavailable — will work without persistence")
    except Exception as e:
        print(f"[DB] Setup skipped: {e}")

    print("  LLM services initialize lazily on first request.")
    print("=" * 60)
    print("  Frontend : http://localhost:5000")
    print("  API      : http://localhost:5000/api/health")
    print("=" * 60 + "\n")

    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)
