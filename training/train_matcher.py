"""Train and evaluate the fast retrieval baseline."""

from __future__ import annotations

import argparse
import json
from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

from training.common import load_config, read_jsonl, write_json
from training.modeling import candidate_dir, ranking_metrics


def _scores(vectorizer: TfidfVectorizer, rows: list[dict[str, Any]]) -> list[float]:
    if not rows:
        return []
    resume = vectorizer.transform([row["resume_text"] for row in rows])
    jobs = vectorizer.transform([row["job_text"] for row in rows])
    return [float(resume[index].multiply(jobs[index]).sum()) for index in range(len(rows))]


def run(config: dict[str, Any]) -> dict[str, Any]:
    train = read_jsonl("data/processed/train.jsonl")
    test = read_jsonl("data/processed/test.jsonl")
    if not train:
        raise ValueError("training split is empty")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, max_features=50_000)
    vectorizer.fit([text for row in train for text in (row["resume_text"], row["job_text"])])
    target = candidate_dir(config) / "matcher"
    target.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, target / "tfidf_vectorizer.joblib", compress=3)
    scores = _scores(vectorizer, test)
    requested = config.get("models", {}).get("matcher_candidates", [])
    executed = []
    if config["mode"] != "smoke" and requested:
        from training.neural import train_biencoder

        for model_name in requested:
            metrics = train_biencoder(
                model_name,
                train,
                test,
                target / model_name.replace("/", "--"),
                config,
            )
            executed.append({"model": model_name, "metrics": metrics})
    result = {
        "model": "tfidf_cosine",
        "metrics": ranking_metrics(test, scores) if test else {},
        "test_records": len(test),
        "evaluation_scope": "synthetic_smoke" if config["mode"] == "smoke" else "configured_split",
        "requested_neural_candidates": requested,
        "executed_neural_candidates": executed,
        "best_neural_candidate": max(
            executed, key=lambda row: row["metrics"].get("ndcg@10", 0), default=None
        ),
    }
    write_json(target / "evaluation.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
