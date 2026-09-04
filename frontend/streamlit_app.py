"""
Enterprise AI Research Agent — Streamlit dashboard.

This is purely a UI layer: it calls the FastAPI backend over HTTP for every
piece of data and holds no research logic itself. That separation is what
lets the architecture diagram show a real UI -> API -> AI -> Data flow
instead of one monolithic script.
"""
import os
import time

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")

st.set_page_config(page_title="Enterprise AI Research Agent", layout="wide")
st.title("🔎 Enterprise AI Research Agent")
st.caption(
    "Automotive Engineering, Predictive Maintenance & Smart Manufacturing — "
    "AI transformation research, backed by a persistent, traceable knowledge base."
)

tab_ask, tab_history, tab_trace = st.tabs(
    ["🧠 Ask a Research Question", "📚 Research History", "🔗 Source & Traceability Lookup"]
)

# ---------------------------------------------------------------------------
# TAB 1 — Ask a new research question (this is the "surprise question" entry point)
# ---------------------------------------------------------------------------
with tab_ask:
    st.subheader("Ask a new research question")
    st.write(
        "Enter ANY research question about AI in automotive engineering, predictive "
        "maintenance, or smart manufacturing — including one you invent on the spot. "
        "The pipeline is fully generic; nothing here is hard-coded."
    )
    example_qs = [
        "How is generative AI changing automotive quality inspection?",
        "What AI techniques are used for predictive maintenance in manufacturing plants?",
        "How are digital twins used in smart factories today?",
    ]
    chosen_example = st.selectbox("Or pick an example:", ["(type my own below)"] + example_qs)
    default_text = "" if chosen_example == "(type my own below)" else chosen_example
    question_text = st.text_area("Research question", value=default_text, height=80)

    if st.button("Run Research Pipeline", type="primary", disabled=not question_text.strip()):
        with st.status("Running research pipeline...", expanded=True) as status:
            st.write("① Searching sources...")
            try:
                resp = requests.post(f"{API_BASE}/questions", json={"question_text": question_text}, timeout=580)
                resp.raise_for_status()
                result = resp.json()
                st.write("② Extracting & classifying findings...")
                st.write("③ Comparing evidence & detecting contradictions...")
                st.write("④ Generating traceable conclusions...")
                status.update(label="Pipeline complete ✅", state="complete")
                st.session_state["last_question_id"] = result["id"]
            except requests.exceptions.RequestException as e:
                status.update(label="Pipeline failed ❌", state="error")
                st.error(f"Could not reach backend at {API_BASE}. Is `uvicorn app.main:app` running? Details: {e}")

    if st.session_state.get("last_question_id"):
        qid = st.session_state["last_question_id"]
        detail = requests.get(f"{API_BASE}/questions/{qid}").json()

        st.divider()
        st.subheader(f"Results: {detail['question_text']}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sources", len(detail["sources"]))
        c2.metric("Findings", len(detail["findings"]))
        c3.metric("Contradictions", len(detail["contradictions"]))
        c4.metric("Conclusions", len(detail["conclusions"]))

        st.markdown("### 📌 Conclusions (traceable to findings)")
        for c in detail["conclusions"]:
            with st.container(border=True):
                st.markdown(f"**{c['summary']}**")
                st.caption(f"Supported by findings: {c['supporting_finding_ids']}")
                if c.get("caveat"):
                    st.warning(c["caveat"])

        with st.expander(f"🔬 All extracted findings ({len(detail['findings'])})"):
            for f in detail["findings"]:
                st.markdown(f"- `[{f['classification']}, conf={f['confidence']:.2f}]` {f['statement']}  "
                            f"·  _finding id: `{f['id']}`_")

        if detail["contradictions"]:
            with st.expander(f"⚠️ Contradictions detected ({len(detail['contradictions'])})"):
                for ct in detail["contradictions"]:
                    st.markdown(f"**Severity: {ct['severity']}** — {ct['explanation']}")

        with st.expander(f"🌐 Sources used ({len(detail['sources'])})"):
            for s in detail["sources"]:
                st.markdown(f"- [{s['title'] or s['url']}]({s['url']})  ·  type: `{s['source_type']}`")

# ---------------------------------------------------------------------------
# TAB 2 — Browse all past research (proves persistence across restarts)
# ---------------------------------------------------------------------------
with tab_history:
    st.subheader("Research knowledge base history")
    st.write("Every question ever run is persisted here — restarting the app does not erase it.")
    if st.button("Refresh history"):
        st.rerun()
    try:
        questions = requests.get(f"{API_BASE}/questions").json()
        if not questions:
            st.info("No research runs yet — ask a question in the first tab.")
        for q in questions:
            with st.container(border=True):
                st.markdown(f"**{q['question_text']}**")
                st.caption(f"Status: {q['status']} · Created: {q['created_at']}")
                if st.button("View details", key=f"view_{q['id']}"):
                    st.session_state["last_question_id"] = q["id"]
                    st.rerun()
    except requests.exceptions.RequestException:
        st.error(f"Could not reach backend at {API_BASE}.")

# ---------------------------------------------------------------------------
# TAB 3 — Manual traceability lookup by finding id
# ---------------------------------------------------------------------------
with tab_trace:
    st.subheader("Look up a finding's full provenance")
    finding_id = st.text_input("Finding ID (copy from the findings list above)")
    if st.button("Trace") and finding_id:
        try:
            trace = requests.get(f"{API_BASE}/findings/{finding_id}/trace")
            if trace.status_code == 404:
                st.error("Finding not found.")
            else:
                data = trace.json()
                st.json(data)
        except requests.exceptions.RequestException:
            st.error(f"Could not reach backend at {API_BASE}.")
