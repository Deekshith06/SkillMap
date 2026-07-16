"""Taxonomy flattening and exact skill evidence extraction."""

from __future__ import annotations

import re
from collections.abc import Iterable


def flatten_taxonomy(node: object) -> list[str]:
    values: list[str] = []
    if isinstance(node, dict):
        for value in node.values():
            values.extend(flatten_taxonomy(value))
    elif isinstance(node, list):
        for value in node:
            values.extend(flatten_taxonomy(value))
    elif isinstance(node, str):
        values.append(node.strip().lower())
    return values


def domain_label(key: str) -> str:
    replacements = {
        "CSE": "CSE",
        "ECE": "ECE",
        "EEE": "EEE",
        "MLOps": "MLOps",
        "DevOps": "DevOps",
        "GRC": "GRC",
        "UX": "UX",
        "HR": "HR",
    }
    parts = key.replace("_", " ").split()
    return " ".join(replacements.get(part, part.title()) for part in parts)


def normalize_for_matching(text: str) -> str:
    text = text.lower().replace("\u00a0", " ")
    text = re.sub(r"[^a-z0-9+#./&-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _contains(text: str, phrase: str) -> bool:
    escaped = re.escape(phrase).replace(r"\ ", r"\s+")
    return bool(re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text))


def extract_taxonomy_skills(text: str, skills: Iterable[str], limit: int = 30) -> list[str]:
    normalized = normalize_for_matching(text)
    unique = sorted(
        {skill.strip().lower() for skill in skills if skill.strip()},
        key=lambda item: (-len(item), item),
    )
    found: list[str] = []
    for skill in unique:
        if _contains(normalized, skill):
            found.append(skill)
            if len(found) >= limit:
                break
    return found


def redact_pii(text: str) -> str:
    """Mask common direct identifiers and labelled protected attributes."""

    text = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", " [EMAIL] ", text)
    text = re.sub(
        r"(?<!\w)(?:\+?\d(?:[().\s-]*\d){8,14})(?!\w)",
        " [PHONE] ",
        text,
    )
    text = re.sub(r"https?://\S+|www\.\S+", " [URL] ", text, flags=re.IGNORECASE)
    labelled = (
        (r"(?:full\s+)?name", "[NAME]"),
        (r"(?:home|street|postal|mailing\s+)?address", "[ADDRESS]"),
        (r"(?:date of birth|dob|born)", "[DATE_OF_BIRTH]"),
        (r"(?:age|gender|sex|nationality|religion|marital status)", "[PROTECTED_ATTRIBUTE]"),
        (r"(?:passport|aadhaar|aadhar|ssn|social security|government id)", "[GOVERNMENT_ID]"),
    )
    for label, replacement in labelled:
        text = re.sub(rf"(?im)^\s*{label}\s*[:#-]\s*[^\n]+$", replacement, text)
    return re.sub(r"\s+", " ", text).strip()
