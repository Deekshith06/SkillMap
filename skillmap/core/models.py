"""
core/models.py — Canonical dataclasses for the SkillMap platform.

All data flowing through the system is typed via these dataclasses:
  ResumeDocument → ATSReport (via ATSEngine)
  ResumeDocument → SkillProfile (via SkillEngine)
  list[SkillProfile] → ClusterMap (via SkillEngine.cluster_candidates)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Input Models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ResumeDocument:
    """Parsed and normalised resume ready for downstream ML."""
    raw_text: str
    cleaned_text: str
    filename: str
    file_format: str  # "pdf" | "docx" | "txt"

    resume_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sections: dict[str, str] = field(default_factory=dict)
    contact: dict[str, str] = field(default_factory=dict)
    word_count: int = 0
    char_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    embedding: Optional[list[float]] = None  # 384-dim, populated by embedder

    def __post_init__(self) -> None:
        if not self.raw_text or not self.raw_text.strip():
            raise ValueError("ResumeDocument.raw_text cannot be empty")
        if self.file_format not in {"pdf", "docx", "txt"}:
            raise ValueError(
                f"Unsupported file_format '{self.file_format}'. Expected pdf/docx/txt."
            )
        self.word_count = len(self.cleaned_text.split())
        self.char_count = len(self.cleaned_text)


@dataclass
class JobDescription:
    """Parsed job description for ATS scoring and matching."""
    raw_text: str
    cleaned_text: str

    jd_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    keywords: list[str] = field(default_factory=list)   # KeyBERT extracted
    embedding: Optional[list[float]] = None

    def __post_init__(self) -> None:
        if not self.raw_text or not self.raw_text.strip():
            raise ValueError("JobDescription.raw_text cannot be empty")


# ─────────────────────────────────────────────────────────────────────────────
# Output Models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ATSReport:
    """Full ATS scoring result with per-category breakdown and suggestions."""
    resume_id: str
    total_score: int          # 0–100
    grade: str                # "Excellent" | "Good" | "Needs Work"
    categories: dict[str, dict]
    suggestions: list[dict]  # priority-sorted: critical > important > nice
    matched_keywords: list[str]
    missing_keywords: list[str]
    domains: list[dict]       # [{domain, confidence, matchedCount, topMatches}]

    jd_id: Optional[str] = None
    match_score: Optional[float] = None  # cosine sim × 100 (0–100)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if not (0 <= self.total_score <= 100):
            raise ValueError(
                f"ATSReport.total_score must be 0–100, got {self.total_score}"
            )
        valid_grades = {"Excellent", "Good", "Needs Work"}
        if self.grade not in valid_grades:
            raise ValueError(
                f"ATSReport.grade must be one of {valid_grades}, got '{self.grade}'"
            )

    @property
    def passed_ats(self) -> bool:
        """Heuristic: score ≥ 60 is likely to pass most ATS filters."""
        return self.total_score >= 60

    def to_dict(self) -> dict:
        return {
            "resume_id": self.resume_id,
            "total_score": self.total_score,
            "grade": self.grade,
            "passed_ats": self.passed_ats,
            "categories": self.categories,
            "suggestions": self.suggestions,
            "matched_keywords": self.matched_keywords,
            "missing_keywords": self.missing_keywords,
            "domains": self.domains,
            "jd_id": self.jd_id,
            "match_score": self.match_score,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class SkillProfile:
    """Extracted skill signals + embedding for a single candidate."""
    resume_id: str
    skills: list[dict]         # [{name, confidence, frequency}]
    skill_names: list[str]     # flat list for fast membership checks
    embedding: list[float]     # 384-dim normalised vector

    cluster_id: Optional[int] = None
    cluster_label: Optional[str] = None
    cluster_confidence: float = 0.0
    umap_x: Optional[float] = None   # 2D coords from UMAP for scatter viz
    umap_y: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.embedding:
            raise ValueError("SkillProfile.embedding cannot be empty")
        if not (0.0 <= self.cluster_confidence <= 1.0):
            raise ValueError(
                f"cluster_confidence must be 0–1, got {self.cluster_confidence}"
            )


@dataclass
class ClusterMap:
    """Result of clustering a corpus of SkillProfiles."""
    n_clusters: int
    clusters: list[dict]   # [{id, label, size, top_skills, center_skills}]
    noise_count: int       # HDBSCAN outliers (label == -1)
    silhouette_score: float
    umap_points: list[dict]  # [{resume_id, x, y, cluster_id, cluster_label}]
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if self.n_clusters < 0:
            raise ValueError("n_clusters cannot be negative")
        if not (-1.0 <= self.silhouette_score <= 1.0):
            raise ValueError(
                f"silhouette_score must be in [-1, 1], got {self.silhouette_score}"
            )

    @property
    def noise_ratio(self) -> float:
        total = sum(c.get("size", 0) for c in self.clusters) + self.noise_count
        return self.noise_count / total if total > 0 else 0.0

    def cluster_by_id(self, cid: int) -> Optional[dict]:
        return next((c for c in self.clusters if c.get("id") == cid), None)

    def to_dict(self) -> dict:
        return {
            "n_clusters": self.n_clusters,
            "clusters": self.clusters,
            "noise_count": self.noise_count,
            "noise_ratio": round(self.noise_ratio, 4),
            "silhouette_score": round(self.silhouette_score, 4),
            "umap_points": self.umap_points,
            "generated_at": self.generated_at.isoformat(),
        }
