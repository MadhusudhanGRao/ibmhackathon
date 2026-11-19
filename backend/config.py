"""
CyberRakshak AI — Application Configuration
Multi-LLM setup: 3× IBM watsonx (Llama/Granite) + 1× Gemini + 1× Groq
"""
import os
from dotenv import load_dotenv

# Always load from project root so the server works from any working directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "cyberrakshak-change-me")
    FLASK_ENV  = os.getenv("FLASK_ENV", "production")
    DEBUG      = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # ── IBM Granite (3 instances) ─────────────────────────────
    # LLM 1 — Incident Intake Agent
    GRANITE_INTAKE_API_KEY    = os.getenv("GRANITE_INTAKE_API_KEY", "")
    GRANITE_INTAKE_PROJECT_ID = os.getenv("GRANITE_INTAKE_PROJECT_ID", "")
    GRANITE_INTAKE_URL        = os.getenv("GRANITE_INTAKE_URL", "https://us-south.ml.cloud.ibm.com")
    GRANITE_INTAKE_MODEL      = os.getenv("GRANITE_INTAKE_MODEL", "meta-llama/llama-3-3-70b-instruct")

    # LLM 2 — Scam Analysis Agent
    GRANITE_SCAM_API_KEY    = os.getenv("GRANITE_SCAM_API_KEY", "")
    GRANITE_SCAM_PROJECT_ID = os.getenv("GRANITE_SCAM_PROJECT_ID", "")
    GRANITE_SCAM_URL        = os.getenv("GRANITE_SCAM_URL", "https://us-south.ml.cloud.ibm.com")
    GRANITE_SCAM_MODEL      = os.getenv("GRANITE_SCAM_MODEL", "meta-llama/llama-3-3-70b-instruct")

    # LLM 3 — Evidence Organization Agent
    GRANITE_EVIDENCE_API_KEY    = os.getenv("GRANITE_EVIDENCE_API_KEY", "")
    GRANITE_EVIDENCE_PROJECT_ID = os.getenv("GRANITE_EVIDENCE_PROJECT_ID", "")
    GRANITE_EVIDENCE_URL        = os.getenv("GRANITE_EVIDENCE_URL", "https://us-south.ml.cloud.ibm.com")
    GRANITE_EVIDENCE_MODEL      = os.getenv("GRANITE_EVIDENCE_MODEL", "meta-llama/llama-3-3-70b-instruct")

    # ── Gemini (LLM 4) — Reporting Guidance Agent ─────────────
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    # ── Groq (LLM 5) — Guidance Dashboard Agent ──────────────
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL   = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

    # ── MySQL ─────────────────────────────────────────────────
    MYSQL_HOST     = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT     = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER     = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "cyberrakshak_db")

    # ── Uploads ───────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "uploads"
    )
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", 16)) * 1024 * 1024
    ALLOWED_EXTENSIONS = set(
        os.getenv("ALLOWED_EXTENSIONS", "png,jpg,jpeg,gif,pdf,txt,doc,docx").split(",")
    )

    # ── Reports ───────────────────────────────────────────────
    REPORTS_FOLDER = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "reports"
    )

    # ── Convenience checkers ──────────────────────────────────
    _PH = "your_ibm_watsonx_api_key_here"

    @classmethod
    def granite_configured(cls, role: str) -> bool:
        key = getattr(cls, f"GRANITE_{role.upper()}_API_KEY", "")
        pid = getattr(cls, f"GRANITE_{role.upper()}_PROJECT_ID", "")
        return bool(key and key != cls._PH and pid)

    @classmethod
    def gemini_configured(cls) -> bool:
        k = cls.GEMINI_API_KEY
        return bool(k and k != "your_gemini_api_key_here")

    @classmethod
    def groq_configured(cls) -> bool:
        k = cls.GROQ_API_KEY
        return bool(k and k != "your_groq_api_key_here")
