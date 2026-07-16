from __future__ import annotations

import pytest
from pydantic import ValidationError

from skillmap.adapters.artifact_repository import load_runtime_assets
from skillmap.domain.models import PredictionResult
from skillmap.domain.scoring import _weighted_score, score_match
from skillmap.domain.taxonomy import extract_taxonomy_skills, flatten_taxonomy
from skillmap.services.analysis_service import analyze_resume, match_job


def _skills() -> list[str]:
    assets = load_runtime_assets()
    return sorted(
        {skill for domain in assets.taxonomy.values() for skill in flatten_taxonomy(domain)}
    )


def test_extracts_supported_skills_without_substring_matches() -> None:
    skills = extract_taxonomy_skills(
        "Python, SQL, and Kubernetes in production.",
        ["Python", "SQL", "Kubernetes", "R"],
    )

    assert skills == ["kubernetes", "python", "sql"]


def test_weighted_score_normalizes_available_components() -> None:
    score = _weighted_score(
        {
            "skill_overlap": (0.8, 0.65),
            "lexical_similarity": (0.4, 0.25),
            "experience_alignment": (None, 0.10),
        }
    )

    assert score == pytest.approx((0.8 * 0.65 + 0.4 * 0.25) / 0.90)


def test_match_score_is_normalized_and_explained() -> None:
    assets = load_runtime_assets()
    result = score_match(
        "Python developer with SQL and 5 years experience.",
        "Python engineer requiring SQL and 4 years experience.",
        all_skills=_skills(),
        vectorizer=assets.vectorizer,
        model_version=assets.manifest.model_version,
        taxonomy_version=assets.manifest.taxonomy_version,
    )

    assert 0 <= result.score <= 100
    assert result.scoring_mode == "lexical"
    assert set(result.matched_skills) >= {"python", "sql"}
    assert result.score_breakdown["skill_overlap"] == 100
    assert result.evidence


def test_no_artificial_fifty_percent_fallback() -> None:
    result = match_job("Accountant with Excel", "Python Kubernetes engineer")

    assert result.score != 50.0
    assert result.evidence


def test_no_score_when_job_has_no_supported_requirement_evidence() -> None:
    result = match_job("Experienced professional", "Bring curiosity and do great work")

    assert result.score is None
    assert "Insufficient evidence" in result.evidence[0]
    assert "not a probability" in result.score_meaning


def test_empty_inputs_are_rejected() -> None:
    with pytest.raises(Exception, match="Resume text is empty"):
        analyze_resume("   ")
    with pytest.raises(Exception, match="Job description is empty"):
        match_job("Python", "   ")


def test_prediction_contract_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        PredictionResult(
            cluster_id=1,
            cluster_name="Engineering",
            confidence=1.5,
            top_skills=[],
            domains=[],
            seniority="Unknown",
            behavioral_signals=[],
            adjacent_roles=[],
            evidence=[],
            model_version="test",
            taxonomy_version="test",
            scoring_mode="taxonomy",
        )
