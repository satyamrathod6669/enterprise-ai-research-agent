# Architecture — Enterprise AI Research Agent

## Chosen case
**Research topic:** How AI and generative models are transforming automotive
engineering, predictive maintenance, and smart manufacturing.

This is Assignment 9 (Enterprise AI Research Agent) from the Modus Enterprise
AI Build Challenge: a system that conducts *structured, repeatable* enterprise
research — not a one-shot LLM+search wrapper.

## Layered architecture (maps to the brief's mandatory gate)

```
┌─────────────────────────────────────────────────────────────┐
│  USER INTERFACE — Streamlit dashboard (frontend/)             │
│  - Ask new research question (incl. live "surprise" question) │
│  - Browse research history (proves persistence)               │
│  - Trace any finding back to its source                       │
└───────────────────────────┬─────────────────────────────────┘
                             │ HTTP (JSON)
┌───────────────────────────▼─────────────────────────────────┐
│  APPLICATION / API LAYER — FastAPI (backend/app/api, main.py)│
│  POST /api/questions            → runs full pipeline          │
│  GET  /api/questions             → list all research runs     │
│  GET  /api/questions/{id}        → full detail + traceability │
│  GET  /api/findings/{id}/trace   → finding → source provenance│
└───────────────────────────┬─────────────────────────────────┘
                             │
┌───────────────────────────▼─────────────────────────────────┐
│  AI INTELLIGENCE LAYER — backend/app/pipeline, llm/           │
│  Orchestrator runs, in order, persisting after each step:     │
│   1. Search Sources        (search/ abstraction)               │
│   2. Collect Information                                       │
│   3. Store Sources          → relational DB                    │
│   4. Extract Findings       → LLM, per-source, atomic claims   │
│   5. Classify Findings      → LLM-assigned category            │
│   6. Compare Evidence       → vector similarity (Chroma)        │
│   7. Detect Contradictions  → LLM judges candidate-similar pairs│
│   8. Generate Conclusions   → LLM synthesis, cites finding ids  │
│   9. Maintain Traceability  → every row carries FK back to     │
│                                its source/finding               │
│  LLM provider is hot-swappable: Groq | Gemini | Ollama          │
│  (single env var, `BaseLLMClient` interface, zero code changes) │
└───────────────────────────┬─────────────────────────────────┘
                             │
┌───────────────────────────▼─────────────────────────────────┐
│  DATA & KNOWLEDGE LAYER                                        │
│  - SQLite (SQLAlchemy ORM) — questions, sources, findings,     │
│    contradictions, conclusions. Persistent file on disk.       │
│  - ChromaDB (local, persistent) — vector index of findings,    │
│    used to find semantically related findings across ALL past  │
│    research runs (this is what makes the KB "reusable" rather  │
│    than siloed per-question).                                  │
└───────────────────────────┬─────────────────────────────────┘
                             │
┌───────────────────────────▼─────────────────────────────────┐
│  EXTERNAL RESEARCH / DATA                                      │
│  - Tavily Search API (free tier) — primary                     │
│  - DuckDuckGo (duckduckgo-search, zero API key) — automatic    │
│    fallback if Tavily is unconfigured/unavailable/rate-limited │
└─────────────────────────────────────────────────────────────┘
```

## Why this satisfies the "not accepted" list

- **Not a ChatGPT wrapper**: the LLM is called multiple times per research
  question, each time for a narrow, structured sub-task (classify source,
  extract findings, compare two findings, synthesize conclusions) — never
  "answer this research question" in one giant prompt.
- **Not hard-coded**: `POST /api/questions` accepts arbitrary `question_text`
  at runtime. Nothing about the topic, sources, or output is hard-coded — the
  automotive/manufacturing case study is just the *demo* topic; the pipeline
  itself is domain-agnostic (see "1,000 processes tomorrow" test below).
- **Not a notebook or static HTML**: real client-server app, two processes,
  HTTP between them, containerizable.
- **Persists across restarts**: SQLite file + Chroma persistent directory
  both live under `data/`, mounted as a Docker volume. Restarting either
  service does not lose research history.
- **Traceable**: every `Finding` row has a `source_id` FK; every `Conclusion`
  stores `supporting_finding_ids`. The `/api/findings/{id}/trace` endpoint and
  the "Source & Traceability Lookup" UI tab let a judge click from a
  conclusion all the way back to the original source excerpt.

## Answering the brief's key judging question

> "If we give your application 1,000 processes tomorrow instead of 100,
> what happens?"

Reframed for Assignment 9: *"If we give your application 1,000 new research
questions tomorrow, what happens?"*

- Each question is an independent row in `research_questions`; the pipeline
  has no per-question hard-coded logic, so it scales horizontally — the
  bottleneck is LLM/search API rate limits, not code.
- The vector store means questions #501–1000 benefit from findings already
  extracted by questions #1–500 (semantic similarity search surfaces prior
  findings before the system asks the LLM to re-derive them from scratch,
  and contradiction-detection compares new findings against the *entire*
  historical set, not just the current run).
- For real production scale you would swap SQLite → Postgres and add a task
  queue (Celery/RQ) so `POST /api/questions` returns immediately and the
  pipeline runs as a background job — the orchestrator function itself
  wouldn't need to change, since it's already decoupled from the API layer.

## What happens if a free-tier service becomes unavailable?

| Service | Fallback | How |
|---|---|---|
| Tavily (search) | DuckDuckGo (`duckduckgo-search`) | `SEARCH_PROVIDER=duckduckgo` in `.env`, or automatic if `TAVILY_API_KEY` is blank |
| Groq (LLM) | Gemini free tier, or local Ollama | `LLM_PROVIDER=gemini` or `LLM_PROVIDER=ollama` in `.env` — zero code changes |
| Chroma embeddings | N/A — runs 100% locally via `sentence-transformers`, no external dependency at all |

## Known limitations (disclosed honestly, as the brief asks)

- Contradiction detection only compares findings that the vector store judges
  as semantically similar (distance ≤ 0.6) — it does not do an exhaustive
  O(n²) LLM comparison of every finding pair, which would not scale.
- Source-type classification and finding extraction rely on LLM judgment and
  can occasionally mis-classify or under/over-extract — this is disclosed as
  a real limitation, not hidden.
- `POST /api/questions` currently runs the pipeline synchronously (blocking
  the HTTP request) for demo simplicity/predictability. Documented above as
  the first thing to change for production scale.
