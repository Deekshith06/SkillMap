"""Compatibility API for callers migrating to typed runtime services."""

from __future__ import annotations

from typing import Any

from skillmap.config.settings import get_settings
from skillmap.domain.models import PredictionResult
from skillmap.ml_runtime import get_engine
from skillmap.services.analysis_service import get_clusters, get_stats


def embed_and_predict(text: str) -> PredictionResult:
    return get_engine().analyze(text)


def get_sentence_model() -> Any | None:
    if get_settings().mode != "full":
        return None
    return getattr(get_engine(), "_semantic_model", None)


def cluster_lookup() -> dict[int, dict[str, Any]]:
    return {cluster["id"]: cluster for cluster in get_clusters()}


__all__ = [
    "cluster_lookup",
    "embed_and_predict",
    "get_clusters",
    "get_sentence_model",
    "get_stats",
]
