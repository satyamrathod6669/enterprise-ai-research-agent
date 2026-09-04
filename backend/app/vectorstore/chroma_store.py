"""
Persistent local vector store for findings, using ChromaDB with its built-in
free, local sentence-transformers embedding function (no API key, no cost).

This is what makes the knowledge base "reusable" across research questions:
before writing a brand-new finding, we can check whether a semantically
similar finding already exists (from a prior, unrelated research run) and
link to it instead of duplicating research effort.
"""
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions

from app import config

_client = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection
    _client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
    embed_fn = embedding_functions.DefaultEmbeddingFunction()
    
    _collection = _client.get_or_create_collection(
        name="findings",
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def add_finding(finding_id: str, statement: str, metadata: dict):
    col = get_collection()
    col.add(ids=[finding_id], documents=[statement], metadatas=[metadata])


def find_similar(statement: str, n_results: int = 5, exclude_id: Optional[str] = None):
    col = get_collection()
    count = col.count()
    if count == 0:
        return []
    res = col.query(query_texts=[statement], n_results=min(n_results, count))
    out = []
    ids = res.get("ids", [[]])[0]
    docs = res.get("documents", [[]])[0]
    dists = res.get("distances", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    for fid, doc, dist, meta in zip(ids, docs, dists, metas):
        if exclude_id and fid == exclude_id:
            continue
        out.append({"id": fid, "statement": doc, "distance": dist, "metadata": meta})
    return out
