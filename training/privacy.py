"""Typed PII masking and fail-closed processed-data checks."""

from __future__ import annotations

import re

_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "email",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
        "[EMAIL]",
    ),
    ("url", re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE), "[URL]"),
    (
        "phone",
        re.compile(r"(?<!\w)(?:\+?\d(?:[ ().-]*\d){8,14})(?!\w)"),
        "[PHONE]",
    ),
    (
        "government_id",
        re.compile(
            r"(?im)^\s*(?:passport|aadhaar|aadhar|ssn|social security|government id)\s*[:#-]\s*\S+.*$"
        ),
        "[GOVERNMENT_ID]",
    ),
    (
        "date_of_birth",
        re.compile(r"(?im)^\s*(?:date of birth|dob|born)\s*[:#-]\s*[^\n]+$"),
        "[DATE_OF_BIRTH]",
    ),
    (
        "name",
        re.compile(r"(?im)^\s*(?:full\s+)?name\s*[:#-]\s*[^\n]{1,100}$"),
        "[NAME]",
    ),
    (
        "address",
        re.compile(r"(?im)^\s*(?:home|street|postal|mailing\s+)?address\s*[:#-]\s*[^\n]+$"),
        "[ADDRESS]",
    ),
    (
        "protected_attribute",
        re.compile(
            r"(?im)^\s*(?:age|gender|sex|nationality|religion|marital status)\s*[:#-]\s*[^\n]+$"
        ),
        "[PROTECTED_ATTRIBUTE]",
    ),
)


def mask_pii(text: str) -> str:
    for _, pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return re.sub(r"[ \t]+", " ", text).strip()


def find_pii(text: str) -> list[str]:
    """Return direct-identifier classes still visible after processing."""

    return [name for name, pattern, _ in _PATTERNS if pattern.search(text)]


def assert_no_pii(text: str) -> None:
    found = find_pii(text)
    if found:
        raise ValueError(f"PII found in processed text: {', '.join(sorted(found))}")
