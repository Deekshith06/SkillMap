from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from skillmap.adapters.artifact_repository import load_runtime_assets, runtime_ready
from skillmap.api import health
from skillmap.config.settings import get_settings
from skillmap.core.exceptions import ArtifactUnavailableError, FullModeUnavailableError
from skillmap.ml_runtime import get_engine
from skillmap.ml_runtime.full_engine import FullEngine


def test_lite_runtime_analyzes_without_training_data(monkeypatch: pytest.MonkeyPatch) -> None:
    original_open = Path.open

    def guarded_open(path: Path, *args: object, **kwargs: object):
        if path.name in {"Resume.csv", "cluster_results.csv"}:
            raise AssertionError("training data was opened by the runtime")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    get_engine.cache_clear()
    result = get_engine().analyze(
        "Senior Python engineer using FastAPI, Docker, Kubernetes, and AWS."
    )

    assert result.cluster_name != "Insufficient evidence"
    assert result.model_version == "skillmap-lite-1.0.0"
    assert result.evidence


def test_missing_runtime_artifacts_fail_explicitly(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("SKILLMAP_ARTIFACT_DIR", str(tmp_path / "missing"))
    get_settings.cache_clear()
    load_runtime_assets.cache_clear()
    try:
        with pytest.raises(ArtifactUnavailableError):
            load_runtime_assets()
        assert runtime_ready() is False
    finally:
        monkeypatch.delenv("SKILLMAP_ARTIFACT_DIR")
        get_settings.cache_clear()
        load_runtime_assets.cache_clear()


def test_full_mode_requires_local_dependencies_and_model() -> None:
    with pytest.raises(FullModeUnavailableError):
        FullEngine()


def test_health_endpoint_reports_runtime_version() -> None:
    response = asyncio.run(health())
    body = json.loads(response.body)

    assert response.status_code == 200
    assert body["status"] == "ready"
    assert body["model_version"] == "skillmap-lite-1.0.0"
