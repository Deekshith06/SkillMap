from __future__ import annotations

import io
import logging

from skillmap.config.logging import JsonFormatter, log_analysis_event


def test_structured_logs_cannot_include_resume_pii() -> None:
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("skillmap.test.safe-logging")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)

    log_analysis_event(
        logger,
        request_id="SM-ABC123",
        operation="resume_analysis",
        outcome="success",
        duration_ms=12,
        parser_type="txt",
        scoring_mode="lexical",
        model_version="test",
        file_size=128,
    )

    event = output.getvalue()
    assert "SM-ABC123" in event
    assert "candidate@example.com" not in event
    assert "+91 9876543210" not in event
    assert "resume_text" not in event
