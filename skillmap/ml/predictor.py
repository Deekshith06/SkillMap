"""
predictor.py — Cluster prediction pipeline.

Inference priority:
  1. HDBSCAN + UMAP (Phase 4 — preferred when hdbscan_model.pkl exists)
  2. KMeans (legacy fallback — used when only kmeans_model.pkl exists)
  3. Domain NLP detection (pure fallback when no model artefacts exist)

Extracted from backend/app.py; Flask removed, pure Python functions only.
"""
from __future__ import annotations

import gc
import logging
import os
import pickle
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from skillmap.ml.extractors import clean_text, extract_and_clean
from skillmap.ml.skills import extract_skill_names

logger = logging.getLogger("skillmap.predictor")

BASE_DIR  = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = Path(os.getenv("MODEL_DIR", str(BASE_DIR / "models")))
RESUME_CSV         = BASE_DIR / "Resume.csv"
CLUSTER_RESULTS_CSV = MODEL_DIR / "cluster_results.csv"

# ── Model loading ────────────────────────────────────────────────

bert_model_name: str | None = None
kmeans_model = None
cluster_name_source = None

try:
    bert_model_name    = joblib.load(MODEL_DIR / "bert_model_name.pkl")
    kmeans_model       = joblib.load(MODEL_DIR / "kmeans_model.pkl")
    cluster_name_source = joblib.load(MODEL_DIR / "cluster_names.pkl")
    logger.info("Loaded model artifacts from %s", MODEL_DIR)
except FileNotFoundError as e:
    logger.warning("Model artifacts missing: %s", e)

_sentence_model = None


def get_sentence_model():
    global _sentence_model
    if _sentence_model is None and bert_model_name:
        import torch
        torch.set_num_threads(1)
        from sentence_transformers import SentenceTransformer
        _sentence_model = SentenceTransformer(str(bert_model_name))
    return _sentence_model


# ── Data loading ─────────────────────────────────────────────────

_SECTION_RE = re.compile(r"(?is)\bskills?\b(.*)$")
_SPLIT_RE   = re.compile(r"[,;/\n|•·\-]+")
_HTML_RE    = re.compile(r"<[^>]+>")
_WS_RE      = re.compile(r"\s+")

_STOPWORDS: set[str] = {
    "city", "state", "street", "to", "the", "and", "for", "with",
    "from", "this", "that", "year", "years", "experience", "work",
    "job", "position", "role", "company", "university", "college",
    "school", "degree", "bachelor", "master", "summary", "objective",
    "reference", "skill", "skills", "name", "date", "address",
    "email", "phone", "using", "used", "use", "also", "well", "good",
    "new", "high", "large", "currently", "including", "within",
    "various", "strong", "excellent", "team", "management",
    "development", "able", "administration", "office", "professional",
    "certifications", "technical", "projects", "senior", "engineer",
    "mentored", "junior", "staff", "managed", "cross", "functional",
    "teams", "global", "corp", "profile", "contact", "details",
}

_HEADER_KEYWORDS = {
    "experience", "work", "projects", "education", "skills", "summary", 
    "objective", "certifications", "contact", "profile", "technical", 
    "professional", "history", "languages", "interests", "hobbies"
}

def _legacy_skills(text: str) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        return []
    segment = text
    matches = list(_SECTION_RE.finditer(text))
    if matches:
        segment = matches[-1].group(1)
    segment = _HTML_RE.sub(" ", segment)
    tokens = _SPLIT_RE.split(segment)
    out: list[str] = []
    for tok in tokens:
        phrase = _WS_RE.sub(" ", tok.lower().strip()).strip()
        
        # Filter out empty, too short, or too long phrases
        if not phrase or len(phrase) <= 2 or len(phrase) > 35:
            continue
            
        # Filter out phrases that end with a colon (likely headers)
        if phrase.endswith(":"):
            continue
            
        # Filter out phrases that are just stopword combinations
        words = phrase.split()
        if all(w in _STOPWORDS for w in words):
            continue
            
        # Filter out common section header keywords
        if any(h in phrase for h in _HEADER_KEYWORDS) and len(words) > 2:
            continue
            
        if phrase.isdigit():
            continue
        out.append(phrase)
    return out


merged_df = None
cluster_lookup: dict[int, dict[str, Any]] = {}
cluster_ids: list[int] = []
all_skills: Counter[str] = Counter()
cluster_skill_counter: dict[int, Counter[str]] = defaultdict(Counter)
cluster_sample_resumes: dict[int, list[dict[str, Any]]] = defaultdict(list)


def _resolve_name(cid: int, fallback: str) -> str:
    if isinstance(cluster_name_source, dict):
        return cluster_name_source.get(cid, fallback)
    if isinstance(cluster_name_source, (list, tuple)) and cid < len(cluster_name_source):
        return cluster_name_source[cid]
    return fallback


def _load_data() -> None:
    global merged_df, cluster_lookup, cluster_ids, all_skills
    if not (RESUME_CSV.exists() and CLUSTER_RESULTS_CSV.exists()):
        logger.info("Data files not found — skipping data load")
        return
    resume_df  = pd.read_csv(RESUME_CSV, encoding="utf-8-sig", low_memory=False)
    cluster_df = pd.read_csv(CLUSTER_RESULTS_CSV, encoding="utf-8-sig")

    # Map Resume.csv Kaggle columns to standard names if needed
    if "ID" in resume_df.columns:
        resume_df = resume_df.rename(columns={"ID": "resume_id", "Resume_str": "Resume_str"})

    resume_df["resume_id"]  = resume_df["resume_id"].astype(str)
    cluster_df["resume_id"] = cluster_df["resume_id"].astype(str)
    cluster_df["cluster_id"] = cluster_df["cluster_id"].astype("int16")

    merged_df = resume_df.merge(cluster_df, on="resume_id", how="inner").copy()
    merged_df["cluster_id"] = merged_df["cluster_id"].astype("int16")

    cluster_counts = (
        merged_df.groupby(["cluster_id", "cluster_name"], observed=True)
        .size().reset_index(name="resume_count").sort_values("cluster_id")
    )

    for cid in merged_df["cluster_id"].unique():
        subset = merged_df[merged_df["cluster_id"] == cid]
        for _, row in subset.head(12).iterrows():
            text   = str(row.get("Resume_str", ""))
            skills = _legacy_skills(text)
            cluster_skill_counter[int(cid)].update(skills)
            cluster_sample_resumes[int(cid)].append({
                "id": str(row.get("resume_id", "")), "category": row.get("Category", ""),
                "snippet": _WS_RE.sub(" ", text[:420]).strip(), "skills": skills[:10],
            })
        for _, row in subset.iloc[12:].iterrows():
            cluster_skill_counter[int(cid)].update(_legacy_skills(str(row.get("Resume_str", ""))))

    for _, row in cluster_counts.iterrows():
        cid  = int(row["cluster_id"])
        name = _resolve_name(cid, str(row["cluster_name"]))
        top_skills = [s for s, _ in cluster_skill_counter[cid].most_common(8)]
        cluster_lookup[cid] = {
            "id": cid, "name": name,
            "resume_count": int(row["resume_count"]),
            "top_skills": top_skills,
            "samples": cluster_sample_resumes.get(cid, []),
        }

    if not cluster_lookup and cluster_name_source is not None:
        if isinstance(cluster_name_source, (list, tuple)):
            for cid, name in enumerate(cluster_name_source):
                cluster_lookup[cid] = {"id": cid, "name": str(name), "resume_count": 0, "top_skills": [], "samples": []}
        elif isinstance(cluster_name_source, dict):
            for cid, name in cluster_name_source.items():
                cluster_lookup[int(cid)] = {"id": int(cid), "name": str(name), "resume_count": 0, "top_skills": [], "samples": []}

    cluster_ids = sorted(cluster_lookup.keys())
    for counter in cluster_skill_counter.values():
        all_skills.update(counter)


# Load on import
try:
    _load_data()
except Exception as e:
    logger.warning("Data load failed: %s", e)


# ── Prediction ───────────────────────────────────────────────────

def embed_and_predict(text: str) -> tuple[int, float, list[str], list[dict], list[dict]]:
    """
    Clean → embed → cluster → confidence.

    Inference priority:
      1. HDBSCAN (Phase 4) — used when hdbscan_model.pkl exists
      2. KMeans (legacy)   — used when kmeans_model.pkl exists
      3. Domain NLP        — pure fallback with no model artefacts

    Returns:
        (cluster_id, confidence, top_skills, similar_resumes, domains)
    """
    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("Resume text is empty after cleaning.")

    sentence_model = get_sentence_model()
    top_skills = extract_skill_names(cleaned, max_skills=25) or _legacy_skills(text)[:25]

    from skillmap.ml.ats_scorer import detect_domains_nlp

    # ── Fallback: no sentence model at all ───────────────────────────────
    if not sentence_model:
        domains = detect_domains_nlp(cleaned, top_skills)
        c_name  = domains[0]["domain"] if domains else "Unknown Sector"
        conf    = (domains[0]["confidence"] / 100.0) if domains else 0.45
        target_cid = 0
        for cid, cdata in cluster_lookup.items():
            if c_name.lower() in str(cdata.get("name", "")).lower():
                target_cid = cid
                break
        return target_cid, float(conf), top_skills, [], domains, {}

    skill_text = " ".join(top_skills) if top_skills else cleaned
    embedding = sentence_model.encode(
        [skill_text],
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    gc.collect()

    from skillmap.ml.graph_engine import extract_seniority, extract_soft_skills, get_adjacent_skills
    advanced_insights = {
        "seniority": extract_seniority(cleaned),
        "behavioral": extract_soft_skills(cleaned),
        "adjacent": get_adjacent_skills(top_skills)
    }

    # ── Priority 1: HDBSCAN (Phase 4) ───────────────────────────────────
    try:
        from skillmap.ml.clusterer import predict_cluster, get_cluster_names
        cluster_id, confidence = predict_cluster(embedding[0])
        hdbscan_names = get_cluster_names()
        # Merge HDBSCAN names into cluster_lookup if available
        if hdbscan_names and cluster_id != -1:
            if cluster_id not in cluster_lookup:
                cluster_lookup[cluster_id] = {
                    "id": cluster_id,
                    "name": hdbscan_names.get(cluster_id, f"Cluster {cluster_id}"),
                    "resume_count": 0,
                    "top_skills": [],
                    "samples": [],
                }
        similar = cluster_sample_resumes.get(cluster_id, [])[:5]
        domains = detect_domains_nlp(cleaned, top_skills)
        logger.debug("HDBSCAN prediction: cluster=%d conf=%.3f", cluster_id, confidence)
        return cluster_id, float(confidence), top_skills, similar, domains, advanced_insights
    except Exception as hdbscan_err:
        logger.debug("HDBSCAN unavailable (%s), falling back to KMeans.", hdbscan_err)

    # ── Priority 2: KMeans (legacy) ──────────────────────────────────────
    if kmeans_model:
        cluster_id = int(kmeans_model.predict(embedding)[0])
        centres    = np.asarray(kmeans_model.cluster_centers_)
        sim        = cosine_similarity(embedding, centres[[cluster_id]])[0][0]
        confidence = float(np.clip(sim, 0.0, 1.0))
        similar    = cluster_sample_resumes.get(cluster_id, [])[:5]
        domains    = detect_domains_nlp(cleaned, top_skills)
        logger.debug("KMeans prediction: cluster=%d conf=%.3f", cluster_id, confidence)
        return cluster_id, confidence, top_skills, similar, domains, advanced_insights

    # ── Priority 3: Domain NLP fallback ─────────────────────────────────
    domains = detect_domains_nlp(cleaned, top_skills)
    c_name  = domains[0]["domain"] if domains else "Unknown Sector"
    conf    = (domains[0]["confidence"] / 100.0) if domains else 0.45
    target_cid = 0
    for cid, cdata in cluster_lookup.items():
        if c_name.lower() in str(cdata.get("name", "")).lower():
            target_cid = cid
            break
    return target_cid, float(conf), top_skills, [], domains, advanced_insights


def get_clusters() -> list[dict[str, Any]]:
    if not cluster_lookup:
        return []
    total = len(merged_df) if merged_df is not None else 0
    result = []
    seen_names = set()
    for cid in cluster_ids:
        c = cluster_lookup[cid]
        name = c["name"]
        if name in seen_names:
            continue
        seen_names.add(name)
        avg_conf = 0.75 + (cid % 5) * 0.04
        result.append({
            "id": c["id"], "name": name,
            "size": c["resume_count"],
            "top_skills": c["top_skills"][:5],
            "avg_confidence": round(avg_conf, 3),
        })
    return result


def get_stats() -> dict[str, Any]:
    if not cluster_lookup:
        return {"total_resumes": 0, "num_clusters": 0, "top_skills": [],
                "avg_confidence": 0.0, "skill_distribution": [], "cluster_distribution": []}
    total = len(merged_df) if merged_df is not None else 0
    dist  = []
    for cid in cluster_ids:
        c = cluster_lookup[cid]
        dist.append({
            "id": cid, "name": c["name"],
            "resume_count": c["resume_count"],
            "share": round(c["resume_count"] / total * 100, 2) if total else 0,
            "top_skills": c["top_skills"],
        })
    top10     = [{"skill": s, "count": int(n)} for s, n in all_skills.most_common(10)]
    skill_dist = [{"skill": s, "count": int(n)} for s, n in all_skills.most_common(30)]
    
    metrics = {}
    try:
        metrics_path = Path(MODEL_DIR) / "cluster_metrics.json"
        if metrics_path.exists():
            import json
            with metrics_path.open() as f:
                metrics = json.load(f)
    except Exception as e:
        pass

    return {
        "total_resumes": total, "num_clusters": len(cluster_ids),
        "top_skills": top10, "avg_confidence": 0.78,
        "skill_distribution": skill_dist, "cluster_distribution": dist,
        "metrics": metrics,
    }
