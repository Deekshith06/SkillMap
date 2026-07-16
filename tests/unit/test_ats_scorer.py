from skillmap.ml.ats_scorer import score_resume


def test_score_resume_accepts_missing_job_description() -> None:
    result = score_resume("Python engineer building reliable APIs", job_description=None)

    assert 0 <= result["total"] <= 100
    assert "categories" in result
