"""
CyberRakshak AI — Security Service
Input validation, file security, XSS protection.
"""
import os
import re
import uuid
from werkzeug.utils import secure_filename
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.config import Config


def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS


def safe_filename(filename: str) -> str:
    base = secure_filename(filename)
    if not base:
        base = "upload"
    ext = ""
    if "." in base:
        base, ext = base.rsplit(".", 1)
        ext = "." + ext
    return f"{base}_{uuid.uuid4().hex[:8]}{ext}"


def sanitize_text(text: str) -> str:
    """Basic XSS prevention — strip HTML tags."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", str(text))
    text = text.replace("&", "&amp;").replace('"', "&quot;")
    return text.strip()[:10000]  # Cap at 10k chars


def validate_incident_input(data: dict) -> tuple:
    """
    Returns (is_valid: bool, errors: list)
    """
    errors = []
    if not data.get("description") or len(str(data["description"]).strip()) < 10:
        errors.append("Incident description must be at least 10 characters.")
    if not data.get("incident_category"):
        errors.append("Incident category is required.")
    if not data.get("consent"):
        errors.append("Consent for processing is required.")
    loss = data.get("financial_loss", 0)
    try:
        if loss and float(loss) < 0:
            errors.append("Financial loss cannot be negative.")
    except (ValueError, TypeError):
        errors.append("Financial loss must be a valid number.")
    return len(errors) == 0, errors


def generate_incident_id() -> str:
    import datetime
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    uid = uuid.uuid4().hex[:6].upper()
    return f"INC-{ts}-{uid}"
