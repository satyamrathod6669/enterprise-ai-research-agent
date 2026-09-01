import datetime as dt
from typing import Optional
from pydantic import BaseModel


class QuestionCreate(BaseModel):
    question_text: str


class SourceOut(BaseModel):
    id: str
    url: str
    title: Optional[str]
    source_type: str
    search_rank: float

    class Config:
        from_attributes = True


class FindingOut(BaseModel):
    id: str
    source_id: str
    statement: str
    classification: str
    confidence: float

    class Config:
        from_attributes = True


class ContradictionOut(BaseModel):
    id: str
    finding_a_id: str
    finding_b_id: str
    explanation: str
    severity: str

    class Config:
        from_attributes = True


class ConclusionOut(BaseModel):
    id: str
    summary: str
    supporting_finding_ids: str
    caveat: Optional[str]

    class Config:
        from_attributes = True


class QuestionOut(BaseModel):
    id: str
    question_text: str
    status: str
    created_at: dt.datetime
    completed_at: Optional[dt.datetime]

    class Config:
        from_attributes = True


class QuestionDetailOut(QuestionOut):
    sources: list[SourceOut] = []
    findings: list[FindingOut] = []
    contradictions: list[ContradictionOut] = []
    conclusions: list[ConclusionOut] = []
