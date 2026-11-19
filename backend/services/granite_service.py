"""
CyberRakshak AI — IBM Granite Service (via IBM watsonx.ai)
Supports three separate Granite model instances:
  - granite_intake   : ibm/granite-3-3-8b-instruct   → Incident Intake Agent
  - granite_scam     : ibm/granite-3-3-2b-instruct   → Scam Analysis Agent
  - granite_evidence : ibm/granite-3-1-8b-instruct   → Evidence Organization Agent

Each instance is independently configured via env vars so different
IBM Cloud API keys / project IDs can be used if needed.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# ── Per-instance state ────────────────────────────────────────────────────────
_clients = {}       # role → ModelInference instance
_available = {}     # role → bool
_initialized = {}   # role → bool

ROLES = {
    "intake": {
        "api_key_env":    "GRANITE_INTAKE_API_KEY",
        "project_id_env": "GRANITE_INTAKE_PROJECT_ID",
        "url_env":        "GRANITE_INTAKE_URL",
        "model_env":      "GRANITE_INTAKE_MODEL",
        "default_model":  "meta-llama/llama-3-3-70b-instruct",
        "label":          "Llama 3.3 70B via watsonx (Intake)",
    },
    "scam": {
        "api_key_env":    "GRANITE_SCAM_API_KEY",
        "project_id_env": "GRANITE_SCAM_PROJECT_ID",
        "url_env":        "GRANITE_SCAM_URL",
        "model_env":      "GRANITE_SCAM_MODEL",
        "default_model":  "meta-llama/llama-3-3-70b-instruct",
        "label":          "Llama 3.3 70B via watsonx (Scam)",
    },
    "evidence": {
        "api_key_env":    "GRANITE_EVIDENCE_API_KEY",
        "project_id_env": "GRANITE_EVIDENCE_PROJECT_ID",
        "url_env":        "GRANITE_EVIDENCE_URL",
        "model_env":      "GRANITE_EVIDENCE_MODEL",
        "default_model":  "meta-llama/llama-3-3-70b-instruct",
        "label":          "Llama 3.3 70B via watsonx (Evidence)",
    },
}

_PLACEHOLDER = "your_ibm_watsonx_api_key_here"


def _init_role(role: str):
    """Lazy-initialise one Granite role."""
    if _initialized.get(role):
        return
    _initialized[role] = True
    cfg = ROLES[role]

    api_key    = os.getenv(cfg["api_key_env"], "")
    project_id = os.getenv(cfg["project_id_env"], "")
    url        = os.getenv(cfg["url_env"], "https://us-south.ml.cloud.ibm.com")
    model_id   = os.getenv(cfg["model_env"], cfg["default_model"])

    if not api_key or api_key == _PLACEHOLDER or not project_id:
        print(f"[Granite:{role}] Not configured — deterministic fallback active.")
        _available[role] = False
        return

    try:
        from ibm_watsonx_ai import APIClient, Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference

        credentials = Credentials(url=url, api_key=api_key)
        client = APIClient(credentials=credentials, project_id=project_id)
        _clients[role] = ModelInference(
            model_id=model_id,
            api_client=client,
        )
        _available[role] = True
        print(f"[Granite:{role}] Initialized — model: {model_id}")
    except Exception as e:
        print(f"[Granite:{role}] Init failed: {e} — deterministic fallback active.")
        _available[role] = False


def granite_available(role: str) -> bool:
    if not _initialized.get(role):
        _init_role(role)
    return _available.get(role, False)


def call_granite(role: str, prompt: str, max_tokens: int = 1024) -> dict:
    """
    Call a Granite model for the given role.
    Returns {"success": bool, "text": str, "error": str|None, "mode": str}
    """
    if not _initialized.get(role):
        _init_role(role)

    if not _available.get(role):
        return {
            "success": False, "text": "",
            "error": f"Granite [{role}] not configured — fallback active.",
            "mode": "fallback",
        }

    cfg   = ROLES[role]
    model = os.getenv(cfg["model_env"], cfg["default_model"])

    try:
        client: "ModelInference" = _clients[role]
        # Use chat API (faster, non-deprecated)
        response = client.chat(
            messages=[{"role": "user", "content": prompt}],
            params={
                "max_tokens": max_tokens,
                "temperature": 0.3,
            },
        )
        # chat() response structure
        text = ""
        if isinstance(response, dict):
            choices = response.get("choices", [{}])
            text = choices[0].get("message", {}).get("content", "") if choices else ""
        else:
            text = str(response)

        text = text.strip()
        # Strip stray markdown fences
        if text.startswith("```"):
            lines = text.split("\n")
            inner = lines[1:]
            if inner and inner[-1].strip() == "```":
                inner = inner[:-1]
            text = "\n".join(inner).strip()

        return {"success": True, "text": text, "error": None, "mode": f"granite-{role}"}
    except Exception as e:
        return {"success": False, "text": "", "error": str(e), "mode": "fallback"}


def get_all_status() -> dict:
    """Return configured status for all three Granite roles."""
    result = {}
    for role, cfg in ROLES.items():
        avail = granite_available(role)
        result[role] = {
            "configured": avail,
            "model": os.getenv(cfg["model_env"], cfg["default_model"]) if avail else "N/A",
            "label": cfg["label"],
            "mode":  "granite-ai" if avail else "deterministic-fallback",
        }
    return result
