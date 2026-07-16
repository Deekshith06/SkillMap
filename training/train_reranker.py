"""Train an explainable compact feature reranker."""

from __future__ import annotations

import argparse
import json
from typing import Any

import joblib
from sklearn.linear_model import LogisticRegression, Ridge

from training.common import load_config, read_jsonl, write_json
from training.modeling import (
    FEATURE_NAMES,
    binary_labels,
    candidate_dir,
    classification_metrics,
    pair_features,
    ranking_metrics,
)


def run(config: dict[str, Any]) -> dict[str, Any]:
    train = read_jsonl("data/processed/train.jsonl")
    test = read_jsonl("data/processed/test.jsonl")
    labels = binary_labels(train)
    if len(set(labels)) < 2:
        raise ValueError("reranker needs positive and negative training examples")
    model = LogisticRegression(
        class_weight="balanced", max_iter=1000, random_state=int(config.get("seed", 42))
    )
    model.fit(pair_features(train), labels)
    target = candidate_dir(config) / "reranker"
    target.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, target / "model.joblib", compress=3)
    scores = list(model.predict_proba(pair_features(test))[:, 1]) if test else []
    result = {
        "model": "logistic_feature_reranker",
        "feature_names": FEATURE_NAMES,
        "coefficients": dict(zip(FEATURE_NAMES, map(float, model.coef_[0]), strict=True)),
        "classification": classification_metrics(binary_labels(test), scores) if test else {},
        "ranking": ranking_metrics(test, scores) if test else {},
        "test_records": len(test),
        "evaluation_scope": "synthetic_smoke" if config["mode"] == "smoke" else "configured_split",
    }
    reranker_kind = str(config.get("models", {}).get("reranker", ""))
    if config["mode"] != "smoke" and "cross_encoder" in reranker_kind:
        from training.neural import train_cross_encoder_teacher

        teacher_name = str(
            config.get("models", {}).get("teacher_reranker", "cross-encoder/ms-marco-MiniLM-L6-v2")
        )
        teacher_train, teacher_test = train_cross_encoder_teacher(
            teacher_name,
            train,
            test,
            target / "teacher",
            config,
        )
        student = Ridge(alpha=1.0)
        student.fit(pair_features(train), teacher_train)
        joblib.dump(student, target / "distilled_student.joblib", compress=3)
        student_scores = [
            max(0.0, min(1.0, float(value))) for value in student.predict(pair_features(test))
        ]
        result["teacher"] = {
            "model": teacher_name,
            "classification": classification_metrics(binary_labels(test), teacher_test),
            "ranking": ranking_metrics(test, teacher_test),
        }
        result["distilled_student"] = {
            "model": "ridge_feature_student",
            "classification": classification_metrics(binary_labels(test), student_scores),
            "ranking": ranking_metrics(test, student_scores),
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
