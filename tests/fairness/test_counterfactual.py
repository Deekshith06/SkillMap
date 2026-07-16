from __future__ import annotations

from skillmap.ml_runtime.lite_engine import LiteEngine


def test_direct_identifier_counterfactual_does_not_change_match() -> None:
    engine = LiteEngine()
    job = "Python FastAPI SQL engineer with 4 years experience"
    first = engine.match(
        "Name: Ada Example\nada@example.com\nPython FastAPI SQL engineer with 5 years experience",
        job,
    )
    second = engine.match(
        "Name: Grace Example\ngrace@example.net\nPython FastAPI SQL engineer with 5 years experience",
        job,
    )

    assert first.score == second.score
    assert first.score_breakdown == second.score_breakdown


def test_academic_team_lead_does_not_imply_professional_management() -> None:
    result = LiteEngine._seniority(
        "University capstone team lead with six months of internship experience."
    )

    assert result not in {"Lead / Manager", "Director / Executive"}
