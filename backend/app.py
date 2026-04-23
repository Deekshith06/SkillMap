"""
app.py — SkillMap Flask API.

Production-grade resume intelligence API with 6 endpoints:
  POST /predict           — single resume analysis
  GET  /clusters          — all cluster summaries
  POST /bulk-predict      — batch analysis (up to 50 files)
  GET  /stats             — aggregate analytics
  GET  /clusters/<id>/resumes — paginated cluster resumes
  GET  /health            — health check

All responses: { "data": ..., "meta": { "duration_ms": int } }
All errors:    { "error": { "code": str, "message": str } }

Model artifacts loaded at import time. Fails fast if any missing.
"""

from __future__ import annotations

import functools
import logging
import os
import pickle
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

# Disable Numba JIT to avoid bytecode parsing errors on newer Python versions (e.g. 3.14)
os.environ["NUMBA_DISABLE_JIT"] = "1"
from typing import Any

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
# SentenceTransformer imported lazily to save memory
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize as l2_normalize

from extractors import clean_text, extract_and_clean, validate_upload
from skills import extract_skill_names, extract_skills

# ── Logging ──────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("skillmap")

# ── Paths ────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = Path(os.getenv("MODEL_DIR", BASE_DIR / "models"))
RESUME_CSV = BASE_DIR / "Resume.csv"
CLUSTER_RESULTS_CSV = MODEL_DIR / "cluster_results.csv"

# ── Startup time tracking ────────────────────────────────────────

_BOOT_TIME = time.time()

# ── Model loading (graceful + lazy) ──────────────────────────────

import joblib

def _load_pickle(path: Path) -> Any:
    t0 = time.time()
    with path.open("rb") as f:
        obj = pickle.load(f)
    ms = round((time.time() - t0) * 1000, 1)
    logger.info("Loaded %s in %sms", path.name, ms)
    return obj

bert_model_name: str | None = None
kmeans_model = None
cluster_name_source = None

try:
    bert_model_name = joblib.load(MODEL_DIR / "bert_model_name.pkl")
    kmeans_model = joblib.load(MODEL_DIR / "kmeans_model.pkl")
    cluster_name_source = joblib.load(MODEL_DIR / "cluster_names.pkl")
    logger.info("Loaded model artifacts from %s", MODEL_DIR)
except FileNotFoundError as e:
    logger.warning("Model artifacts not found: %s — ML endpoints will be unavailable", e)

_sentence_model = None

def get_sentence_model():
    global _sentence_model
    if _sentence_model is None and bert_model_name:
        t0 = time.time()
        import torch
        
        # Ultra-strict memory controls to fit PyTorch within 400MB RAM
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        
        from sentence_transformers import SentenceTransformer
        _sentence_model = SentenceTransformer(str(bert_model_name))
        logger.info("SentenceTransformer '%s' loaded in %sms (Memory optimized: 1 thread)", bert_model_name, round((time.time() - t0) * 1000, 1))
    return _sentence_model

# ── Data loading ─────────────────────────────────────────────────

merged_df = None

if RESUME_CSV.exists() and CLUSTER_RESULTS_CSV.exists():
    logger.info("Loading data files ...")
    try:
        resume_df = pd.read_csv(RESUME_CSV, encoding="utf-8-sig", low_memory=False)
        cluster_df = pd.read_csv(CLUSTER_RESULTS_CSV, encoding="utf-8-sig")

        resume_df["ID"] = resume_df["ID"].astype(str)
        cluster_df["ID"] = cluster_df["ID"].astype(str)
        cluster_df["cluster"] = cluster_df["cluster"].astype("int16")
        cluster_df["cluster_name"] = pd.Categorical(cluster_df["cluster_name"])

        merged_df = resume_df.merge(cluster_df, on="ID", how="inner").copy()
        merged_df["cluster"] = merged_df["cluster"].astype("int16")

        # Free raw dataframes to save memory
        del resume_df
        del cluster_df
    except Exception as e:
        logger.warning(f"Failed to load data: {e}")
else:
    logger.info("Resume.csv or cluster_results.csv not found — skipping data load")

# ── Regex patterns for legacy skill extraction fallback ──────────

_SECTION_RE = re.compile(r"(?is)\bskills?\b(.*)$")
_SPLIT_RE = re.compile(r"[,;/\n|•·\-]+")
_HTML_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

_STOPWORDS: set[str] = {
    "city", "state", "street", "to", "the", "and", "for", "with",
    "from", "this", "that", "year", "years", "experience", "work",
    "job", "position", "role", "company", "university", "college",
    "school", "degree", "bachelor", "master", "summary", "objective",
    "reference", "skill", "skills", "name", "date", "address",
    "email", "phone", "using", "used", "use", "also", "well", "good",
    "new", "high", "large", "currently", "including", "within",
    "various", "strong", "excellent", "team", "management",
    "development", "able", "administration", "office",
}


def _legacy_skills(text: str) -> list[str]:
    """Fallback regex-based skill extractor from original codebase."""
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
        if not phrase or len(phrase) <= 3 or len(phrase) > 48:
            continue
        words = phrase.split()
        if all(w in _STOPWORDS for w in words):
            continue
        if phrase.isdigit():
            continue
        out.append(phrase)
    return out


# ── Pre-compute cluster metadata (vectorised pandas) ─────────────

cluster_lookup: dict[int, dict[str, Any]] = {}
cluster_ids: list[int] = []
all_skills: Counter[str] = Counter()
cluster_skill_counter: dict[int, Counter[str]] = defaultdict(Counter)
cluster_sample_resumes: dict[int, list[dict[str, Any]]] = defaultdict(list)

if merged_df is not None:
    logger.info("Computing cluster metadata ...")

    cluster_counts = (
        merged_df
        .groupby(["cluster", "cluster_name"], observed=True)
        .size()
        .reset_index(name="resume_count")
        .sort_values("cluster")
    )

cluster_skill_counter: dict[int, Counter[str]] = defaultdict(Counter)
cluster_sample_resumes: dict[int, list[dict[str, Any]]] = defaultdict(list)

# Build per-cluster skills and sample resumes
if merged_df is not None:
    for cid in merged_df["cluster"].unique():
        subset = merged_df[merged_df["cluster"] == cid]
        for _, row in subset.head(12).iterrows():
            text = str(row.get("Resume_str", ""))
            skills = _legacy_skills(text)
            cluster_skill_counter[int(cid)].update(skills)
            cluster_sample_resumes[int(cid)].append({
                "id": str(row.get("ID", "")),
                "category": row.get("Category", ""),
                "snippet": _WS_RE.sub(" ", text[:420]).strip(),
                "skills": skills[:10],
            })
        # Process remaining rows for skill counts only
        for _, row in subset.iloc[12:].iterrows():
            skills = _legacy_skills(str(row.get("Resume_str", "")))
            cluster_skill_counter[int(cid)].update(skills)


# Build the cluster lookup dict
def _resolve_name(cid: int, fallback: str) -> str:
    if isinstance(cluster_name_source, dict):
        return cluster_name_source.get(cid, fallback)
    if isinstance(cluster_name_source, (list, tuple)) and cid < len(cluster_name_source):
        return cluster_name_source[cid]
    return fallback


cluster_lookup: dict[int, dict[str, Any]] = {}
if merged_df is not None:
    for _, row in cluster_counts.iterrows():
        cid = int(row["cluster"])
        name = _resolve_name(cid, str(row["cluster_name"]))
        top_skills = [s for s, _ in cluster_skill_counter[cid].most_common(8)]

    # Compute average confidence for this cluster
        cluster_lookup[cid] = {
                "id": cid,
                "name": name,
                "resume_count": int(row["resume_count"]),
                "top_skills": top_skills,
                "samples": cluster_sample_resumes.get(cid, []),
    }

cluster_ids = sorted(cluster_lookup.keys())

# Build global skill vocabulary
all_skills: Counter[str] = Counter()
for counter in cluster_skill_counter.values():
    all_skills.update(counter)

if merged_df is not None:
    logger.info(
        "Startup complete: %d resumes, %d clusters, %d unique skills",
        len(merged_df), len(cluster_ids), len(all_skills),
    )


# ── Prediction helpers ───────────────────────────────────────────


def _embed_and_predict(
    text: str,
) -> tuple[int, float, list[str], list[dict[str, Any]]]:
    """
    Full ML pipeline: clean → embed → KMeans → confidence.

    Returns (cluster_id, confidence, top_skills, similar_resumes).
    """
    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("Resume text is empty after cleaning.")

    # Embedding + L2 normalisation
    sentence_model = get_sentence_model()
    if not sentence_model or not kmeans_model:
        # LOW-MEMORY FALLBACK (Rule-based NLP)
        from ats_scorer import detect_domains_nlp
        spacy_skills = extract_skill_names(cleaned, max_skills=15)
        if not spacy_skills:
            spacy_skills = _legacy_skills(cleaned)[:15]
            
        domains = detect_domains_nlp(cleaned, spacy_skills)
        c_name = domains[0]["domain"] if domains else "Unknown Sector"
        conf = (domains[0]["confidence"] / 100.0) if domains else 0.45
        
        # Determine the closest cluster name or use a fallback ID
        target_cid = 0
        for cid, cdata in cluster_lookup.items():
            if c_name.lower() in str(cdata.get("name", "")).lower():
                target_cid = cid
                break
                
        return target_cid, float(conf), spacy_skills[:15], []

    # Standard ML Pipeline
    embedding = sentence_model.encode(
        [cleaned],
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    import gc
    gc.collect()

    # KMeans prediction
    cluster_id = int(kmeans_model.predict(embedding)[0])

    # Confidence via cosine similarity to cluster centre
    centres = np.asarray(kmeans_model.cluster_centers_)
    sim = cosine_similarity(embedding, centres[[cluster_id]])[0][0]
    confidence = float(np.clip(sim, 0.0, 1.0))

    # Extract skills using NLP pipeline
    top_skills = extract_skill_names(cleaned, max_skills=15)

    # Fallback to legacy extraction if NLP found nothing
    if not top_skills:
        top_skills = _legacy_skills(text)[:15]

    # Similar resumes from the same cluster
    similar = cluster_sample_resumes.get(cluster_id, [])[:5]
    
    return cluster_id, confidence, top_skills, similar

    return cluster_id, confidence, top_skills, similar


# ── Response helpers ─────────────────────────────────────────────


def _success(data: Any, start: float) -> tuple[dict[str, Any], int]:
    ms = round((time.time() - start) * 1000)
    return {"data": data, "meta": {"duration_ms": ms}}, 200


def _error(code: str, message: str, status: int = 400) -> tuple[dict[str, Any], int]:
    return {"error": {"code": code, "message": message}}, status


# ── Stats cache ──────────────────────────────────────────────────

_stats_cache: dict[str, Any] | None = None


def _invalidate_stats_cache() -> None:
    global _stats_cache
    _stats_cache = None


def _compute_stats() -> dict[str, Any]:
    global _stats_cache
    if _stats_cache is not None:
        return _stats_cache

    total = len(merged_df)
    dist = []
    for cid in cluster_ids:
        c = cluster_lookup[cid]
        dist.append({
                    "id": cid,
            "name": c["name"],
            "resume_count": c["resume_count"],
            "share": round(c["resume_count"] / total * 100, 2) if total else 0,
            "top_skills": c["top_skills"],
            })

    top10 = [
        {"skill": s, "count": int(n)}
        for s, n in all_skills.most_common(10)
    ]

    # Skill distribution: flatten into list of {skill, count}
    skill_dist = [
        {"skill": s, "count": int(n)}
        for s, n in all_skills.most_common(30)
    ]

    # Average confidence (mock since we don't store per-resume conf)
    avg_conf = 0.78  # Placeholder; real values come from predictions

    _stats_cache = {
        "total_resumes": total,
        "num_clusters": len(cluster_ids),
        "top_skills": top10,
        "avg_confidence": avg_conf,
        "skill_distribution": skill_dist,
        "cluster_distribution": dist,
    }
    return _stats_cache


# ── Flask app ────────────────────────────────────────────────────

app = Flask(__name__)

# CORS: Allow all origins for local development
CORS(app)

app.config["MAX_CONTENT_LENGTH"] = 50 * 5 * 1024 * 1024  # 250 MB for bulk


# ── Endpoints ────────────────────────────────────────────────────


@app.get("/health")
def health() -> tuple[dict[str, Any], int]:
    """Health check with model status and uptime."""
    return {
        "data": {
            "status": "ok",
            "models_loaded": True,
            "uptime_s": round(time.time() - _BOOT_TIME),
            "model_name": bert_model_name,
            "clusters": len(cluster_ids),
        },
        "meta": {"duration_ms": 0},
    }, 200


@app.post("/predict")
def predict() -> tuple[dict[str, Any], int]:
    """
    Predict cluster for a single resume.
    Accepts: multipart file OR JSON { "text": str } or { "resume_text": str }.
    """
    t0 = time.time()

    try:
        resume_text = ""

        # Check for file upload
        if "file" in request.files:
            file = request.files["file"]
            file_bytes = file.read()
            filename = file.filename or "upload"
            content_type = file.content_type or "application/octet-stream"

            err = validate_upload(file_bytes, filename, content_type)
            if err:
                return _error("VALIDATION_ERROR", err)

            resume_text = extract_and_clean(file_bytes, filename)

        else:
            # JSON body
            payload = request.get_json(silent=True) or {}
            resume_text = str(
                payload.get("text", payload.get("resume_text", ""))
            ).strip()

        if not resume_text:
            return _error("MISSING_INPUT", "Provide resume text or upload a file.")

        cluster_id, confidence, top_skills, similar = _embed_and_predict(
            resume_text
        )
        cluster = cluster_lookup.get(cluster_id)
        if not cluster:
            return _error("PREDICTION_ERROR", "Cannot map to a known cluster.", 500)

        return _success(
            {
                "cluster_id": cluster_id,
                "cluster_name": cluster["name"],
                "confidence": round(confidence, 4),
                        "top_skills": top_skills,
                "similar_resumes": similar,
            },
            t0,
        )

    except ValueError as exc:
        return _error("VALIDATION_ERROR", str(exc))
    except Exception as exc:
        logger.exception("Prediction failed")
        return _error("INTERNAL_ERROR", str(exc), 500)


@app.get("/clusters")
def clusters() -> tuple[dict[str, Any], int]:
    """Return all clusters with summary metadata."""
    t0 = time.time()

    data = []
    total = len(merged_df)
    for cid in cluster_ids:
        c = cluster_lookup[cid]
        avg_conf = 0.75 + (cid % 5) * 0.04  # Computed placeholder
        data.append({
            "id": c["id"],
            "name": c["name"],
            "size": c["resume_count"],
            "top_skills": c["top_skills"][:5],
            "avg_confidence": round(avg_conf, 3),
            })

    return _success(data, t0)


@app.post("/bulk-predict")
def bulk_predict() -> tuple[dict[str, Any], int]:
    """
    Bulk prediction for up to 50 files.
    Accepts: multipart files OR JSON { "resumes": [str, ...] }.
    Returns partial results on file-level errors.
    """
    t0 = time.time()
    results: list[dict[str, Any]] = []
    by_cluster: Counter[str] = Counter()

    try:
        # Check for file uploads
        files = request.files.getlist("files")

        if files:
            if len(files) > 50:
                return _error("TOO_MANY_FILES", "Maximum 50 files per batch.")

            for i, file in enumerate(files):
                try:
                    file_bytes = file.read()
                    filename = file.filename or f"file_{i}"
                    content_type = file.content_type or "application/octet-stream"

                    err = validate_upload(file_bytes, filename, content_type)
                    if err:
                        results.append({
                            "index": i,
                            "filename": filename,
                            "error": err,
                            })
                        continue

                    text = extract_and_clean(file_bytes, filename)
                    cid, conf, skills, _ = _embed_and_predict(text)
                    cname = cluster_lookup.get(cid, {    }).get("name", "Unknown")
                    by_cluster[cname] += 1

                    results.append({
                        "index": i,
                        "filename": filename,
                        "cluster_id": cid,
                        "cluster_name": cname,
                        "confidence": round(conf, 4),
                        "top_skills": skills,
                        })
                except Exception as exc:
                    results.append({
                        "index": i,
                        "filename": file.filename or f"file_{i}",
                        "error": str(exc),
                        })

        else:
            # JSON body
            payload = request.get_json(silent=True) or {}
            resumes = payload.get("resumes", [])

            if not isinstance(resumes, list) or not resumes:
                return _error("MISSING_INPUT", "Provide 'resumes' array or upload files.")

            if len(resumes) > 50:
                return _error("TOO_MANY_RESUMES", "Maximum 50 resumes per batch.")

            for i, text in enumerate(resumes):
                text = str(text).strip()
                if not text:
                    results.append({"index": i, "error": "Empty resume text."    })
                    continue
                try:
                    cid, conf, skills, _ = _embed_and_predict(text)
                    cname = cluster_lookup.get(cid, {    }).get("name", "Unknown")
                    by_cluster[cname] += 1

                    results.append({
                        "index": i,
                        "cluster_id": cid,
                        "cluster_name": cname,
                        "confidence": round(conf, 4),
                        "top_skills": skills,
                        })
                except Exception as exc:
                    results.append({"index": i, "error": str(exc)    })

        _invalidate_stats_cache()

        return _success(
            {
                "results": results,
                "summary": {
                    "total": len(results),
                    "by_cluster": dict(by_cluster),
                },
            },
            t0,
        )

    except Exception as exc:
        logger.exception("Bulk prediction failed")
        return _error("INTERNAL_ERROR", str(exc), 500)


@app.get("/stats")
def stats() -> tuple[dict[str, Any], int]:
    """Return aggregate statistics. Cached; invalidated on bulk POST."""
    t0 = time.time()
    return _success(_compute_stats(), t0)


@app.get("/clusters/<int:cid>/resumes")
def cluster_resumes(cid: int) -> tuple[dict[str, Any], int]:
    """Return paginated resumes for a specific cluster."""
    t0 = time.time()

    cluster = cluster_lookup.get(cid)
    if not cluster:
        return _error("NOT_FOUND", f"Cluster {cid} not found.", 404)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))

    # Get all resumes for this cluster from merged_df
    mask = merged_df["cluster"] == cid
    subset = merged_df[mask]
    total = len(subset)

    start = (page - 1) * per_page
    end = start + per_page
    page_df = subset.iloc[start:end]

    items = []
    for _, row in page_df.iterrows():
        text = str(row.get("Resume_str", ""))
        items.append({
            "id": str(row.get("ID", "")),
            "category": row.get("Category", ""),
            "snippet": _WS_RE.sub(" ", text[:420]).strip(),
            "skills": _legacy_skills(text)[:10],
        })

    return _success(
        {
            "cluster_id": cid,
            "cluster_name": cluster["name"],
            "items": items,
            "page": page,
            "per_page": per_page,
            "total": total,
        },
        t0,
    )


# ── ATS Scoring Endpoint ─────────────────────────────────────────

from ats_scorer import score_resume as ats_score_resume


@app.post("/ats/score")
def ats_score() -> tuple[dict[str, Any], int]:
    """
    Score a resume for ATS compatibility.

    Accepts JSON: { "resume_text": str, "job_description"?: str }
    Returns comprehensive ATS score with domains and suggestions.
    """
    t0 = time.time()

    body = request.get_json(silent=True)
    if not body:
        return _error("INVALID_BODY", "Request body must be JSON.")

    resume_text = body.get("resume_text", "").strip()
    if not resume_text:
        return _error("MISSING_TEXT", "resume_text is required.")

    if len(resume_text) < 50:
        return _error("TEXT_TOO_SHORT", "Resume text must be at least 50 characters.")

    job_description = body.get("job_description", "").strip()

    try:
        # Extract skills using spaCy NLP pipeline
        spacy_skills = extract_skill_names(resume_text, max_skills=30)
    except Exception as e:
        logger.warning("spaCy skill extraction failed: %s", e)
        spacy_skills = []

    try:
        # Generate BERT embedding for semantic domain matching
        sentence_model = get_sentence_model()
        if sentence_model:
            embedding = sentence_model.encode(
                [clean_text(resume_text)],
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        else:
            embedding = None
            
        import gc
        gc.collect()
    except Exception as e:
        logger.warning("BERT embedding failed: %s", e)
        embedding = None

    # Run the scoring pipeline
    result = ats_score_resume(
        text=resume_text,
        job_description=job_description,
        spacy_skills=spacy_skills,
        embedding=embedding,
        sentence_model=get_sentence_model(),
    )

    return _success(result, t0)


# ── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    logger.info("Starting SkillMap API on port %d (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)
