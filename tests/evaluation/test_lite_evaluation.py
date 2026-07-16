from __future__ import annotations

import pytest

from skillmap.ml_runtime.lite_engine import LiteEngine


@pytest.mark.evaluation
def test_more_required_skill_evidence_improves_match_score() -> None:
    engine = LiteEngine()
    job = "Python FastAPI SQL Docker Kubernetes engineer with 4 years experience"
    weak = engine.match("Python developer with 1 year experience", job)
    strong = engine.match(
        "Python FastAPI SQL Docker Kubernetes engineer with 5 years experience",
        job,
    )

    assert strong.score > weak.score
    assert len(strong.matched_skills) > len(weak.matched_skills)
    assert strong.score_breakdown["experience_alignment"] == 100.0


@pytest.mark.evaluation
def test_unknown_resume_returns_no_fabricated_domain() -> None:
    result = LiteEngine().analyze("Enthusiastic professional seeking opportunities")

    assert result.cluster_id == -1
    assert result.cluster_name == "Insufficient evidence"
    assert result.confidence == 0.0
    assert result.evidence
