"""Compatibility wrappers for the secured document parser."""

from __future__ import annotations

import re
import unicodedata

from skillmap.adapters.document_parser import ALLOWED_TYPES, parse_document
from skillmap.config.settings import get_settings
from skillmap.core.exceptions import UserFacingError

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(\+?\d{1,3}[-.\\s]?)?\(?\d{2,4}\)?[-.\\s]?\d{3,4}[-.\\s]?\d{3,4}")
_HTML_RE = re.compile(r"<[^>]+>")
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
_NON_ASCII_PUNCT_RE = re.compile(r"[^\x00-\x7F\s]")
_MULTI_WS_RE = re.compile(r"\s+")


def extract_pdf(file_bytes: bytes) -> str:
    return parse_document(file_bytes, "upload.pdf", ALLOWED_TYPES[".pdf"]).text


def extract_docx(file_bytes: bytes) -> str:
    return parse_document(file_bytes, "upload.docx", ALLOWED_TYPES[".docx"]).text


def extract_txt(file_bytes: bytes) -> str:
    return parse_document(file_bytes, "upload.txt", ALLOWED_TYPES[".txt"]).text


def clean_text(raw: str) -> str:
    text = unicodedata.normalize("NFKC", raw or "")
    text = _HTML_RE.sub(" ", text)
    text = _CTRL_RE.sub(" ", text)
    text = _EMAIL_RE.sub(" ", text)
    text = _URL_RE.sub(" ", text)
    text = _PHONE_RE.sub(" ", text)
    text = text.lower()
    text = _NON_ASCII_PUNCT_RE.sub(" ", text)
    text = _MULTI_WS_RE.sub(" ", text).strip()
    return text


def sentence_split(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def extract_and_clean(file_bytes: bytes, filename: str) -> str:
    extension = "." + filename.lower().rsplit(".", 1)[-1]
    mime = ALLOWED_TYPES.get(extension, "application/octet-stream")
    return clean_text(parse_document(file_bytes, filename, mime).text)


def validate_upload(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    max_bytes: int = 2 * 1024 * 1024,
) -> str | None:
    settings = get_settings().model_copy(
        update={"max_resume_size_mb": max(1, max_bytes // (1024 * 1024))}
    )
    try:
        parse_document(file_bytes, filename, content_type, settings)
    except UserFacingError as exc:
        return exc.public_message
    return None
