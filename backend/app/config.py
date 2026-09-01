"""
Central configuration for the Enterprise AI Research Agent.

All provider selection is driven by environment variables so the system can be
hot-swapped between local and hosted, free-tier components with zero code changes
(per challenge requirement: "must be reproducible without purchasing software
licences" and "no hard-coded outputs").
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR") or (BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- Database -----------------------------------------------------------
SQLITE_PATH = DATA_DIR / "research_agent.db"
# Use `or` (not just getenv's default arg) so a blank DATABASE_URL= line left
# in .env falls back correctly instead of producing an empty connection string.
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{SQLITE_PATH}"

# --- Vector store ---------------------------------------------------------
CHROMA_PERSIST_DIR = str(DATA_DIR / "chroma")

# --- LLM provider ---------------------------------------------------------
# One of: "groq", "gemini", "ollama"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

# --- Search provider --------------------------------------------------------
# One of: "tavily", "duckduckgo". Falls back to duckduckgo automatically if
# TAVILY_API_KEY is missing, so the app runs with ZERO external keys configured.
SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "tavily").lower()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
MAX_SOURCES_PER_QUESTION = int(os.getenv("MAX_SOURCES_PER_QUESTION", "6"))

# --- Embeddings for the vector store ----------------------------------------
# Local, free, no API key required (sentence-transformers via chromadb default,
# or explicit model name below).
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
