"""Minimal structured logging without document content or personal data."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from skillmap.config.settings import get_settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        event = getattr(record, "event", None)
        if isinstance(event, dict):
            payload.update(event)
        return json.dumps(payload, separators=(",", ":"), default=str)


def configure_logging() -> None:
    root = logging.getLogger()
    if any(isinstance(handler.formatter, JsonFormatter) for handler in root.handlers):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(get_settings().log_level)


def log_analysis_event(
    logger: logging.Logger,
    *,
    request_id: str,
    operation: str,
    outcome: str,
    duration_ms: int,
    parser_type: str = "",
    scoring_mode: str = "",
    model_version: str = "",
    file_size: int | None = None,
    error_category: str = "",
) -> None:
    """Log only the allowlisted operational metadata in this signature."""

    logger.info(
        "analysis_request",
        extra={
            "event": {
                "request_id": request_id,
                "operation": operation,
                "outcome": outcome,
                "duration_ms": duration_ms,
                "parser_type": parser_type,
                "scoring_mode": scoring_mode,
                "model_version": model_version,
                "file_size": file_size,
                "error_category": error_category,
            }
        },
    )
