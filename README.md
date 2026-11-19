# 🛡️ CyberRakshak AI
### AI-Powered Cybercrime Reporting & Response Support Platform

**Hackathon:** Inter-Institute IBM Bob Hackathon with IBM SkillsBuild  
**Problem Statement:** 19 — AI-Powered Cybercrime Reporting & Response Support Agent  
**Tagline:** Detect. Understand. Organize. Report. Protect.  
**Primary Users:** Residents of Bengaluru, India

---

## Quick Start

### 1. Configure Environment

```
# Copy the example env file
copy .env.example .env

# Edit .env — fill in your credentials:
#   GEMINI_API_KEY    — from https://aistudio.google.com/app/apikey
#   MYSQL_PASSWORD    — your local MySQL root password
```

### 2. Set Up MySQL Database

```sql
-- Run from MySQL client or Workbench:
source database/schema.sql
-- Optional demo data:
source database/seed_demo.sql
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the Application

```bash
python backend/app.py
```

Open: **http://localhost:5000**

---

## Environment Variables (.env)

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ For AI | Google AI Studio API key |
| `GEMINI_MODEL` | Optional | Default: `gemini-2.0-flash` |
| `GOOGLE_CLOUD_PROJECT_ID` | Optional | Google Cloud Project ID |
| `MYSQL_HOST` | ✅ | MySQL host (default: `localhost`) |
| `MYSQL_PORT` | ✅ | MySQL port (default: `3306`) |
| `MYSQL_USER` | ✅ | MySQL username |
| `MYSQL_PASSWORD` | ✅ | MySQL password |
| `MYSQL_DATABASE` | ✅ | Database name (default: `cyberrakshak_db`) |
| `SECRET_KEY` | ✅ | Flask secret key |
| `FLASK_DEBUG` | Optional | `true` for development |

---

## Architecture

```
User (Browser) → Flask Backend → Central Orchestrator
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              ↓                         ↓                         ↓
    1. Privacy Protection     2. Incident Intake       3. Scam Analysis
       (regex-based, no AI)     (Gemini / fallback)     (Gemini / fallback)
              ↓                         ↓                         ↓
    4. Evidence Organizer     5. Reporting Guidance    6. Guidance Dashboard
       (Gemini / fallback)     (Gemini / fallback)     (Gemini / fallback)
              │
              ↓
         MySQL Database  +  Downloadable Report
```

---

## Six AI Agents

| Agent | AI | Responsibility |
|---|---|---|
| Privacy Protection | Deterministic (regex) | Redacts OTP, PIN, CVV, Aadhaar before AI processing |
| Incident Intake | Gemini / Fallback | Classifies and structures the incident |
| Scam Analysis | Gemini / Fallback | Identifies risk indicators, assesses risk level |
| Evidence Organizer | Gemini / Fallback | Organizes files, builds timeline |
| Reporting Guidance | Gemini / Fallback | Provides official Indian reporting channels |
| Guidance Dashboard | Gemini / Fallback | Consolidates all outputs into one report |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/incidents` | Submit incident (triggers all agents) |
| GET | `/api/incidents` | List all incidents |
| GET | `/api/incidents/<id>` | Get incident detail |
| POST | `/api/incidents/<id>/evidence` | Upload additional evidence |
| GET | `/api/incidents/<id>/report` | Download text report |
| POST | `/api/incidents/<id>/analyze` | Re-analyze existing incident |

---

## Official Reporting Resources

- **1930** — Financial Cyber Fraud Helpline (24/7)
- **https://cybercrime.gov.in/** — National Cyber Crime Reporting Portal
- **https://i4c.mha.gov.in/** — Indian Cyber Crime Coordination Centre
- **https://www.ceir.gov.in/** — CEIR (Block stolen device)
- **https://sachet.rbi.org.in/** — RBI Sachet (Financial fraud)

---

## Disclaimer

CyberRakshak AI is a victim-support and guidance platform.

- It does **not** submit official complaints on behalf of users.
- It does **not** verify criminal activity or identify criminals.
- It does **not** access police databases.
- AI analysis identifies **potential indicators only**.
- Always use official government portals to file complaints.

---

## Demonstration Scenario

Load the **"Demo Scenario"** button on the home page to simulate:

> A Bengaluru resident receives a fake KYC SMS from an impersonated bank, clicks a phishing link, and loses ₹5,000 via UPI.

This is **synthetic data** clearly labelled as a demonstration. It is not a real case.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| IBM Bob | Development environment |
| Google Gemini AI (`google-genai`) | Primary AI intelligence |
| Python 3.14 + Flask | Backend |
| HTML5 + CSS3 + Vanilla JS | Frontend |
| MySQL 8.0 | Persistent storage |

---

*CyberRakshak AI — Built for the IBM Bob Hackathon with IBM SkillsBuild*
