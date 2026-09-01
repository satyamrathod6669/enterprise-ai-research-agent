"""
Relational schema for the research knowledge base.

Design intent (per challenge brief): every conclusion must be TRACEABLE back to
findings, and every finding traceable back to a source. Nothing is hard-coded;
the same tables serve every research question the system ever runs, which is
what makes the knowledge base "reusable" rather than a one-off demo script.
"""
import datetime as dt
import enum
import uuid

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Enum, Float, Boolean
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class SourceType(str, enum.Enum):
    NEWS = "news"
    VENDOR = "vendor"
    RESEARCH_PAPER = "research_paper"
    INDUSTRY_REPORT = "industry_report"
    COMPANY_BLOG = "company_blog"
    GENERAL_WEB = "general_web"
    UNKNOWN = "unknown"


class FindingClassification(str, enum.Enum):
    TECHNOLOGY_TREND = "technology_trend"
    BUSINESS_IMPACT = "business_impact"
    RISK = "risk"
    CASE_STUDY = "case_study"
    STATISTIC = "statistic"
    OPINION = "opinion"
    OTHER = "other"


class ResearchQuestion(Base):
    __tablename__ = "research_questions"

    id = Column(String, primary_key=True, default=gen_id)
    question_text = Column(Text, nullable=False)
    normalized_topic = Column(String, index=True)  # used to link related questions
    status = Column(String, default="pending")  # pending|running|completed|failed
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    sources = relationship("Source", back_populates="question", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="question", cascade="all, delete-orphan")
    conclusions = relationship("Conclusion", back_populates="question", cascade="all, delete-orphan")
    contradictions = relationship("Contradiction", back_populates="question", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"

    id = Column(String, primary_key=True, default=gen_id)
    question_id = Column(String, ForeignKey("research_questions.id"))
    url = Column(String, nullable=False)
    title = Column(String)
    raw_content = Column(Text)  # cleaned text/markdown collected from the source
    source_type = Column(Enum(SourceType), default=SourceType.UNKNOWN)
    retrieved_at = Column(DateTime, default=dt.datetime.utcnow)
    search_rank = Column(Float, default=0.0)  # relevance score returned by search provider

    question = relationship("ResearchQuestion", back_populates="sources")
    findings = relationship("Finding", back_populates="source")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String, primary_key=True, default=gen_id)
    question_id = Column(String, ForeignKey("research_questions.id"))
    source_id = Column(String, ForeignKey("sources.id"))
    statement = Column(Text, nullable=False)  # extracted, atomic factual claim
    classification = Column(Enum(FindingClassification), default=FindingClassification.OTHER)
    confidence = Column(Float, default=0.5)  # LLM self-reported extraction confidence
    embedding_id = Column(String, nullable=True)  # id in vector store, for semantic reuse
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    question = relationship("ResearchQuestion", back_populates="findings")
    source = relationship("Source", back_populates="findings")


class Contradiction(Base):
    __tablename__ = "contradictions"

    id = Column(String, primary_key=True, default=gen_id)
    question_id = Column(String, ForeignKey("research_questions.id"))
    finding_a_id = Column(String, ForeignKey("findings.id"))
    finding_b_id = Column(String, ForeignKey("findings.id"))
    explanation = Column(Text)  # why the LLM judged these as contradictory
    severity = Column(String, default="minor")  # minor|moderate|major
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    question = relationship("ResearchQuestion", back_populates="contradictions")


class Conclusion(Base):
    __tablename__ = "conclusions"

    id = Column(String, primary_key=True, default=gen_id)
    question_id = Column(String, ForeignKey("research_questions.id"))
    summary = Column(Text, nullable=False)
    supporting_finding_ids = Column(Text)  # comma-separated Finding ids (traceability)
    caveat = Column(Text, nullable=True)  # e.g. notes about contradictions/low confidence
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    question = relationship("ResearchQuestion", back_populates="conclusions")
