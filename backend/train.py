"""
train.py — Offline training pipeline for SkillMap.

Steps:
  1. Load Resume.csv; validate schema (assert required columns).
  2. Deduplicate on (resume_text hash); log removed count.
  3. Embed in batches of 64 to avoid OOM.
  4. L2-normalise all vectors before UMAP.
  5. UMAP: n_components=2, n_neighbors=15, min_dist=0.1, metric='cosine'.
  6. KMeans: k=auto (elbow method, range 4–12), random_state=42.
  7. Persist artifacts with joblib.dump.
  8. Log: silhouette score, Davies-Bouldin index, inertia.
  9. Save cluster_results.csv with columns:
       resume_id, cluster_id, cluster_name, confidence, top_skills

Reproducibility:
  Set PYTHONHASHSEED=0, pin random_state=42 everywhere.

Usage:
  python backend/train.py
"""

from __future__ import annotations

import hashlib
import logging
import os
import pickle
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import davies_bouldin_score, silhouette_score
from sklearn.preprocessing import normalize as l2_normalize

# ── Configuration ────────────────────────────────────────────────

RANDOM_STATE = 42
BATCH_SIZE = 64
K_RANGE = range(4, 13)  # 4 to 12 inclusive
MODEL_NAME = "all-MiniLM-L6-v2"

BASE_DIR = Path(__file__).resolve().parent.parent
RESUME_CSV = BASE_DIR / "Resume.csv"
MODEL_DIR = BASE_DIR / "models"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("train")

np.random.seed(RANDOM_STATE)
os.environ["PYTHONHASHSEED"] = "0"


# ── Step 1: Load and validate ────────────────────────────────────


def load_data() -> pd.DataFrame:
    logger.info("Loading %s ...", RESUME_CSV)
    if not RESUME_CSV.exists():
        raise FileNotFoundError(f"Resume.csv not found at {RESUME_CSV}")

    df = pd.read_csv(RESUME_CSV, encoding="utf-8-sig", low_memory=False)

    required = {"ID", "Resume_str", "Category"}
    missing = required - set(df.columns)
    assert not missing, f"Missing required columns: {missing}"

    logger.info("Loaded %d rows, columns: %s", len(df), list(df.columns))
    return df


# ── Step 2: Deduplicate ──────────────────────────────────────────


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    original_count = len(df)

    df = df.dropna(subset=["Resume_str"]).copy()
    df["_hash"] = df["Resume_str"].apply(
        lambda x: hashlib.md5(str(x).encode()).hexdigest()
    )
    df = df.drop_duplicates(subset="_hash", keep="first").drop(columns=["_hash"])

    removed = original_count - len(df)
    logger.info("Deduplicated: removed %d duplicates, %d remaining", removed, len(df))
    return df.reset_index(drop=True)


# ── Step 3: Embed in batches ─────────────────────────────────────


def embed_texts(
    texts: list[str], model: SentenceTransformer
) -> np.ndarray:
    logger.info("Embedding %d texts in batches of %d ...", len(texts), BATCH_SIZE)
    t0 = time.time()

    all_embeddings: list[np.ndarray] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i: i + BATCH_SIZE]
        embs = model.encode(
            batch,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=False,  # We L2-normalise after
        )
        all_embeddings.append(embs)

        if (i // BATCH_SIZE) % 20 == 0:
            logger.info("  Batch %d/%d", i // BATCH_SIZE + 1, len(texts) // BATCH_SIZE + 1)

    embeddings = np.vstack(all_embeddings)
    logger.info("Embedding complete in %.1fs, shape: %s", time.time() - t0, embeddings.shape)
    return embeddings


# ── Step 4: L2 normalise ─────────────────────────────────────────


def normalise(embeddings: np.ndarray) -> np.ndarray:
    logger.info("L2-normalising embeddings ...")
    return l2_normalize(embeddings, norm="l2")





# ── Step 6: KMeans with elbow method ─────────────────────────────


def find_optimal_k(data: np.ndarray) -> tuple[KMeans, int]:
    logger.info("Running elbow method for k in %s ...", list(K_RANGE))

    inertias: list[float] = []
    models: list[KMeans] = []

    for k in K_RANGE:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        km.fit(data)
        inertias.append(km.inertia_)
        models.append(km)
        logger.info("  k=%d  inertia=%.2f", k, km.inertia_)

    # Elbow: find the k with the biggest drop in inertia rate-of-change
    diffs = [inertias[i] - inertias[i + 1] for i in range(len(inertias) - 1)]
    diffs2 = [diffs[i] - diffs[i + 1] for i in range(len(diffs) - 1)]

    best_idx = 0
    if diffs2:
        best_idx = int(np.argmax(diffs2))

    best_k = list(K_RANGE)[best_idx]
    best_model = models[best_idx]

    logger.info("Selected k=%d via elbow method", best_k)
    return best_model, best_k


# ── Step 7 & 8: Evaluate and persist ─────────────────────────────


def evaluate(
    data: np.ndarray, labels: np.ndarray
) -> dict[str, float]:
    sil = silhouette_score(data, labels)
    db = davies_bouldin_score(data, labels)

    logger.info("Evaluation metrics:")
    logger.info("  Silhouette Score:     %.4f", sil)
    logger.info("  Davies-Bouldin Index: %.4f", db)

    return {"silhouette": sil, "davies_bouldin": db}


# ── Cluster naming ───────────────────────────────────────────────

# Default heuristic names based on category majority
def name_clusters(
    df: pd.DataFrame, labels: np.ndarray, k: int
) -> dict[int, str]:
    """Name clusters by majority category vote."""
    df = df.copy()
    df["_cluster"] = labels

    names: dict[int, str] = {}
    for cid in range(k):
        subset = df[df["_cluster"] == cid]
        if subset.empty:
            names[cid] = f"Cluster {cid}"
            continue

        top_cat = subset["Category"].value_counts().head(3)
        cat_labels = " & ".join(top_cat.index.tolist()[:2])
        names[cid] = cat_labels if cat_labels else f"Cluster {cid}"

    return names


# ── Main pipeline ────────────────────────────────────────────────


def main() -> None:
    logger.info("=" * 60)
    logger.info("SkillMap Training Pipeline")
    logger.info("=" * 60)

    # Step 1
    df = load_data()

    # Step 2
    df = deduplicate(df)

    # Load model
    logger.info("Loading SentenceTransformer '%s' ...", MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME)

    # Step 3
    texts = df["Resume_str"].fillna("").astype(str).tolist()
    embeddings = embed_texts(texts, model)

    # Step 4
    embeddings = normalise(embeddings)

    # Step 6
    kmeans, best_k = find_optimal_k(embeddings)
    labels = kmeans.labels_

    # Step 8: Evaluate
    evaluate(embeddings, labels)

    # Name clusters
    cluster_names = name_clusters(df, labels, best_k)
    logger.info("Cluster names: %s", cluster_names)

    # Step 7: Persist
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(MODEL_NAME, MODEL_DIR / "bert_model_name.pkl")
    joblib.dump(kmeans, MODEL_DIR / "kmeans_model.pkl")
    joblib.dump(cluster_names, MODEL_DIR / "cluster_names.pkl")

    logger.info("Saved model artifacts to %s", MODEL_DIR)

    # Step 9: cluster_results.csv
    results_df = pd.DataFrame({
        "ID": df["ID"].values,
        "Category": df["Category"].values,
        "cluster": labels.astype("int16"),
        "cluster_name": [cluster_names[int(l)] for l in labels],
    })
    results_df.to_csv(MODEL_DIR / "cluster_results.csv", index=False)
    logger.info("Saved cluster_results.csv (%d rows)", len(results_df))

    logger.info("=" * 60)
    logger.info("Training pipeline complete.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
