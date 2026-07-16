"""Explainable, normalized resume-to-job scoring."""

from __future__ import annotations

import math
import re
from typing import Any, Literal, Protocol

from rank_bm25 import BM25Okapi
from sklearn.metrics.pairwise import cosine_similarity

from skillmap.domain.models import MatchResult
from skillmap.domain.taxonomy import extract_taxonomy_skills, normalize_for_matching, redact_pii

_TOKEN_RE = re.compile(r"[a-z0-9+#.]{2,}")
_YEARS_RE = re.compile(
    r"\b(\d{1,2})(?:\s*[-\u2013]\s*\d{1,2})?\+?\s+years?\b",
    re.IGNORECASE,
)


class Vectorizer(Protocol):
    def transform(self, raw_documents: list[str]) -> Any: ...


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(normalize_for_matching(text))


def _years(text: str) -> int | None:
    values = [int(match) for match in _YEARS_RE.findall(text)]
    return max(values) if values else None


def _bm25_similarity(resume_text: str, job_text: str) -> float:
    corpus = [_tokens(part) for part in re.split(r"(?<=[.!?])\s+|\n+", resume_text)]
    corpus = [tokens for tokens in corpus if tokens]
    query = _tokens(job_text)
    if not corpus or not query:
        return 0.0
    scores = BM25Okapi(corpus).get_scores(query)
    positive = sorted((max(0.0, float(score)) for score in scores), reverse=True)[:3]
    raw_score = sum(positive)
    return raw_score / (raw_score + max(1.0, math.sqrt(len(set(query)))))


def _tfidf_similarity(vectorizer: Vectorizer, resume_text: str, job_text: str) -> float:
    matrix = vectorizer.transform([resume_text, job_text])
    return max(0.0, min(1.0, float(cosine_similarity(matrix[0], matrix[1])[0][0])))


def _weighted_score(components: dict[str, tuple[float | None, float]]) -> float:
    weight_total = 0.0
    weighted_total = 0.0
    for value, weight in components.values():
        if value is None:
            continue
        weight_total += weight
        weighted_total += value * weight
    if weight_total == 0:
        return 0.0
    return weighted_total / weight_total


def score_match(
    resume_text: str,
    job_text: str,
    *,
    all_skills: list[str],
    vectorizer: Vectorizer,
    model_version: str,
    taxonomy_version: str,
    semantic_similarity: float | None = None,
    role_alignment: float | None = None,
) -> MatchResult:
    resume_text = redact_pii(resume_text)
    job_text = redact_pii(job_text)
    required = extract_taxonomy_skills(job_text, all_skills, limit=50)
    resume_skills = set(extract_taxonomy_skills(resume_text, all_skills, limit=100))
    matched = [skill for skill in required if skill in resume_skills]
    missing = [skill for skill in required if skill not in resume_skills]
    skill_overlap = len(matched) / len(required) if required else None

    tfidf = _tfidf_similarity(vectorizer, resume_text, job_text)
    bm25 = _bm25_similarity(resume_text, job_text)
    lexical = (tfidf + bm25) / 2

    required_years = _years(job_text)
    resume_years = _years(resume_text)
    experience = None
    if required_years is not None:
        experience = min(1.0, (resume_years or 0) / max(required_years, 1))

    if semantic_similarity is None:
        mode: Literal["lexical", "semantic"] = "lexical"
        components = {
            "skill_overlap": (skill_overlap, 0.65),
            "lexical_similarity": (lexical, 0.25),
            "experience_alignment": (experience, 0.10),
        }
    else:
        mode = "semantic"
        components = {
            "semantic_similarity": (semantic_similarity, 0.45),
            "skill_overlap": (skill_overlap, 0.35),
            "experience_alignment": (experience, 0.15),
            "role_alignment": (role_alignment, 0.05),
        }

    score = round(max(0.0, min(1.0, _weighted_score(components))) * 100, 1)
    word_count = len(_tokens(job_text))
    if len(required) >= 5 and word_count >= 100:
        confidence: Literal["low", "medium", "high"] = "high"
    elif len(required) >= 2 and word_count >= 40:
        confidence = "medium"
    else:
        confidence = "low"

    evidence = [
        f"{len(matched)} of {len(required)} taxonomy skills matched."
        if required
        else "No taxonomy skills were explicit; the score uses lexical evidence only.",
        f"TF-IDF similarity: {tfidf * 100:.1f}%.",
        f"BM25 similarity: {bm25 * 100:.1f}%.",
    ]
    if required_years is not None:
        evidence.append(
            f"Experience evidence: {resume_years or 0} years found against {required_years} required."
        )

    breakdown = {
        name: round(float(value) * 100, 1)
        for name, (value, _) in components.items()
        if value is not None
    }
    breakdown["tfidf_similarity"] = round(tfidf * 100, 1)
    breakdown["bm25_similarity"] = round(bm25 * 100, 1)
    return MatchResult(
        score=score,
        scoring_mode=mode,
        model_version=model_version,
        taxonomy_version=taxonomy_version,
        confidence=confidence,
        matched_skills=matched,
        missing_skills=missing,
        score_breakdown=breakdown,
        evidence=evidence,
    )
