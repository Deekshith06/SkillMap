"""
ml/clusterer.py — UMAP + HDBSCAN clustering pipeline.

Replaces the legacy KMeans predictor with automatic-K density-based clustering.

Algorithm chain (from Phase 2 research):
  SentenceTransformer('all-MiniLM-L6-v2') → 384-dim embeddings
  → UMAP(n_components=5, metric='cosine')  → dense 5-dim representation
  → HDBSCAN(min_cluster_size=10, metric='euclidean', cluster_selection_method='eom')
  → automatic cluster labels + noise detection
  → UMAP(n_components=2) → 2-dim coords for scatter visualisation

Source: community proj_006 pattern; HDBSCAN params validated across resume corpora.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from skillmap.core.exceptions import InsufficientDataError, ModelNotFoundError

logger = logging.getLogger("skillmap.clusterer")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models"

# Minimum resumes to attempt clustering
_MIN_CLUSTER_SIZE_DEFAULT = 10
_MIN_RESUMES_REQUIRED = 30


# ─────────────────────────────────────────────────────────────────────────────
# Training pipeline
# ─────────────────────────────────────────────────────────────────────────────


def build_cluster_pipeline(
    embeddings: np.ndarray,
    min_cluster_size: int = _MIN_CLUSTER_SIZE_DEFAULT,
    umap_components: int = 5,
    umap_neighbors: int = 15,
    umap_min_dist: float = 0.1,
    random_state: int = 42,
) -> dict[str, Any]:
    """
    Full UMAP → HDBSCAN pipeline on a matrix of embeddings.

    Args:
        embeddings:       (N, 384) float32 array of L2-normalised embeddings.
        min_cluster_size: HDBSCAN minimum points per cluster.
        umap_components:  Target dimensionality for clustering (5 recommended).
        umap_neighbors:   UMAP n_neighbors parameter.
        umap_min_dist:    UMAP min_dist parameter.
        random_state:     Reproducibility seed.

    Returns:
        dict with keys: labels, X_2d, X_5d, reducer_5d, reducer_2d,
                        clusterer, n_clusters, noise_count, silhouette_score.

    Raises:
        InsufficientDataError: if fewer than _MIN_RESUMES_REQUIRED embeddings.
    """
    import hdbscan
    import umap as umap_lib
    from sklearn.metrics import silhouette_score

    n = len(embeddings)
    if n < _MIN_RESUMES_REQUIRED:
        raise InsufficientDataError(n=n, min_required=_MIN_RESUMES_REQUIRED)

    logger.info("Building UMAP(%dd) on %d embeddings...", umap_components, n)
    reducer_5d = umap_lib.UMAP(
        n_components=umap_components,
        metric="cosine",
        n_neighbors=umap_neighbors,
        min_dist=umap_min_dist,
        random_state=random_state,
        low_memory=True,
    )
    reducer_2d = umap_lib.UMAP(
        n_components=2,
        metric="cosine",
        n_neighbors=umap_neighbors,
        min_dist=umap_min_dist,
        random_state=random_state,
        low_memory=True,
    )

    X_5d: np.ndarray = reducer_5d.fit_transform(embeddings)
    X_2d: np.ndarray = reducer_2d.fit_transform(embeddings)

    logger.info("Running HDBSCAN(min_cluster_size=%d)...", min_cluster_size)
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,  # enables approximate_predict for new points
    )
    labels: np.ndarray = clusterer.fit_predict(X_5d)

    unique_labels = set(labels.tolist())
    n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
    noise_count = int((labels == -1).sum())

    if n_clusters > 1:
        # Only compute silhouette on non-noise points
        mask = labels != -1
        sil = float(silhouette_score(X_5d[mask], labels[mask])) if mask.sum() > 1 else 0.0
    else:
        sil = 0.0

    logger.info(
        "Clustering done → clusters=%d  noise=%d  silhouette=%.4f",
        n_clusters,
        noise_count,
        sil,
    )

    return {
        "labels": labels,
        "X_2d": X_2d,
        "X_5d": X_5d,
        "reducer_5d": reducer_5d,
        "reducer_2d": reducer_2d,
        "clusterer": clusterer,
        "n_clusters": n_clusters,
        "noise_count": noise_count,
        "silhouette_score": sil,
    }


def label_clusters(
    labels: np.ndarray,
    skill_lists: list[list[str]],
    existing_names: dict[int, str] | None = None,
) -> dict[int, str]:
    """
    Auto-label each cluster by its most frequent skill term.
    Falls back to existing_names if provided (e.g., from cluster_names.pkl).

    Args:
        labels:         1-D array of cluster labels (same length as skill_lists).
        skill_lists:    Per-resume list of extracted skill strings.
        existing_names: Optional override dict {cluster_id: label}.

    Returns:
        dict[cluster_id → human-readable label]
    """
    cluster_skill_counts: dict[int, Counter[str]] = {}

    for i, cid in enumerate(labels.tolist()):
        if cid == -1:
            continue
        if cid not in cluster_skill_counts:
            cluster_skill_counts[cid] = Counter()
        cluster_skill_counts[cid].update(skill_lists[i])

    cluster_names: dict[int, str] = {}
    for cid, counter in cluster_skill_counts.items():
        if existing_names and cid in existing_names:
            cluster_names[cid] = existing_names[cid]
        elif counter:
            top_skill = counter.most_common(1)[0][0].replace("_", " ").title()
            cluster_names[cid] = f"{top_skill} Specialists"
        else:
            cluster_names[cid] = f"Cluster {cid}"

    return cluster_names


def save_cluster_models(
    result: dict[str, Any],
    cluster_names: dict[int, str],
) -> None:
    """Persist all cluster artefacts to MODEL_DIR."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(result["clusterer"], MODEL_DIR / "hdbscan_model.pkl")
    joblib.dump(result["reducer_5d"], MODEL_DIR / "umap_5d_model.pkl")
    joblib.dump(result["reducer_2d"], MODEL_DIR / "umap_2d_model.pkl")
    joblib.dump(cluster_names, MODEL_DIR / "cluster_names.pkl")

    metrics = {
        "n_clusters": result["n_clusters"],
        "noise_count": result["noise_count"],
        "silhouette_score": round(result["silhouette_score"], 6),
    }
    (MODEL_DIR / "cluster_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    logger.info("Cluster artefacts saved to %s", MODEL_DIR)


# ─────────────────────────────────────────────────────────────────────────────
# Inference pipeline
# ─────────────────────────────────────────────────────────────────────────────

_hdbscan_model: Any = None
_umap_5d_model: Any = None
_umap_2d_model: Any = None
_cluster_names_loaded: dict[int, str] = {}


def _load_inference_models() -> None:
    global _hdbscan_model, _umap_5d_model, _umap_2d_model, _cluster_names_loaded
    hdbscan_path = MODEL_DIR / "hdbscan_model.pkl"
    if not hdbscan_path.exists():
        raise ModelNotFoundError(str(hdbscan_path))
    _hdbscan_model = joblib.load(hdbscan_path)
    _umap_5d_model = joblib.load(MODEL_DIR / "umap_5d_model.pkl")
    _umap_2d_model = joblib.load(MODEL_DIR / "umap_2d_model.pkl")
    _cluster_names_loaded = joblib.load(MODEL_DIR / "cluster_names.pkl")
    logger.info("HDBSCAN inference models loaded from %s", MODEL_DIR)


def predict_cluster(embedding: np.ndarray) -> tuple[int, float]:
    """
    Predict cluster for a single new 384-dim embedding.

    Returns:
        (cluster_id, membership_strength)  cluster_id == -1 means noise.

    Raises:
        ModelNotFoundError: if HDBSCAN artefacts are missing.
    """
    import hdbscan as hdbscan_lib

    global _hdbscan_model, _umap_5d_model
    if _hdbscan_model is None:
        _load_inference_models()

    emb_2d: np.ndarray = _umap_5d_model.transform(embedding.reshape(1, -1))
    labels, strengths = hdbscan_lib.approximate_predict(_hdbscan_model, emb_2d)
    return int(labels[0]), float(strengths[0])


def get_cluster_names() -> dict[int, str]:
    """Return the loaded cluster name mapping."""
    global _cluster_names_loaded
    if not _cluster_names_loaded:
        try:
            _load_inference_models()
        except ModelNotFoundError:
            return {}
    return _cluster_names_loaded


def get_cluster_metrics() -> dict:
    """Return stored cluster quality metrics from last training run."""
    metrics_path = MODEL_DIR / "cluster_metrics.json"
    if metrics_path.exists():
        return json.loads(metrics_path.read_text(encoding="utf-8"))
    return {"n_clusters": 0, "noise_count": 0, "silhouette_score": 0.0}


# ─────────────────────────────────────────────────────────────────────────────
# Retraining trigger check
# ─────────────────────────────────────────────────────────────────────────────

RETRAIN_MIN_NEW_RESUMES = 500
RETRAIN_SILHOUETTE_FLOOR = 0.35


def should_retrain(current_n: int, last_trained_n: int) -> tuple[bool, str]:
    """
    Check whether conditions warrant a retraining run.

    Returns:
        (should_retrain: bool, reason: str)
    """
    metrics = get_cluster_metrics()
    sil = metrics.get("silhouette_score", 1.0)

    if sil < RETRAIN_SILHOUETTE_FLOOR:
        return True, (f"Silhouette score {sil:.3f} < floor {RETRAIN_SILHOUETTE_FLOOR}")
    new_count = current_n - last_trained_n
    if new_count >= RETRAIN_MIN_NEW_RESUMES:
        return True, (
            f"{new_count} new resumes since last training (threshold={RETRAIN_MIN_NEW_RESUMES})"
        )
    return False, "No retraining needed"
