"""
core/exceptions.py — Custom exception hierarchy for SkillMap.

Hierarchy:
  SkillMapError (base)
  ├── IngestionError
  │   ├── UnsupportedFileTypeError
  │   └── FileTooLargeError
  ├── ScoringError
  │   └── EmptyResumeError
  ├── ClusteringError
  │   ├── InsufficientDataError
  │   └── ModelNotFoundError
  └── DatasetError
      ├── MinimumCountError
      └── SchemaValidationError
"""

from __future__ import annotations

import secrets


class SkillMapError(Exception):
    """Base exception for all SkillMap errors."""


def new_request_id() -> str:
    return f"SM-{secrets.token_hex(3).upper()}"


class UserFacingError(SkillMapError):
    """An internal failure with a stable, non-sensitive public message."""

    def __init__(
        self,
        public_message: str,
        *,
        category: str,
        request_id: str | None = None,
    ) -> None:
        self.request_id = request_id or new_request_id()
        self.category = category
        self.public_message = f"{public_message} Reference: {self.request_id}"
        super().__init__(self.public_message)


class ArtifactUnavailableError(UserFacingError):
    def __init__(self, detail: str = "") -> None:
        self.detail = detail
        super().__init__(
            "The SkillMap analysis engine is not ready. Try again shortly.",
            category="runtime_artifact_unavailable",
        )


class FullModeUnavailableError(UserFacingError):
    def __init__(self) -> None:
        super().__init__(
            "Full ML mode is not installed. Install the optional ML dependencies or use lite mode.",
            category="full_mode_unavailable",
        )


# ── Ingestion ─────────────────────────────────────────────────────────────────


class IngestionError(SkillMapError):
    """Raised when file ingestion or parsing fails."""


class UnsupportedFileTypeError(IngestionError):
    """Raised when an unsupported file extension or MIME type is uploaded."""

    def __init__(self, filename: str, mime: str = "") -> None:
        detail = f"Unsupported file: '{filename}'"
        if mime:
            detail += f" (MIME: {mime})"
        super().__init__(detail)
        self.filename = filename
        self.mime = mime


class FileTooLargeError(IngestionError):
    """Raised when uploaded file exceeds the size limit."""

    def __init__(self, size_bytes: int, max_bytes: int) -> None:
        super().__init__(f"File too large: {size_bytes:,} bytes (max {max_bytes:,} bytes)")
        self.size_bytes = size_bytes
        self.max_bytes = max_bytes


# ── Scoring ───────────────────────────────────────────────────────────────────


class ScoringError(SkillMapError):
    """Raised when ATS scoring fails."""


class EmptyResumeError(ScoringError):
    """Raised when resume text is empty or too short to score."""

    def __init__(self, min_chars: int = 10) -> None:
        super().__init__(f"Resume text is empty or too short (minimum {min_chars} characters).")


# ── Clustering ────────────────────────────────────────────────────────────────


class ClusteringError(SkillMapError):
    """Raised when clustering pipeline fails."""


class InsufficientDataError(ClusteringError):
    """Raised when there are not enough resumes to cluster meaningfully."""

    def __init__(self, n: int, min_required: int) -> None:
        super().__init__(
            f"Only {n} resumes available; clustering requires at least {min_required}."
        )
        self.n = n
        self.min_required = min_required


class ModelNotFoundError(ClusteringError):
    """Raised when a required model artifact file is missing."""

    def __init__(self, path: str) -> None:
        super().__init__(
            f"Model file not found: '{path}'. "
            "Run `python pipeline/training_dag.py --stage all` to train."
        )
        self.path = path


# ── Dataset ───────────────────────────────────────────────────────────────────


class DatasetError(SkillMapError):
    """Raised when dataset validation fails."""


class MinimumCountError(DatasetError):
    """Raised when a domain/sub-domain has fewer resumes than the minimum."""

    def __init__(self, violations: list[str]) -> None:
        detail = "Dataset minimum count violations:\n" + "\n".join(f"  • {v}" for v in violations)
        super().__init__(detail)
        self.violations = violations


class SchemaValidationError(DatasetError):
    """Raised when a resume record fails Pydantic schema validation."""

    def __init__(self, record_id: str, errors: list) -> None:
        super().__init__(f"Schema validation failed for record '{record_id}': {errors}")
        self.record_id = record_id
        self.errors = errors
