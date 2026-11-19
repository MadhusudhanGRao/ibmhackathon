"""
CyberRakshak AI — Simple server launcher
Run: python run_server.py
"""
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from backend.config import Config
from backend.app import app

print("\n" + "=" * 60)
print("  CyberRakshak AI — Server Starting")
print("=" * 60)

# DB init
try:
    from backend.database import init_db, test_connection
    init_db()
    db_ok = test_connection()
    print(f"[DB] MySQL: {'Connected' if db_ok else 'Unavailable (non-fatal)'}")
except Exception as e:
    print(f"[DB] Skipped: {e}")

print("  LLM services will initialize on first request.")
print("=" * 60)
print("  Open in browser: http://localhost:5000")
print("=" * 60 + "\n")

app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)
