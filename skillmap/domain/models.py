"""Validated contracts returned by SkillMap runtime services."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RuntimeManifest(StrictModel):
    model_version: str
    taxonomy_version: str
    generated_at: str
    scoring_modes: list[str]
    artifacts: dict[str, str]


class ParsedDocument(StrictModel):
    filename: str
    file_type: Literal["pdf", "docx", "txt"]
    text: str = Field(min_length=1)
    size_bytes: int = Field(ge=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    page_count: int | None = Field(default=None, ge=1)


class PredictionResult(StrictModel):
    cluster_id: int
    cluster_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    top_skills: list[str]
    similar_profiles: list[dict[str, Any]] = Field(default_factory=list)
    domains: list[dict[str, Any]] = Field(default_factory=list)
    seniority: str
    behavioral_signals: list[str]
    adjacent_roles: list[str]
    evidence: list[str]
    model_version: str
    taxonomy_version: str
    scoring_mode: str


class MatchResult(StrictModel):
    score: float = Field(ge=0.0, le=100.0)
    scoring_mode: Literal["lexical", "semantic"]
    model_version: str
    taxonomy_version: str
    confidence: Literal["low", "medium", "high"]
    matched_skills: list[str]
    missing_skills: list[str]
    score_breakdown: dict[str, float]
    evidence: list[str]


class ClusterSummary(StrictModel):
    id: int
    name: str
    domain_label: str
    resume_count: int = Field(ge=0)
    top_skills: list[str]
    example_roles: list[str]
    avg_confidence: float = Field(ge=0.0, le=1.0)
