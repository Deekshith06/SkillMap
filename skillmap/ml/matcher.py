"""
matcher.py — Resume ↔ JD matching and skill-gap utilities.
Relocated from backend/matcher.py with updated imports.
"""
from __future__ import annotations

import re
from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from skillmap.ml.extractors import clean_text
from skillmap.ml.skills import extract_skill_names

_WS_RE = re.compile(r"\s+")
_PUNCT_SPLIT_RE = re.compile(r"[,\n;/|•·]+")


def _normalise_phrase(s: str) -> str:
    return _WS_RE.sub(" ", s.lower().strip())


def embed_text(sentence_model: Any, text: str) -> np.ndarray:
    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("Text is empty after cleaning.")
    emb = sentence_model.encode(
        [cleaned],
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )[0]
    return np.asarray(emb, dtype=np.float32)


def compute_match_score(resume_embedding: np.ndarray, jd_embedding: np.ndarray) -> float:
    sim = float(
        cosine_similarity(resume_embedding.reshape(1, -1), jd_embedding.reshape(1, -1))[0][0]
    )
    sim = float(np.clip(sim, 0.0, 1.0))
    return round(sim * 100.0, 1)


def _extract_keywords_fallback(text: str, top_n: int) -> list[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []
    skills = extract_skill_names(cleaned, max_skills=min(30, max(10, top_n)))
    phrases: list[str] = []
    for chunk in _PUNCT_SPLIT_RE.split(cleaned):
        chunk = chunk.strip()
        if not chunk:
            continue
        chunk = _normalise_phrase(chunk)
        if 2 <= len(chunk) <= 40:
            phrases.append(chunk)
    out: list[str] = []
    seen: set[str] = set()
    for kw in skills + phrases:
        kw_n = _normalise_phrase(kw)
        if not kw_n or kw_n in seen:
            continue
        seen.add(kw_n)
        out.append(kw_n)
        if len(out) >= top_n:
            break
    return out


_keybert_model: Any | None = None


def _get_keybert() -> Any | None:
    global _keybert_model
    if _keybert_model is not None:
        return _keybert_model
    try:
        from keybert import KeyBERT
    except Exception:
        return None
    _keybert_model = KeyBERT(model="all-MiniLM-L6-v2")
    return _keybert_model


def extract_jd_keywords(jd_text: str, top_n: int = 20) -> list[str]:
    jd_text = str(jd_text or "").strip()
    if not jd_text:
        return []
    kb = _get_keybert()
    if kb is None:
        return _extract_keywords_fallback(jd_text, top_n=top_n)
    keywords = kb.extract_keywords(
        jd_text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        top_n=top_n,
        use_mmr=True,
        diversity=0.5,
    )
    out: list[str] = []
    seen: set[str] = set()
    for kw, _score in keywords:
        kw_n = _normalise_phrase(kw)
        if not kw_n or kw_n in seen:
            continue
        seen.add(kw_n)
        out.append(kw_n)
    return out


def compute_keyword_overlap(resume_text: str, jd_keywords: list[str]) -> dict[str, list[str]]:
    hay = f" {clean_text(resume_text).lower()} "
    matched: list[str] = []
    missing: list[str] = []
    for kw in jd_keywords:
        needle = f" {kw.lower()} "
        if needle.strip() and needle in hay:
            matched.append(kw)
        else:
            if kw.lower() in hay:
                matched.append(kw)
            else:
                missing.append(kw)
    return {"matched": matched, "missing": missing}


def compute_skill_gap(
    resume_text: str,
    jd_keywords: list[str],
    critical_top_n: int = 10,
) -> dict[str, Any]:
    overlap = compute_keyword_overlap(resume_text, jd_keywords)
    missing = overlap["missing"]
    critical_set = set(jd_keywords[:critical_top_n])
    critical = [kw for kw in missing if kw in critical_set]
    important = [kw for kw in missing if kw not in critical_set]
    resume_skills = extract_skill_names(clean_text(resume_text), max_skills=30)
    jd_set = set(jd_keywords)
    bonus = [s for s in resume_skills if _normalise_phrase(s) not in jd_set]
    return {
        "critical": [{"skill": kw, "context": "missing from resume"} for kw in critical],
        "important": [{"skill": kw, "context": "missing from resume"} for kw in important],
        "nice_to_have": [],
        "bonus": bonus[:20],
    }
