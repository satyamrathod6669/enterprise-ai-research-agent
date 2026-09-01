"""
The research pipeline orchestrator. Implements exactly the flow required by
the challenge brief:

  Define Research Questions -> Search Sources -> Collect Information ->
  Store Sources -> Extract Findings -> Compare Evidence -> Classify Findings ->
  Detect Contradictions -> Generate Conclusions -> Maintain Traceability

Every stage writes to the relational DB immediately (not just at the end), so
a partially-completed run still leaves useful, inspectable data behind, and a
crash mid-pipeline doesn't destroy prior work.
"""
import itertools
import logging

from sqlalchemy.orm import Session

from app.models import ResearchQuestion, Source, Finding, Contradiction, Conclusion
from app.llm.factory import get_llm_client
from app.search.factory import get_search_client
from app.vectorstore import chroma_store
from app.pipeline import steps
from app import config

logger = logging.getLogger("pipeline")


def run_research_pipeline(db: Session, question_id: str) -> ResearchQuestion:
    rq = db.query(ResearchQuestion).filter(ResearchQuestion.id == question_id).first()
    if rq is None:
        raise ValueError(f"ResearchQuestion {question_id} not found")

    rq.status = "running"
    db.commit()

    llm = get_llm_client()
    search = get_search_client()

    # --- Step: Search Sources + Collect Information ------------------------
    results = search.search(rq.question_text, max_results=config.MAX_SOURCES_PER_QUESTION)
    logger.info("Found %d raw search results for question %s", len(results), question_id)

    # --- Step: Store Sources -------------------------------------------------
    stored_sources = []
    for r in results:
        if not r.content or not r.url:
            continue
        source_type = steps.classify_source_type(llm, r.url, r.title)
        src = Source(
            question_id=rq.id,
            url=r.url,
            title=r.title,
            raw_content=r.content,
            source_type=source_type,
            search_rank=r.score,
        )
        db.add(src)
        stored_sources.append(src)
    db.commit()

    # --- Step: Extract Findings (per source) + Classify Findings -----------
    all_findings = []
    for src in stored_sources:
        extracted = steps.extract_findings(llm, rq.question_text, src.raw_content, src.title or "")
        for item in extracted:
            finding = Finding(
                question_id=rq.id,
                source_id=src.id,
                statement=item["statement"],
                classification=item["classification"],
                confidence=item["confidence"],
            )
            db.add(finding)
            db.flush()  # get finding.id without full commit
            try:
                chroma_store.add_finding(
                    finding.id,
                    finding.statement,
                    metadata={"question_id": rq.id, "source_id": src.id, "classification": item["classification"]},
                )
                finding.embedding_id = finding.id
            except Exception as e:
                logger.warning("Vector store write failed (continuing without it): %s", e)
            all_findings.append(finding)
    db.commit()
    logger.info("Extracted %d findings for question %s", len(all_findings), question_id)

    # --- Step: Compare Evidence + Detect Contradictions ---------------------
    # Compare pairs of findings that are semantically similar (candidate
    # conflicts), rather than a brute-force O(n^2) LLM comparison of everything.
    contradiction_summaries = []
    checked_pairs = set()
    for f in all_findings:
        if not f.embedding_id:
            continue
        try:
            similar = chroma_store.find_similar(f.statement, n_results=4, exclude_id=f.id)
        except Exception:
            similar = []
        for s in similar:
            other_id = s["id"]
            pair_key = tuple(sorted([f.id, other_id]))
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)
            other_finding = next((x for x in all_findings if x.id == other_id), None)
            if other_finding is None or s["distance"] > 0.6:  # too dissimilar, skip
                continue
            verdict = steps.detect_contradiction(llm, f.statement, other_finding.statement)
            if verdict:
                c = Contradiction(
                    question_id=rq.id,
                    finding_a_id=f.id,
                    finding_b_id=other_finding.id,
                    explanation=verdict["explanation"],
                    severity=verdict["severity"],
                )
                db.add(c)
                contradiction_summaries.append(
                    f"- {f.statement} [vs] {other_finding.statement}: {verdict['explanation']}"
                )
    db.commit()
    logger.info("Detected %d contradictions for question %s", len(contradiction_summaries), question_id)

    # --- Step: Generate Conclusions (with traceability) ----------------------
    findings_payload = [
        {"id": f.id, "statement": f.statement, "classification": f.classification.value
         if hasattr(f.classification, "value") else f.classification, "confidence": f.confidence}
        for f in all_findings
    ]
    conclusions = steps.generate_conclusions(
        llm, rq.question_text, findings_payload, "\n".join(contradiction_summaries)
    )
    for c in conclusions:
        supporting = c.get("supporting_finding_ids", [])
        conclusion = Conclusion(
            question_id=rq.id,
            summary=c.get("summary", ""),
            supporting_finding_ids=",".join(supporting) if isinstance(supporting, list) else str(supporting),
            caveat=c.get("caveat"),
        )
        db.add(conclusion)
    db.commit()

    rq.status = "completed"
    import datetime as dt
    rq.completed_at = dt.datetime.utcnow()
    db.commit()
    db.refresh(rq)
    return rq
