"""Canonical data contracts shared by preparation, training, and evaluation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EntityCategory = Literal[
    "SKILL",
    "HARD_SKILL",
    "SOFT_SKILL",
    "KNOWLEDGE",
    "TOOL",
    "PROGRAMMING_LANGUAGE",
    "FRAMEWORK",
    "DATABASE",
    "CLOUD_PLATFORM",
    "CERTIFICATION",
    "DEGREE",
    "FIELD_OF_STUDY",
    "OCCUPATION",
    "EXPERIENCE_DURATION",
    "SENIORITY",
    "RESPONSIBILITY",
    "ACHIEVEMENT",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Entity(StrictModel):
    text: str = Field(min_length=1)
    normalized_name: str | None = None
    taxonomy: str | None = None
    taxonomy_id: str | None = None
    category: EntityCategory
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence: str | None = None
    mapping_method: str | None = None

    @model_validator(mode="after")
    def offsets_are_valid(self) -> Entity:
        if self.end <= self.start:
            raise ValueError("entity end must be greater than start")
        return self


class CanonicalDocument(StrictModel):
    document_id: str
    document_type: Literal["resume", "job", "sentence"]
    language: str = "en"
    text: str = Field(min_length=1)
    sections: list[dict] = Field(default_factory=list)
    skills: list[Entity] = Field(default_factory=list)
    knowledge: list[Entity] = Field(default_factory=list)
    occupations: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    experience: list[dict] = Field(default_factory=list)
    certifications: list[dict] = Field(default_factory=list)
    seniority: str | None = None
    source_dataset: str
    official_split: Literal["train", "validation", "test"] | None = None
    family_id: str | None = None
    synthetic: bool = False

    @model_validator(mode="after")
    def spans_match_text(self) -> CanonicalDocument:
        for entity in [*self.skills, *self.knowledge]:
            if self.text[entity.start : entity.end] != entity.text:
                raise ValueError(f"span does not match text for {entity.text!r}")
        return self


class MatchPair(StrictModel):
    pair_id: str
    resume_id: str
    job_id: str
    group_id: str
    occupation: str
    resume_text: str
    job_text: str
    component_labels: dict[str, float]
    final_score: float = Field(ge=0, le=100)
    label: Literal["STRONG_MATCH", "POTENTIAL_MATCH", "WEAK_MATCH", "NOT_MATCH"]
    evidence: list[str]
    label_generation_method: str
    confidence: Literal["low", "medium", "high"]
    taxonomy_concepts: list[str]
    synthetic: bool
    hard_negative: bool = False


def bio_spans(
    tokens: list[str], tags: list[str], category: EntityCategory
) -> tuple[str, list[Entity]]:
    """Reconstruct non-overlapping character spans from BIO tags."""

    if len(tokens) != len(tags):
        raise ValueError("token and tag lengths differ")
    text = " ".join(tokens)
    offsets: list[tuple[int, int]] = []
    cursor = 0
    for token in tokens:
        offsets.append((cursor, cursor + len(token)))
        cursor += len(token) + 1
    spans: list[Entity] = []
    start_index: int | None = None
    for index, tag in enumerate([*tags, "O"]):
        prefix = tag.split("-", 1)[0]
        if prefix == "B" or (prefix == "I" and start_index is None):
            if start_index is not None:
                start, end = offsets[start_index][0], offsets[index - 1][1]
                spans.append(Entity(text=text[start:end], category=category, start=start, end=end))
            start_index = index
        elif prefix == "O" and start_index is not None:
            start, end = offsets[start_index][0], offsets[index - 1][1]
            spans.append(Entity(text=text[start:end], category=category, start=start, end=end))
            start_index = None
    return text, spans
