"""Offline training and compact runtime artifact export."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from skillmap.domain.taxonomy import domain_label, flatten_taxonomy

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "models"
RUNTIME_DIR = MODEL_DIR / "runtime"
TAXONOMY_SOURCE = ROOT / "skillmap" / "ml" / "data" / "powerSkills.json"
MODEL_VERSION = "skillmap-lite-1.0.0"
TAXONOMY_VERSION = "2026.07"

CATEGORY_DOMAIN = {
    "Computer Science & Engineering (CSE)": "Computer_Science_CSE",
    "Electronics & Communication (ECE)": "Electronics_Communication_ECE",
    "Electrical & Electronics (EEE)": "Electrical_Engineering_EEE",
    "Mechanical Engineering": "Mechanical_Engineering",
    "Civil Engineering": "Civil_Engineering",
    "Chemical Engineering": "Chemical_Engineering",
}
NON_TECH_DOMAIN = {
    "Healthcare Professionals": "Healthcare",
    "Teachers/Educators": "Education",
    "Chef/Culinary Professionals": "Culinary",
    "Creative/Design Roles": "Design_UX",
    "Business/Management Roles": "Project_Management",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _role_examples(key: str, taxonomy: dict[str, Any]) -> list[str]:
    ignored = {"core", "tools", "skills", "degrees", "software"}
    examples = [
        f"{name.replace('_', ' ').title()} Specialist"
        for name in taxonomy
        if name.lower() not in ignored
    ]
    return examples[:5] or [f"{domain_label(key)} Professional"]


def _dataset_counts() -> tuple[Counter[str], dict[str, Counter[str]]]:
    counts: Counter[str] = Counter()
    roles: dict[str, Counter[str]] = {}
    path = ROOT / "Resume.csv"
    if not path.exists():
        return counts, roles
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = CATEGORY_DOMAIN.get(row.get("Category", ""))
            if key is None:
                key = NON_TECH_DOMAIN.get(row.get("Sub_domain", ""))
            if key is None:
                continue
            counts[key] += 1
            roles.setdefault(key, Counter())[row.get("Sub_domain", "")] += 1
    return counts, roles


def export_runtime_artifacts() -> None:
    taxonomy = json.loads(TAXONOMY_SOURCE.read_text(encoding="utf-8"))
    all_skills = sorted({skill for value in taxonomy.values() for skill in flatten_taxonomy(value)})
    samples: list[str] = []
    labels: list[str] = []
    for key, value in taxonomy.items():
        for skill in flatten_taxonomy(value):
            samples.append(f"{domain_label(key)} {skill}")
            labels.append(key)

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        sublinear_tf=True,
        max_features=8_000,
    ).fit(all_skills + samples)
    classifier = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    sublinear_tf=True,
                    max_features=8_000,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1_000,
                    random_state=42,
                ),
            ),
        ]
    ).fit(samples, labels)

    counts, dataset_roles = _dataset_counts()
    catalog = []
    for index, (key, value) in enumerate(taxonomy.items()):
        role_names = [name for name, _ in dataset_roles.get(key, Counter()).most_common(5)]
        catalog.append(
            {
                "id": index,
                "name": domain_label(key),
                "domain_label": domain_label(key),
                "resume_count": counts[key],
                "top_skills": flatten_taxonomy(value)[:8],
                "example_roles": role_names or _role_examples(key, value),
                "avg_confidence": 0.0,
            }
        )

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TAXONOMY_SOURCE, RUNTIME_DIR / "skill_taxonomy.json")
    (RUNTIME_DIR / "cluster_catalog.json").write_text(
        json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    joblib.dump(vectorizer, RUNTIME_DIR / "vectorizer.joblib", compress=3)
    joblib.dump(classifier, RUNTIME_DIR / "classifier.joblib", compress=3)

    artifact_names = [
        "skill_taxonomy.json",
        "cluster_catalog.json",
        "vectorizer.joblib",
        "classifier.joblib",
    ]
    manifest = {
        "model_version": MODEL_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "scoring_modes": ["taxonomy", "lexical"],
        "artifacts": {name: _sha256(RUNTIME_DIR / name) for name in artifact_names},
    }
    (RUNTIME_DIR / "model_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Exported compact runtime artifacts to {RUNTIME_DIR}")


def train_full_models() -> None:
    """Train optional transformer/UMAP/HDBSCAN artifacts for local full mode."""

    try:
        import pandas as pd
        from sentence_transformers import SentenceTransformer

        from skillmap.ml.clusterer import (
            build_cluster_pipeline,
            label_clusters,
            save_cluster_models,
        )
        from skillmap.ml.extractors import clean_text
        from skillmap.ml.skills import extract_skill_names
    except ImportError as exc:
        raise SystemExit(
            "Full training dependencies are missing. Install requirements-ml.in."
        ) from exc

    frame = pd.read_csv(ROOT / "Resume.csv")
    if "ID" in frame.columns:
        frame = frame.rename(columns={"ID": "resume_id"})
    skill_lists: list[list[str]] = []
    inputs: list[str] = []
    for _, row in frame.iterrows():
        cleaned = clean_text(str(row.get("Resume_str", "")))
        skills = extract_skill_names(cleaned, max_skills=25)
        skill_lists.append(skills)
        inputs.append(" ".join(skills) or cleaned)
    semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
    full_model_path = MODEL_DIR / "full" / "all-MiniLM-L6-v2"
    semantic_model.save(str(full_model_path))
    embeddings = semantic_model.encode(
        inputs,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    result = build_cluster_pipeline(embeddings)
    names = label_clusters(result["labels"], skill_lists)
    save_cluster_models(result, names)
    frame["cluster_id"] = result["labels"]
    frame["cluster_name"] = [names.get(cid, "Noise") for cid in result["labels"]]
    frame[["resume_id", "cluster_id", "cluster_name"]].to_csv(
        MODEL_DIR / "cluster_results.csv", index=False
    )
    export_runtime_artifacts()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full",
        action="store_true",
        help="Train optional transformer and clustering artifacts before export.",
    )
    args = parser.parse_args()
    train_full_models() if args.full else export_runtime_artifacts()
