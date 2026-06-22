from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


TaskStatus = Literal["created", "running", "completed", "failed"]


class ResearchTaskCreate(BaseModel):
    topic: str = Field(min_length=2, max_length=300)
    language: Literal["zh", "en"] = "zh"
    max_papers: int = Field(default=8, ge=3, le=20)


class AgentLog(BaseModel):
    id: int
    agent: str
    status: str
    message: str
    payload: dict[str, Any] | None = None
    created_at: str


class Paper(BaseModel):
    id: int | None = None
    title: str
    authors: list[str] = []
    year: int | None = None
    source: str
    abstract: str
    url: str | None = None
    relevance: float = 0.0
    summary: str | None = None


class Evaluation(BaseModel):
    relevance: float
    citation: float
    structure: float
    faithfulness: float
    overall: float
    suggestions: list[str]


class ResearchTask(BaseModel):
    task_id: str
    topic: str
    language: Literal["zh", "en"]
    max_papers: int
    status: TaskStatus
    current_step: str
    progress: int
    created_at: str
    updated_at: str
    report_path: str | None = None
    error: str | None = None
    agent_logs: list[AgentLog] = []
    papers: list[Paper] = []
    evaluation: Evaluation | None = None


class ResearchTaskCreated(BaseModel):
    task_id: str
    status: TaskStatus


class ResearchTaskDeleted(BaseModel):
    task_id: str
    deleted: bool


class ReportResponse(BaseModel):
    task_id: str
    format: Literal["markdown"]
    content: str


class ChatRequest(BaseModel):
    task_id: str
    question: str = Field(min_length=2, max_length=500)


class ChatSource(BaseModel):
    title: str
    url: str | None = None
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
