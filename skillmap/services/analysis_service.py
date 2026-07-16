"""Business operations shared by single, ATS, bulk, and health workflows."""

from __future__ import annotations

import logging
import time
from collections import Counter
from typing import Any

from skillmap.adapters.artifact_repository import load_runtime_assets
from skillmap.config.logging import log_analysis_event
from skillmap.core.exceptions import UserFacingError, new_request_id
from skillmap.domain.models import MatchResult, PredictionResult
from skillmap.ml_runtime import get_engine

logger = logging.getLogger("skillmap.analysis")


def analyze_resume(text: str) -> PredictionResult:
    if not text.strip():
        raise UserFacingError("Resume text is empty.", category="empty_resume")
    request_id = new_request_id()
    started = time.perf_counter()
    try:
        result = get_engine().analyze(text)
    except UserFacingError:
        raise
    except Exception as exc:
        raise UserFacingError(
            "The analysis could not be completed.",
            category="analysis_failure",
            request_id=request_id,
        ) from exc
    log_analysis_event(
        logger,
        request_id=request_id,
        operation="resume_analysis",
        outcome="success",
        duration_ms=round((time.perf_counter() - started) * 1000),
        scoring_mode=result.scoring_mode,
        model_version=result.model_version,
    )
    return result


def match_job(resume_text: str, job_text: str) -> MatchResult:
    if not resume_text.strip():
        raise UserFacingError("Resume text is empty.", category="empty_resume")
    if not job_text.strip():
        raise UserFacingError("Job description is empty.", category="empty_job_description")
    request_id = new_request_id()
    started = time.perf_counter()
    try:
        result = get_engine().match(resume_text, job_text)
    except UserFacingError:
        raise
    except Exception as exc:
        raise UserFacingError(
            "Job matching could not be completed.",
            category="matching_failure",
            request_id=request_id,
        ) from exc
    log_analysis_event(
        logger,
        request_id=request_id,
        operation="job_match",
        outcome="success",
        duration_ms=round((time.perf_counter() - started) * 1000),
        scoring_mode=result.scoring_mode,
        model_version=result.model_version,
    )
    return result


def get_clusters() -> list[dict[str, Any]]:
    return [
        {
            "id": cluster.id,
            "name": cluster.name,
            "size": cluster.resume_count,
            "top_skills": cluster.top_skills,
            "avg_confidence": cluster.avg_confidence,
        }
        for cluster in load_runtime_assets().clusters
        if cluster.resume_count > 0
    ]


def get_stats() -> dict[str, Any]:
    assets = load_runtime_assets()
    clusters = [cluster for cluster in assets.clusters if cluster.resume_count > 0]
    total = sum(cluster.resume_count for cluster in clusters)
    skill_counts = Counter(skill for cluster in clusters for skill in cluster.top_skills)
    return {
        "total_resumes": total,
        "num_clusters": len(clusters),
        "taxonomy_domains": len(assets.taxonomy),
        "top_skills": [
            {"skill": skill, "count": count} for skill, count in skill_counts.most_common(10)
        ],
        "avg_confidence": None,
        "skill_distribution": [
            {"skill": skill, "count": count} for skill, count in skill_counts.most_common(30)
        ],
        "cluster_distribution": [
            {
                "id": cluster.id,
                "name": cluster.name,
                "resume_count": cluster.resume_count,
                "share": round(cluster.resume_count / total * 100, 2) if total else 0,
                "top_skills": cluster.top_skills,
            }
            for cluster in clusters
        ],
        "metrics": {
            "n_clusters": len(clusters),
            "model_version": assets.manifest.model_version,
            "taxonomy_version": assets.manifest.taxonomy_version,
            "scoring_mode": "taxonomy",
        },
    }
