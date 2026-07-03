from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


AgentStatus = Literal["pending", "running", "done", "error"]


class ResearchRequest(BaseModel):
    question: str = Field(min_length=3, max_length=800)


class ApiKeyRequest(BaseModel):
    api_key: str = Field(min_length=20)


class ConfigStatus(BaseModel):
    has_openai_api_key: bool
    model: str
    search_model: str


class SourceItem(BaseModel):
    title: str
    url: str = ""
    snippet: str
    relevance: str = ""


class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: dict
    output_preview: str


class MessageRecord(BaseModel):
    role: str
    content: str


class AgentStep(BaseModel):
    agent_name: str
    role: str
    status: AgentStatus = "pending"
    input_summary: str = ""
    output_summary: str = ""
    handoff_summary: str = ""
    system_prompt_excerpt: str = ""
    messages: list[MessageRecord] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class ResearchResult(BaseModel):
    search_query: str
    summary: str
    sources: list[SourceItem] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class SourceQualityItem(BaseModel):
    title: str
    url: str = ""
    score: int = Field(ge=1, le=5)
    reason: str


class AnalysisResult(BaseModel):
    key_findings: list[str] = Field(default_factory=list)
    source_quality: list[SourceQualityItem] = Field(default_factory=list)
    risks_or_uncertainties: list[str] = Field(default_factory=list)
    synthesis: str


class WriterResult(BaseModel):
    title: str
    final_answer: str
    cited_sources: list[SourceItem] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class ResearchRun(BaseModel):
    question: str
    final_answer: str
    steps: list[AgentStep]
    research: ResearchResult
    analysis: AnalysisResult
    writer: WriterResult
    model: str
    search_model: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

