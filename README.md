# sam-v2-intelligence

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688)](https://fastapi.tiangolo.com)

The **SAM v2 intelligence and backend layer** for the Crypto Moonboys ecosystem. This repo owns the intelligence, scoring, ranking, and bible systems that underpin the SAM knowledge engine.

---

## 🏗️ Role in the 3-Repo System

| Repo | Role |
|------|------|
| [`HODLKONG64/HAY-MUM-IM-BUILDING-AGENTS-OF-CHANGE`](https://github.com/HODLKONG64/HAY-MUM-IM-BUILDING-AGENTS-OF-CHANGE) | Brain / Orchestrator — SAM Master Agent, crawl/validate/publish pipeline |
| **This repo — `sam-v2-intelligence`** | Intelligence / Backend Layer — scoring, ranking, memory, bible endpoints |
| [`Crypto-Moonboys/Crypto-Moonboys.github.io`](https://github.com/Crypto-Moonboys/Crypto-Moonboys.github.io) | Wiki / Display Layer — public-facing GitHub Pages encyclopedia |

> **Current frontend strategy:** The wiki site consumes static GitHub-served JSON/files. `sam-v2-intelligence` is not a live-hosted dependency for the frontend at this time — it is the intelligence layer whose outputs feed into the static publishing pipeline.

---

## 🧠 What This Repo Owns

| Domain | Description |
|--------|-------------|
| **Scoring** | Entity relevance and quality scoring |
| **Ranking** | Entity leaderboard and priority ranking |
| **Memory** | Structured entity memory management |
| **Focus Plan** | SAM cycle focus prioritisation logic |
| **Leaderboard** | Top entity leaderboard generation |
| **Keyword Bank** | Keyword discovery and management |
| **Bible Endpoints** | `/bibles/{entity_name}` — entity bible content API |
| **Dashboard** | Intelligence dashboard and reporting layer |

---

## 📖 SAM Bible System

The bible system generates rich entity knowledge summaries for priority wiki pages. Frontend hooks have been added to the top 10 priority entity pages in the wiki:

- `data-entity-slug` on `<article>` — identifies the entity
- `<div id="bible-content"></div>` before `</article>` — injection target

**Status:** Hooks activated on selected priority pages (`bitcoin`, `ethereum`, `nfts`, `defi`, `graffpunks`, `hodl-wars`, `crypto-moonboys`, `blockchain`, `waxp`, `xrpl`). Bible content generation and display is ongoing — not yet active across all wiki pages.

---

## 🛠️ Stack

- **Python 3.11+**
- **FastAPI** — API framework
- **Uvicorn** — ASGI server
- **Pydantic** — data validation
- **boto3** — Cloudflare R2 / S3-compatible storage
- **HTML + Jinja2** — dashboard templating

---

## 📂 File Structure

```
/
├── main.py                  ← FastAPI app entry point
├── routers/
│   ├── bibles.py            ← /bibles/{entity_name} endpoints
│   ├── leaderboard.py       ← /leaderboard endpoints
│   ├── ranking.py           ← /ranking endpoints
│   ├── keyword_bank.py      ← /keyword-bank endpoints
│   ├── focus_plan.py        ← /focus-plan endpoints
│   └── memory.py            ← /memory endpoints
├── services/
│   ├── scoring.py           ← Entity scoring logic
│   ├── bible_generator.py   ← Bible content generation
│   └── memory_manager.py    ← Memory read/write
├── templates/
│   └── dashboard.html       ← Intelligence dashboard
├── static/                  ← Dashboard static assets
├── requirements.txt
├── .env.example
└── .github/
    └── workflows/
```

---

## 🚀 Setup

### Requirements
- Python 3.11+
- Cloudflare R2 credentials (for memory access)
- xAI Grok API key (for bible generation)

### Local Development
```bash
# 1. Clone repo
git clone https://github.com/HODLKONG64/sam-v2-intelligence.git
cd sam-v2-intelligence

# 2. Create .env file
cp .env.example .env

# 3. Edit .env and add:
# XAI_API_KEY=your_key_here
# R2_ENDPOINT_URL=your_r2_endpoint
# R2_ACCESS_KEY_ID=your_r2_key
# R2_SECRET_ACCESS_KEY=your_r2_secret
# R2_BUCKET=sam-memory

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the API
uvicorn main:app --reload
```

API will be available at `http://localhost:8000`
Dashboard at `http://localhost:8000/dashboard`

---

## 🔗 Related Repos

- **Brain / Orchestrator:** [`HODLKONG64/HAY-MUM-IM-BUILDING-AGENTS-OF-CHANGE`](https://github.com/HODLKONG64/HAY-MUM-IM-BUILDING-AGENTS-OF-CHANGE)
- **Wiki / Frontend:** [`Crypto-Moonboys/Crypto-Moonboys.github.io`](https://github.com/Crypto-Moonboys/Crypto-Moonboys.github.io)

---

## License

Fan content — not for commercial use. **Not financial advice.**