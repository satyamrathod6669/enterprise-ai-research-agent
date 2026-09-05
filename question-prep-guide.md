# Enterprise AI Research Agent — Explanation Guide

## PART 1: The 30-second answer (memorize this)

> "I built a full-stack AI application that does structured research instead of
> just generating a ChatGPT answer. You type a question, it searches the real
> web, pulls out specific facts from each source separately, checks if any
> facts contradict each other, and only then writes conclusions — and every
> conclusion is traceable back to the exact fact and source it came from. It's
> deployed live on Render with a FastAPI backend and Streamlit frontend."

Say this FIRST, before anything technical. It gives them the "what" before the "how."

---

## PART 2: The code flow, traced step by step

This is literally what happens, in order, when someone clicks "Run Research Pipeline."
Reference these exact file names when you explain — it proves you know where things live.

### Step 0 — The click happens
**File: `frontend/streamlit_app.py`**
The button click triggers a `requests.post()` call to your backend's URL, sending the
question as JSON: `{"question_text": "..."}`. The frontend does NOTHING else — no AI
logic, no database access. Its only job is display + sending/receiving HTTP requests.

### Step 1 — The request arrives at the backend
**File: `backend/app/main.py`** → **`backend/app/api/routes.py`**
FastAPI receives the POST request at `/api/questions`. The function `create_question()`
in `routes.py` runs. It immediately:
1. Creates a new `ResearchQuestion` database row with status `"pending"`
2. Saves it to the database (so even if everything after this crashes, the question itself is recorded)
3. Calls `run_research_pipeline()` to actually do the work

### Step 2 — The orchestrator takes over
**File: `backend/app/pipeline/orchestrator.py`**
This is the "conductor" — it doesn't do any AI work itself, it just calls the right
functions in the right order and saves results to the database after each one:

1. **Get the LLM client** — `get_llm_client()` from `llm/factory.py` reads your `.env`
   file's `LLM_PROVIDER` setting and returns either a Groq, Gemini, or Ollama client.
   The rest of the code doesn't know or care which one it got — this is called the
   **"strategy pattern"** in software design: swap the tool without touching the code
   that uses it.

2. **Search the web** — `get_search_client().search(question)` calls either Tavily or
   DuckDuckGo (same pattern — `search/factory.py` decides which). Returns a list of
   raw web pages (URL, title, text content).

3. **Save each source** — for each web page found, a `Source` database row is created
   (`models.py` defines this table) with the URL, title, and raw text. This happens
   BEFORE any AI processing, so you have a permanent record of what was found.

4. **Extract findings, per source, one at a time** — `steps.py`'s `extract_findings()`
   function is called ONCE PER SOURCE (not once for everything). For each source, it
   sends the AI a prompt like: "pull out specific factual claims from this text
   related to [question]." The AI returns a JSON list of facts. Each fact becomes a
   `Finding` row in the database, linked to that specific source via `source_id`.

5. **Classify + embed each finding** — each finding also gets a category tag
   (risk/statistic/case study/etc, decided by the AI) and gets added to the
   vector store (`vectorstore/chroma_store.py`) — this converts the finding's text
   into a list of numbers (an "embedding") that lets the system later find
   semantically similar findings, even if worded completely differently.

6. **Check for contradictions** — for each finding, the system asks the vector store
   "find findings that are similar to this one" (via `chroma_store.find_similar()`).
   For any similar pair, it asks the AI directly: "do these two facts actually
   contradict each other?" If yes, a `Contradiction` row is saved.
   **This is the key efficiency trick**: it does NOT compare every possible pair of
   findings (that would be too slow at scale) — only pairs already flagged as
   topically similar get the expensive "do these actually conflict" AI check.

7. **Generate conclusions** — `generate_conclusions()` in `steps.py` gets ALL the
   findings (with their database IDs) and is told: "write conclusions using ONLY
   these findings, and you must cite which finding IDs support each conclusion."
   This forced citation is what makes the output traceable instead of just prose.

8. **Mark the question complete** — status changes from `"pending"` to `"completed"`.

### Step 3 — The response goes back
The API returns the finished `ResearchQuestion` (with its ID). The frontend then
calls `GET /api/questions/{id}` to fetch the FULL detail — sources, findings,
contradictions, conclusions — and renders it all on screen.

### Step 4 — Traceability, on demand
**File: `backend/app/api/routes.py`** → `trace_finding()` function
When you click "Source & Traceability Lookup" and paste a finding ID, this endpoint
looks up that `Finding` row, follows its `source_id` foreign key to the `Source`
table, and returns the original URL + excerpt. This is a simple database JOIN,
nothing fancy — but it's what "traceability" means concretely.

---

## PART 3: Likely recruiter questions + model answers

### "Walk me through the architecture."
> "Four layers: Streamlit frontend for the UI, FastAPI backend for the API layer,
> a pipeline module that does the actual AI orchestration, and SQLite plus ChromaDB
> for storage — a relational database for structured records and a vector database
> for semantic similarity search."

### "Why not just use ChatGPT directly?"
> "A single prompt can't be traced, checked for contradictions, or made to cite
> its sources. My pipeline breaks the work into separate steps — search, extract,
> classify, compare, conclude — and saves the result of every step to a database,
> so every conclusion can be traced back to a specific fact and a specific source."

### "What happens if I give it a completely new question right now?"
> "It'll work immediately — nothing in the code is hard-coded to a specific topic.
> The `question_text` field accepts anything, and the same generic pipeline runs
> regardless of what the topic is." *(Then actually demo it live with a surprise question.)*

### "How does it decide if two findings contradict each other?"
> "First it uses vector similarity search to find findings that are topically
> related — cheap and fast. Only for those candidate pairs does it make an
> actual AI call asking 'do these contradict each other, or just cover the
> same topic?' This avoids comparing every possible pair, which wouldn't scale."

### "What would happen with 1,000 questions instead of a handful?"
> "Each question is an independent database row processed by the same generic
> pipeline — no per-question code, so it scales horizontally. The real bottleneck
> would be LLM and search API rate limits, plus the fact that right now each
> request runs synchronously and blocks until done. For real scale, I'd add a
> background task queue so the API responds immediately and the pipeline runs
> asynchronously — the orchestrator function itself wouldn't need to change."

### "What was the hardest bug you fixed?"
> "My backend kept crashing on Render's free tier with an out-of-memory error.
> I traced it to my vector embedding library — I was using sentence-transformers,
> which pulls in a full PyTorch stack, way too heavy for a 512MB instance. I
> switched to ChromaDB's built-in ONNX-based embedder, which uses the same
> underlying model but a much lighter runtime, and the crashes stopped."

### "Did you use AI tools to build this?"
> "Yes — the challenge brief explicitly allows and expects that. I used Claude as
> a coding assistant, but I made every architecture decision, and every bug I
> hit — memory crashes, dependency conflicts, Python version issues — I diagnosed
> myself by reading the actual error logs and understanding why it happened,
> not just pasting errors back into a chatbot blindly."

### "Why Render instead of AWS?"
> "Given the 2-day deadline, Render let me connect GitHub and deploy immediately
> with zero infrastructure setup. AWS is more powerful but needs IAM roles, VPCs,
> load balancers — that setup alone could've eaten hours I didn't have. Render's
> free tier also doesn't require a credit card, unlike AWS's free tier."

### "What's a limitation of your current design?"
> "Two honest ones: it processes requests synchronously, which doesn't scale well
> under heavy concurrent load — I'd fix that with a background task queue. And
> contradiction detection only checks similarity-flagged pairs, so it could
> theoretically miss a contradiction between two findings that are worded very
> differently but conceptually conflict."

---

## PART 4: Quick vocabulary check (make sure these roll off your tongue)

- **API** = how the frontend and backend talk to each other over HTTP
- **Foreign key** = a field in one database table that points to a row in another table (this is literally what "traceability" is built from)
- **Vector embedding** = converting text into a list of numbers so a computer can measure how "similar" two pieces of text are
- **Hot-swappable** = can change which tool is used (Groq vs Gemini) via a config setting, no code changes
- **Synchronous** = the request waits until the whole pipeline finishes before responding (a current limitation)
- **ONNX** = a lightweight way to run AI models, used here instead of heavier PyTorch to save memory
