"""Train a compact TF-IDF occupation baseline from grouped split records."""

from __future__ import annotations

import argparse
import json
from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, top_k_accuracy_score
from sklearn.pipeline import Pipeline

from training.common import load_config, read_jsonl, write_json
from training.modeling import candidate_dir


def _unique_resumes(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    unique: dict[str, dict[str, str]] = {}
    for row in rows:
        unique.setdefault(
            row["resume_id"], {"text": row["resume_text"], "label": row["occupation"]}
        )
    return list(unique.values())


def run(config: dict[str, Any]) -> dict[str, Any]:
    train = _unique_resumes(read_jsonl("data/processed/train.jsonl"))
    test = _unique_resumes(read_jsonl("data/processed/test.jsonl"))
    if len({row["label"] for row in train}) < 2:
        result: dict[str, Any] = {
            "status": "skipped",
            "reason": "fewer than two training occupation classes",
        }
        write_json(candidate_dir(config) / "occupation/evaluation.json", result)
        return result
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced", max_iter=1000, random_state=int(config.get("seed", 42))
                ),
            ),
        ]
    )
    model.fit([row["text"] for row in train], [row["label"] for row in train])
    target = candidate_dir(config) / "occupation"
    target.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, target / "model.joblib", compress=3)
    if not test:
        result = {"status": "trained", "test_records": 0, "metrics": {}}
    else:
        truth = [row["label"] for row in test]
        prediction = model.predict([row["text"] for row in test])
        probability = model.predict_proba([row["text"] for row in test])
        classes = list(model.classes_)
        known = [index for index, label in enumerate(truth) if label in classes]
        known_truth = [truth[index] for index in known]
        known_probability = probability[known] if known else []
        metrics = {
            "macro_f1": float(f1_score(truth, prediction, average="macro", zero_division=0)),
            "weighted_f1": float(f1_score(truth, prediction, average="weighted", zero_division=0)),
            "top_1_accuracy": float(accuracy_score(truth, prediction)),
            "top_3_accuracy_known_classes": float(
                top_k_accuracy_score(
                    known_truth,
                    known_probability,
                    k=min(3, len(classes)),
                    labels=classes,
                )
            )
            if known
            else 0.0,
            "unseen_occupation_rate": 1 - len(known) / len(truth),
            "per_domain_recall": {
                label: sum(
                    expected == predicted_label == label
                    for expected, predicted_label in zip(truth, prediction, strict=True)
                )
                / sum(expected == label for expected in truth)
                for label in sorted(set(truth))
            },
        }
        result = {"status": "trained", "test_records": len(test), "metrics": metrics}
    result["evaluation_scope"] = (
        "synthetic_smoke" if config["mode"] == "smoke" else "configured_split"
    )
    write_json(target / "evaluation.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
