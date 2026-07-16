"""Feature ablations evaluated on validation only."""

from __future__ import annotations

import argparse
import csv
import io
import json
from typing import Any

from sklearn.linear_model import LogisticRegression

from training.common import ROOT, load_config, read_jsonl
from training.modeling import FEATURE_NAMES, binary_labels, classification_metrics, pair_features


def run(config: dict[str, Any]) -> dict[str, Any]:
    train = read_jsonl("data/processed/train.jsonl")
    validation = read_jsonl("data/processed/validation.jsonl")
    x_train, x_validation = pair_features(train), pair_features(validation)
    rows: list[dict[str, Any]] = []
    for dropped in [None, *FEATURE_NAMES]:
        keep = [index for index, name in enumerate(FEATURE_NAMES) if name != dropped]
        model = LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=int(config.get("seed", 42))
        )
        model.fit([[row[index] for index in keep] for row in x_train], binary_labels(train))
        scores = (
            list(
                model.predict_proba([[row[index] for index in keep] for row in x_validation])[:, 1]
            )
            if validation
            else []
        )
        metrics = classification_metrics(binary_labels(validation), scores) if validation else {}
        rows.append({"ablation": f"without_{dropped}" if dropped else "all_features", **metrics})
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    target = ROOT / "reports/ablation_results.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(buffer.getvalue(), encoding="utf-8")
    best = max(rows, key=lambda row: float(row.get("f1", 0)))
    summary = (
        "# Ablation summary\n\n"
        f"Scope: {'synthetic smoke validation' if config['mode'] == 'smoke' else 'configured validation split'}.\n\n"
        f"Best validation configuration: `{best['ablation']}` with F1 `{best.get('f1', 0):.4f}`. "
        "This is not real-world test evidence and cannot justify production promotion.\n"
    )
    (ROOT / "reports/ablation_summary.md").write_text(summary, encoding="utf-8")
    return {"rows": len(rows), "best": best, "test_set_used": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
