from typing import Literal
from pydantic import BaseModel


class Stakeholder(BaseModel):
    role: str
    why_affected: str
    impact_level: Literal["high", "medium", "low"]


class Gap(BaseModel):
    topic: str
    why_it_matters: str


class Question(BaseModel):
    question: str
    why_we_ask: str


class StakeholderQuestions(BaseModel):
    stakeholder_role: str
    questions: list[Question]


# Full output (used for the gold example check)
class IntakeAnalysis(BaseModel):
    summary: str
    stakeholders_affected: list[Stakeholder]
    gaps: list[Gap]
    questions: list[StakeholderQuestions]


# The three small jobs
class SummaryOut(BaseModel):
    summary: str


class StakeholdersOut(BaseModel):
    stakeholders_affected: list[Stakeholder]


class GapsQuestionsOut(BaseModel):
    gaps: list[Gap]
    questions: list[StakeholderQuestions]