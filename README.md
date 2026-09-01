# Enterprise AI Research Agent

**Modus Enterprise AI Build Challenge — Assignment 9**

> Research topic: How AI and generative models are transforming automotive
> engineering, predictive maintenance, and smart manufacturing.

A structured enterprise research pipeline — not a ChatGPT-with-search wrapper.
Ask a research question; the system searches sources, extracts atomic
findings, classifies them, detects contradictions, and generates conclusions
that are traceable back to the original source text. Everything persists in a
local database + vector store across restarts.

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full system design and how
it satisfies each requirement in the challenge brief.

## Project structure

```
enterprise-ai-research-agent/
├── backend/                # FastAPI application + AI pipeline
│   ├── app/
│   │   ├── main.py         # FastAPI entrypoint
│   │   ├── config.py       # env-driven provider selection
│   │   ├── models.py       # SQLAlchemy schema (traceable research KB)
│   │   ├── database.py     # DB session/engine
│   │   ├── schemas.py      # Pydantic request/response models
│   │   ├── llm/            # BaseLLMClient + Groq/Gemini/Ollama impls
│   │   ├── search/         # BaseSearchClient + Tavily/DuckDuckGo impls
│   │   ├── vectorstore/    # ChromaDB wrapper (local embeddings)
│   │   ├── pipeline/       # orchestrator.py + steps.py — the AI logic
│   │   └── api/routes.py   # HTTP endpoints
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/                # Streamlit dashboard
│   ├── streamlit_app.py
│   ├── requirements.txt
│   └── Dockerfile
├── data/                    # persisted SQLite DB + Chroma vector index (created at runtime)
├── docker-compose.yml
├── ARCHITECTURE.md
└── README.md
```

## Quick start — Option A: Docker (recommended for evaluators)

```bash
cd enterprise-ai-research-agent
cp backend/.env.example backend/.env
# edit backend/.env and set at minimum GROQ_API_KEY (get a free key at console.groq.com)

docker-compose up --build
```

- Backend API: http://localhost:8000/docs (interactive Swagger UI)
- Frontend dashboard: http://localhost:8501

## Quick start — Option B: Run locally without Docker

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: set GROQ_API_KEY (https://console.groq.com/keys — free)
# TAVILY_API_KEY is optional — leave blank and the app auto-falls-back to
# DuckDuckGo search with zero setup.

uvicorn app.main:app --reload --port 8000
```

**Frontend** (in a second terminal):
```bash
cd frontend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

streamlit run streamlit_app.py
```

Open http://localhost:8501, go to the **"Ask a Research Question"** tab, and
either pick an example or type your own — including a completely new question
an evaluator might throw at it live.

## Required API keys (all free)

| Service | Required? | Get a free key |
|---|---|---|
| Groq (default LLM) | Yes, unless you switch to Ollama/Gemini | https://console.groq.com/keys |
| Tavily (search) | No — auto-falls-back to DuckDuckGo if blank | https://tavily.com |
| Gemini (alt LLM) | Only if `LLM_PROVIDER=gemini` | https://aistudio.google.com/apikey |
| Ollama (alt LLM, fully offline) | Only if `LLM_PROVIDER=ollama`; install from https://ollama.com and run `ollama pull llama3.1` | N/A, local |

## Running the "surprise question" test yourself

1. Start the app (either option above).
2. In the frontend, type any new question about AI in automotive/manufacturing
   that wasn't in the example list — e.g. *"How do autonomous mobile robots
   change warehouse operations in automotive parts logistics?"*
3. Watch the pipeline run live: sources found → findings extracted →
   contradictions checked → conclusions generated, each traceable to its
   source.
4. Restart the backend (`Ctrl+C`, re-run `uvicorn ...`) and check the
   **"Research History"** tab — your question and all its findings are still
   there, proving persistence.

## Model & library inventory (all free/open-source/free-tier)

| Component | Library | License | Cost |
|---|---|---|---|
| API framework | FastAPI, Uvicorn | MIT/BSD | Free |
| ORM / DB | SQLAlchemy + SQLite | MIT/Public domain | Free |
| Vector store | ChromaDB | Apache 2.0 | Free, local |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Apache 2.0 | Free, local, runs on CPU |
| LLM (default) | Groq API (`llama-3.3-70b-versatile`) | Free tier | Free (rate-limited) |
| LLM (alt) | Google Gemini API | Free tier | Free (rate-limited) |
| LLM (alt) | Ollama (local) | MIT | Free, fully offline |
| Search (default) | Tavily API | Free tier | Free (rate-limited) |
| Search (fallback) | duckduckgo-search | MIT | Free, no key |
| Frontend | Streamlit | Apache 2.0 | Free |

## Disclosure: where AI coding assistance was used

This repository was scaffolded with AI coding assistance (Claude). The
architecture decisions (layered API/pipeline/data separation, hot-swappable
provider pattern, traceability-by-foreign-key design, similarity-gated
contradiction detection instead of brute-force O(n²) comparison) and every
component's purpose are understood and must be explained live per the
challenge rules — see `ARCHITECTURE.md` for the reasoning behind each choice.
