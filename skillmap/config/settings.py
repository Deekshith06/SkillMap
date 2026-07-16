"""Typed environment configuration for SkillMap."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Settings(BaseModel):
    """Validated settings shared by Reflex, services, and deployment checks."""

    model_config = ConfigDict(frozen=True)

    mode: Literal["lite", "full"] = "lite"
    api_url: str = "http://localhost:8000"
    deploy_url: str = "http://localhost:3000"
    cors_allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    max_resume_size_mb: int = Field(default=2, ge=1, le=10)
    max_batch_size_mb: int = Field(default=10, ge=1, le=50)
    max_extracted_text_chars: int = Field(default=100_000, ge=10_000, le=500_000)
    max_pdf_pages: int = Field(default=20, ge=1, le=100)
    parser_timeout_seconds: float = Field(default=10.0, ge=1.0, le=60.0)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    artifact_dir: Path = Path("models/runtime")
    full_model_path: Path = Path("models/full/all-MiniLM-L6-v2")

    @field_validator("api_url", "deploy_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        value = value.rstrip("/")
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("must be an absolute HTTP(S) URL")
        return value

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_origins(cls, origins: tuple[str, ...]) -> tuple[str, ...]:
        if not origins:
            raise ValueError("at least one CORS origin is required")
        for origin in origins:
            if origin == "*":
                raise ValueError("wildcard CORS origins are not allowed")
            parsed = urlsplit(origin)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError(f"invalid CORS origin: {origin}")
            if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
                raise ValueError(f"CORS origin must not contain a path: {origin}")
        return origins

    @property
    def max_resume_bytes(self) -> int:
        return self.max_resume_size_mb * 1024 * 1024

    @property
    def max_batch_bytes(self) -> int:
        return self.max_batch_size_mb * 1024 * 1024

    @classmethod
    def from_env(cls) -> Settings:
        origins = tuple(
            origin.strip().rstrip("/")
            for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
            if origin.strip()
        )
        return cls.model_validate(
            {
                "mode": os.getenv("SKILLMAP_MODE", "lite").strip().lower(),
                "api_url": os.getenv("API_URL", "http://localhost:8000"),
                "deploy_url": os.getenv("DEPLOY_URL", "http://localhost:3000"),
                "cors_allowed_origins": origins,
                "max_resume_size_mb": os.getenv("MAX_RESUME_SIZE_MB", "2"),
                "max_batch_size_mb": os.getenv("MAX_BATCH_SIZE_MB", "10"),
                "max_extracted_text_chars": os.getenv("MAX_EXTRACTED_TEXT_CHARS", "100000"),
                "max_pdf_pages": os.getenv("MAX_PDF_PAGES", "20"),
                "parser_timeout_seconds": os.getenv("PARSER_TIMEOUT_SECONDS", "10"),
                "log_level": os.getenv("LOG_LEVEL", "INFO").strip().upper(),
                "artifact_dir": Path(os.getenv("SKILLMAP_ARTIFACT_DIR", "models/runtime")),
                "full_model_path": Path(
                    os.getenv(
                        "SKILLMAP_FULL_MODEL_PATH",
                        "models/full/all-MiniLM-L6-v2",
                    )
                ),
            }
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
