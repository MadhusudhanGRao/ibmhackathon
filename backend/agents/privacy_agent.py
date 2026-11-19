"""
Agent 1 — Privacy Protection Agent
Detects and redacts sensitive information BEFORE any AI processing.
Uses deterministic Python regex — no AI call required for this agent.
"""
import re
import json


# Patterns for sensitive data
_PATTERNS = {
    "otp":          (r"\b\d{4,8}\b(?=.*(?:otp|one.?time|verification|confirm))",
                     "***OTP-REDACTED***"),
    "password":     (r"(?i)(?:password|passwd|pwd)\s*[:=\s]\s*\S+",
                     "***PASSWORD-REDACTED***"),
    "upi_pin":      (r"(?i)(?:upi\s*pin|mpin)\s*[:=\s]*\d{4,6}",
                     "***UPI-PIN-REDACTED***"),
    "cvv":          (r"(?i)\b(?:cvv|cvc|cvv2)\s*[:=\s]*\d{3,4}\b",
                     "***CVV-REDACTED***"),
    "card_number":  (r"\b(?:\d[ -]?){13,16}\b",
                     "***CARD-NUMBER-REDACTED***"),
    "bank_account": (r"(?i)(?:account\s*(?:no|number|#))\s*[:=\s]*[\dXx]{6,18}",
                     "***ACCOUNT-NUMBER-REDACTED***"),
    "ifsc":         (r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
                     "***IFSC-REDACTED***"),
    "aadhaar":      (r"\b\d{4}\s?\d{4}\s?\d{4}\b",
                     "***AADHAAR-REDACTED***"),
    "pan":          (r"\b[A-Z]{5}\d{4}[A-Z]\b",
                     "***PAN-REDACTED***"),
}

# Standalone 4-8 digit OTP heuristic (context-aware)
_OTP_CONTEXT = re.compile(
    r"(?i)(?:otp|one.time\s*password|verification\s*code|pin\s*is)[^\d]{0,20}(\d{4,8})",
    re.IGNORECASE
)


def run(text: str) -> dict:
    """
    Scan `text` for sensitive data, redact it, return a result dict.
    """
    if not text:
        return _clean_result(text, [], False)

    redacted = text
    warnings = []
    found_sensitive = False

    # Apply OTP context pattern first
    otp_matches = _OTP_CONTEXT.findall(redacted)
    for match in otp_matches:
        redacted = redacted.replace(match, "***OTP-REDACTED***")
        warnings.append("OTP detected and redacted")
        found_sensitive = True

    # Apply all other patterns
    for name, (pattern, replacement) in _PATTERNS.items():
        if re.search(pattern, redacted, re.IGNORECASE):
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
            label = name.replace("_", " ").upper()
            warnings.append(f"{label} detected and redacted")
            found_sensitive = True

    return _clean_result(redacted, warnings, found_sensitive, original_length=len(text))


def _clean_result(redacted_text, warnings, found_sensitive, original_length=0):
    return {
        "agent": "Privacy Protection Agent",
        "redacted_text": redacted_text,
        "warnings": list(set(warnings)),          # deduplicate
        "sensitive_data_found": found_sensitive,
        "safe_for_ai_processing": not found_sensitive or bool(redacted_text),
        "privacy_status": "REDACTED" if found_sensitive else "CLEAN",
        "original_length": original_length,
        "redacted_length": len(redacted_text) if redacted_text else 0,
    }


def scan_dict(data: dict) -> dict:
    """
    Recursively scan all string values in a dict and return
    a redacted copy plus a combined privacy result.
    """
    all_warnings = []
    found = False

    def _redact(obj):
        nonlocal found
        if isinstance(obj, dict):
            return {k: _redact(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_redact(i) for i in obj]
        if isinstance(obj, str):
            r = run(obj)
            if r["sensitive_data_found"]:
                found = True
                all_warnings.extend(r["warnings"])
            return r["redacted_text"]
        return obj

    redacted_data = _redact(data)
    return {
        "redacted_data": redacted_data,
        "warnings": list(set(all_warnings)),
        "sensitive_data_found": found,
        "privacy_status": "REDACTED" if found else "CLEAN",
    }
