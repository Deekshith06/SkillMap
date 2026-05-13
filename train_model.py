import pandas as pd
import numpy as np
import logging
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer

from skillmap.ml.extractors import clean_text
from skillmap.ml.skills import extract_skill_names
from skillmap.ml.clusterer import build_cluster_pipeline, label_clusters, save_cluster_models

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("train_model")

def train():
    BASE_DIR = Path(__file__).resolve().parent
    MODEL_DIR = BASE_DIR / "models"
    MODEL_DIR.mkdir(exist_ok=True, parents=True)

    csv_path = BASE_DIR / "Resume.csv"
    if not csv_path.exists():
        logger.error(f"{csv_path} not found!")
        return

    logger.info(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    
    if "ID" in df.columns:
        df = df.rename(columns={"ID": "resume_id"})

    logger.info(f"Loaded {len(df)} rows. Cleaning text and extracting skills...")
    texts = []
    skill_lists = []
    
    # Process just enough to train accurately (HDBSCAN works best with more points, let's use all if fast, or sample if large)
    # Resume.csv usually has ~2400 rows
    for idx, row in df.iterrows():
        text = str(row.get("Resume_str", ""))
        cleaned = clean_text(text)
        skills = extract_skill_names(cleaned, max_skills=25)
        skill_text = " ".join(skills) if skills else cleaned
        texts.append(skill_text)
        skill_lists.append(skills)

    logger.info("Computing embeddings using all-MiniLM-L6-v2...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)

    logger.info(f"Building cluster pipeline on {embeddings.shape} embeddings...")
    try:
        result = build_cluster_pipeline(embeddings)
    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        return

    labels = result["labels"]
    
    logger.info("Auto-labeling clusters based on dominant skills...")
    cluster_names = label_clusters(labels, skill_lists)

    logger.info("Saving ML models and artifacts...")
    save_cluster_models(result, cluster_names)

    logger.info("Generating and saving cluster_results.csv and umap_coords.csv...")
    df["cluster_id"] = labels
    df["cluster_name"] = [cluster_names.get(cid, "Noise") for cid in labels]
    
    # Save the necessary columns
    out_csv = MODEL_DIR / "cluster_results.csv"
    df[["resume_id", "cluster_id", "cluster_name"]].to_csv(out_csv, index=False)
    logger.info(f"Saved {out_csv}")

    # Save UMAP coordinates
    X_2d = result["X_2d"]
    df["umap_x"] = X_2d[:, 0]
    df["umap_y"] = X_2d[:, 1]
    umap_csv = MODEL_DIR / "umap_coords.csv"
    df[["resume_id", "cluster_id", "cluster_name", "umap_x", "umap_y"]].to_csv(umap_csv, index=False)
    logger.info(f"Saved {umap_csv}")

if __name__ == "__main__":
    train()
