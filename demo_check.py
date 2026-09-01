"""
Optional helper for rehearsing your live demo before presenting.

Usage (with the backend already running on localhost:8000):
    python demo_check.py "How is generative AI used in automotive quality inspection?"

This just calls the same POST /api/questions endpoint the Streamlit UI uses —
it's a convenience script for a quick terminal-based dry run, not a separate
code path, so passing this test means the actual app will work too.
"""
import sys
import json
import time
import requests

API_BASE = "http://localhost:8000/api"


def main():
    question = " ".join(sys.argv[1:]) or "How is AI used in predictive maintenance for automotive manufacturing?"
    print(f"Submitting research question: {question!r}")
    start = time.time()
    try:
        resp = requests.post(f"{API_BASE}/questions", json={"question_text": question}, timeout=300)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"ERROR: could not reach backend at {API_BASE}. Is `uvicorn app.main:app` running?\n{e}")
        sys.exit(1)

    result = resp.json()
    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.1f}s. Status: {result['status']}")

    detail = requests.get(f"{API_BASE}/questions/{result['id']}").json()
    print(f"Sources: {len(detail['sources'])}  Findings: {len(detail['findings'])}  "
          f"Contradictions: {len(detail['contradictions'])}  Conclusions: {len(detail['conclusions'])}")

    print("\n--- Conclusions ---")
    for c in detail["conclusions"]:
        print(f"- {c['summary']}")
        print(f"  (supported by findings: {c['supporting_finding_ids']})")

    if not detail["conclusions"]:
        print("No conclusions generated — check backend logs for LLM/search errors "
              "(likely a missing or invalid API key in backend/.env).")


if __name__ == "__main__":
    main()
