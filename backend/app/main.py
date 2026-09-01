import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.api.routes import router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Enterprise AI Research Agent",
    description=(
        "Structured enterprise research pipeline: Define Research Questions -> "
        "Search Sources -> Collect Information -> Store Sources -> Extract Findings "
        "-> Compare Evidence -> Classify Findings -> Detect Contradictions -> "
        "Generate Conclusions -> Maintain Traceability."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local demo only; tighten for real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(router, prefix="/api")
