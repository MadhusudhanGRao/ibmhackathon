"""
CyberRakshak AI — Groq Service
Used by: Guidance Dashboard Agent (executive summary writer)
Default model: llama-3.3-70b-versatile (fast, high-quality writing)
Obtain API key: https://console.groq.com/keys
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

_client = None
_initialized = False
_available = False
_model_id = "llama-3.3-70b-versatile"
_PLACEHOLDER = "your_groq_api_key_here"


def _init():
    global _client, _initialized, _available, _model_id
    if _initialized:
        return
    _initialized = True
    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key or api_key == _PLACEHOLDER:
            print("[Groq] API key not configured — deterministic fallback active.")
            _available = False
            return
        _client = Groq(api_key=api_key)
        _model_id = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        _available = True
        print(f"[Groq] Service initialized — model: {_model_id}")
    except Exception as e:
        print(f"[Groq] Initialization failed: {e} — deterministic fallback active.")
        _available = False


def groq_available() -> bool:
    if not _initialized:
        _init()
    return _available


def call_groq(prompt: str, max_tokens: int = 1024) -> dict:
    """
    Send a prompt to Groq and return a result dict.
    Returns {"success": bool, "text": str, "error": str|None, "mode": str}
    """
    if not _initialized:
        _init()

    if not _available or _client is None:
        return {
            "success": False, "text": "",
            "error": "Groq not configured — deterministic fallback active.",
            "mode": "fallback",
        }

    try:
        completion = _client.chat.completions.create(
            model=_model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        text = completion.choices[0].message.content.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            inner = lines[1:]
            if inner and inner[-1].strip() == "```":
                inner = inner[:-1]
            text = "\n".join(inner).strip()
        return {"success": True, "text": text, "error": None, "mode": "groq"}
    except Exception as e:
        return {"success": False, "text": "", "error": str(e), "mode": "fallback"}


def get_status() -> dict:
    if not _initialized:
        _init()
    return {
        "configured": _available,
        "model": _model_id if _available else "N/A",
        "mode":  "groq-ai" if _available else "deterministic-fallback",
        "note":  (
            f"Powered by Groq (model: {_model_id})" if _available
            else "Groq not configured — add GROQ_API_KEY to .env to enable."
        ),
    }
