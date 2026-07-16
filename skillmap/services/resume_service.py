"""Upload orchestration with bounded reads, timeout, cleanup, and safe logging."""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from typing import Any

from skillmap.adapters.document_parser import DocumentValidationError, parse_document
from skillmap.config.logging import log_analysis_event
from skillmap.config.settings import get_settings
from skillmap.core.exceptions import UserFacingError, new_request_id
from skillmap.domain.models import ParsedDocument

logger = logging.getLogger("skillmap.resume")


async def _close_upload(upload: Any) -> None:
    close = getattr(upload, "close", None)
    if close is None:
        return
    result = close()
    if inspect.isawaitable(result):
        await result


async def _read_bounded(upload: Any, max_bytes: int) -> bytearray:
    buffer = bytearray()
    while True:
        chunk = await upload.read(64 * 1024)
        if not chunk:
            return buffer
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise DocumentValidationError("file_size_limit")


async def parse_upload(upload: Any, *, max_bytes: int | None = None) -> ParsedDocument:
    settings = get_settings()
    limit = max_bytes or settings.max_resume_bytes
    request_id = new_request_id()
    started = time.perf_counter()
    buffer = bytearray()
    file_type = ""
    try:
        buffer = await _read_bounded(upload, limit)
        document = await asyncio.wait_for(
            asyncio.to_thread(
                parse_document,
                buffer,
                getattr(upload, "filename", "") or "upload",
                getattr(upload, "content_type", "") or "application/octet-stream",
                settings,
            ),
            timeout=settings.parser_timeout_seconds,
        )
        file_type = document.file_type
        log_analysis_event(
            logger,
            request_id=request_id,
            operation="document_parse",
            outcome="success",
            duration_ms=round((time.perf_counter() - started) * 1000),
            parser_type=file_type,
            file_size=document.size_bytes,
        )
        return document
    except TimeoutError as exc:
        error = UserFacingError(
            "Document processing timed out. Try a smaller or simpler file.",
            category="parser_timeout",
            request_id=request_id,
        )
        log_analysis_event(
            logger,
            request_id=error.request_id,
            operation="document_parse",
            outcome="failure",
            duration_ms=round((time.perf_counter() - started) * 1000),
            parser_type=file_type,
            file_size=len(buffer),
            error_category=error.category,
        )
        raise error from exc
    except UserFacingError as exc:
        log_analysis_event(
            logger,
            request_id=exc.request_id,
            operation="document_parse",
            outcome="failure",
            duration_ms=round((time.perf_counter() - started) * 1000),
            parser_type=file_type,
            file_size=len(buffer),
            error_category=exc.category,
        )
        raise
    except Exception as exc:
        error = UserFacingError(
            "We could not process this document.",
            category="unexpected_parser_error",
            request_id=request_id,
        )
        log_analysis_event(
            logger,
            request_id=request_id,
            operation="document_parse",
            outcome="failure",
            duration_ms=round((time.perf_counter() - started) * 1000),
            file_size=len(buffer),
            error_category=error.category,
        )
        raise error from exc
    finally:
        for index in range(len(buffer)):
            buffer[index] = 0
        await _close_upload(upload)
