"""Checksum-verified, cached loading of compact runtime artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from skillmap.config.settings import get_settings
from skillmap.core.exceptions import ArtifactUnavailableError
from skillmap.domain.models import ClusterSummary, RuntimeManifest


@dataclass(frozen=True)
class RuntimeAssets:
    manifest: RuntimeManifest
    taxonomy: dict[str, Any]
    clusters: tuple[ClusterSummary, ...]
    vectorizer: Any
    classifier: Any


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


@lru_cache(maxsize=1)
def load_runtime_assets() -> RuntimeAssets:
    import joblib

    root = get_settings().artifact_dir.resolve()
    manifest_path = root / "model_manifest.json"
    try:
        manifest = RuntimeManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        for filename, expected_digest in manifest.artifacts.items():
            path = (root / filename).resolve()
            if root not in path.parents or not path.is_file():
                raise ValueError(f"missing artifact: {filename}")
            if _digest(path) != expected_digest:
                raise ValueError(f"artifact checksum mismatch: {filename}")

        taxonomy = json.loads((root / "skill_taxonomy.json").read_text("utf-8"))
        raw_clusters = json.loads((root / "cluster_catalog.json").read_text("utf-8"))
        clusters = tuple(ClusterSummary.model_validate(item) for item in raw_clusters)
        vectorizer = joblib.load(root / "vectorizer.joblib")
        classifier = joblib.load(root / "classifier.joblib")
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ArtifactUnavailableError(type(exc).__name__) from exc
    return RuntimeAssets(
        manifest=manifest,
        taxonomy=taxonomy,
        clusters=clusters,
        vectorizer=vectorizer,
        classifier=classifier,
    )


def runtime_ready() -> bool:
    try:
        load_runtime_assets()
    except ArtifactUnavailableError:
        return False
    return True
