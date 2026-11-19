"""
CyberRakshak AI — Gemini AI Service
Uses the new google-genai SDK (google.genai).
Falls back gracefully when API key is not configured.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

_client = None
_initialized = False
_available = False
_model_id = "gemini-2.0-flash"


def _init():
    global _client, _initialized, _available, _model_id
    if _initialized:
        return
    _initialized = True
    try:
        from google import genai
        from backend.config import Config
        api_key = Config.GEMINI_API_KEY
        if not api_key or api_key == "your_gemini_api_key_here":
            print("[Gemini] API key not configured — using deterministic fallback mode.")
            _available = False
            return
        _client = genai.Client(api_key=api_key)
        _model_id = Config.GEMINI_MODEL or "gemini-2.0-flash"
        _available = True
        print(f"[Gemini] Service initialized — model: {_model_id}")
    except Exception as e:
        print(f"[Gemini] Initialization failed: {e} — using deterministic fallback mode.")
        _available = False


def gemini_available() -> bool:
    if not _initialized:
        _init()
    return _available


def call_gemini(prompt: str, max_tokens: int = 1024) -> dict:
    """
    Send a prompt to Gemini and return a result dict.
    Returns: {"success": bool, "text": str, "error": str|None, "mode": str}
    """
    if not _initialized:
        _init()

    if not _available or _client is None:
        return {
            "success": False,
            "text": "",
            "error": "Gemini not configured — deterministic fallback active.",
            "mode": "fallback",
        }

    try:
        from google.genai import types as genai_types
        response = _client.models.generate_content(
            model=_model_id,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=0.3,
            ),
        )
        text = response.text.strip() if response.text else ""
        # Strip markdown code fences if model wraps in ```json ... ```
        if text.startswith("```"):
            lines = text.split("\n")
            inner = lines[1:]
            if inner and inner[-1].strip() == "```":
                inner = inner[:-1]
            text = "\n".join(inner).strip()
        return {"success": True, "text": text, "error": None, "mode": "gemini"}
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": str(e),
            "mode": "fallback",
        }


def get_status() -> dict:
    if not _initialized:
        _init()
    from backend.config import Config
    return {
        "configured": _available,
        "model": _model_id if _available else "N/A",
        "mode": "gemini-ai" if _available else "deterministic-fallback",
        "note": (
            f"Powered by Google Gemini AI (model: {_model_id})" if _available
            else "Running in deterministic fallback mode. Add GEMINI_API_KEY to .env to enable AI."
        ),
    }
