"""
extractors.py — PDF / DOCX / TXT text extraction pipeline.

Each extractor returns cleaned, normalised plain text ready for
downstream embedding and skill extraction. All functions carry
full type hints (Python 3.10+ syntax).

Design decisions
────────────────
• PDF: pdfminer.six (no Tesseract/OCR dependency).
• DOCX: python-docx for structural paragraph access.
• TXT: direct decode with BOM stripping.
• Post-extraction: NFKC normalisation, whitespace collapse,
  PII removal (emails, URLs, phone numbers), lowercase,
  sentence splitting via nltk.
"""

from __future__ import annotations

import io
import re
import unicodedata

import nltk

# ── Lazy download punkt_tab if missing ──────────────────────────
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)

from nltk.tokenize import sent_tokenize
from pdfminer.high_level import extract_text as pdfminer_extract
from docx import Document as DocxDocument


# ── Compiled regex patterns ──────────────────────────────────────

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", re.IGNORECASE)
_PHONE_RE = re.compile(
    r"(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"
)
_HTML_RE = re.compile(r"<[^>]+>")
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
_NON_ASCII_PUNCT_RE = re.compile(r"[^\x00-\x7F\s]")
_MULTI_WS_RE = re.compile(r"\s+")
_BOM = "\ufeff"


# ── Public API ───────────────────────────────────────────────────


def extract_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfminer.six."""
    return pdfminer_extract(io.BytesIO(file_bytes))


def extract_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX bytes using python-docx."""
    doc = DocxDocument(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs)


def extract_txt(file_bytes: bytes) -> str:
    """Decode raw bytes as UTF-8 (strip BOM)."""
    text = file_bytes.decode("utf-8", errors="replace")
    if text.startswith(_BOM):
        text = text[len(_BOM):]
    return text


def clean_text(raw: str) -> str:
    """
    Full cleaning pipeline applied after extraction.

    Steps:
        1. NFKC unicode normalisation
        2. HTML tag removal
        3. Control-character removal
        4. PII removal (email, URL, phone)
        5. Collapse whitespace
        6. Lowercase
        7. Strip non-ASCII punctuation
    """
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
    """Split cleaned text into sentences using NLTK."""
    return sent_tokenize(text) if text else []


def extract_and_clean(file_bytes: bytes, filename: str) -> str:
    """
    One-shot: detect type → extract → clean.
    Raises ValueError for unsupported types.
    """
    lower = filename.lower()
    if lower.endswith(".pdf"):
        raw = extract_pdf(file_bytes)
    elif lower.endswith(".docx"):
        raw = extract_docx(file_bytes)
    elif lower.endswith(".txt"):
        raw = extract_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}")
    return clean_text(raw)


# ── MIME / magic-byte validation ─────────────────────────────────

_ALLOWED_MIME = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}

_MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"%PDF", "pdf"),
    (b"PK\x03\x04", "docx"),  # ZIP (OOXML)
]


def validate_upload(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    max_bytes: int = 5 * 1024 * 1024,
) -> str | None:
    """
    Validate a file upload.  Returns an error string if invalid,
    or None if the file passes all checks.

    Checks:
        • size ≤ max_bytes
        • content_type in allowlist
        • magic-byte signature matches extension
    """
    if len(file_bytes) > max_bytes:
        return f"File too large ({len(file_bytes)} bytes); max is {max_bytes}."

    if content_type not in _ALLOWED_MIME:
        return f"Unsupported MIME type: {content_type}"

    lower = filename.lower()
    if lower.endswith(".pdf"):
        if not file_bytes[:4].startswith(b"%PDF"):
            return "File extension is .pdf but magic bytes do not match."
    elif lower.endswith(".docx"):
        if not file_bytes[:4].startswith(b"PK"):
            return "File extension is .docx but magic bytes do not match."
    elif not lower.endswith(".txt"):
        return f"Unsupported extension: {filename}"

    return None
