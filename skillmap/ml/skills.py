"""Compatibility skill extraction backed by the compact runtime taxonomy."""

from __future__ import annotations

from typing import Any

from skillmap.adapters.artifact_repository import load_runtime_assets
from skillmap.domain.taxonomy import extract_taxonomy_skills, flatten_taxonomy


def extract_skill_names(cleaned_text: str, max_skills: int = 15) -> list[str]:
    assets = load_runtime_assets()
    skills = sorted(
        {skill for value in assets.taxonomy.values() for skill in flatten_taxonomy(value)}
    )
    return extract_taxonomy_skills(cleaned_text, skills, limit=max_skills)


def extract_skills(cleaned_text: str, max_skills: int = 15) -> list[dict[str, Any]]:
    names = extract_skill_names(cleaned_text, max_skills=max_skills)
    lowered = cleaned_text.lower()
    frequencies = {name: lowered.count(name) for name in names}
    max_frequency = max(frequencies.values(), default=1)
    return [
        {
            "name": name,
            "confidence": round(frequencies[name] / max_frequency, 4),
            "frequency": frequencies[name],
        }
        for name in names
    ]
