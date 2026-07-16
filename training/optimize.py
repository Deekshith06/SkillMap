"""Controlled validation-only random search for the compact reranker."""

from __future__ import annotations

import argparse
import json
import random
from typing import Any, cast

from sklearn.linear_model import LogisticRegression

from training.common import load_config, read_jsonl, write_json
from training.modeling import binary_labels, classification_metrics, pair_features


def run(config: dict[str, Any]) -> dict[str, Any]:
    train = read_jsonl("data/processed/train.jsonl")
    validation = read_jsonl("data/processed/validation.jsonl")
    trials = min(int(config.get("training", {}).get("trials", 4)), 40)
    rng = random.Random(int(config.get("seed", 42)))  # nosec B311
    candidates = [10 ** rng.uniform(-2, 2) for _ in range(max(1, trials))]
    results: list[dict[str, Any]] = []
    for c_value in candidates:
        model = LogisticRegression(
            C=c_value,
            class_weight="balanced",
            max_iter=1000,
            random_state=int(config.get("seed", 42)),
        )
        model.fit(pair_features(train), binary_labels(train))
        scores = list(model.predict_proba(pair_features(validation))[:, 1]) if validation else []
        metrics = classification_metrics(binary_labels(validation), scores) if validation else {}
        results.append({"C": c_value, "validation": metrics})
    best = max(
        results,
        key=lambda row: float(cast(dict[str, float], row["validation"]).get("f1", 0)),
    )
    report = {"objective": "validation_f1", "trials": results, "best": best, "test_set_used": False}
    write_json("reports/hyperparameter_search.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
