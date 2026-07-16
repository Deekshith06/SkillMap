"""Create machine-readable and HTML error slices from candidate predictions."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from typing import Any

import joblib

from training.common import ROOT, load_config, read_jsonl, write_json, write_jsonl
from training.modeling import binary_labels, candidate_dir, pair_features


def run(config: dict[str, Any]) -> dict[str, Any]:
    rows = read_jsonl("data/processed/test.jsonl")
    model = joblib.load(candidate_dir(config) / "reranker/model.joblib")
    scores = list(model.predict_proba(pair_features(rows))[:, 1]) if rows else []
    errors: list[dict[str, Any]] = []
    for row, truth, score in zip(rows, binary_labels(rows), scores, strict=True):
        predicted = int(score >= 0.5)
        if predicted != truth:
            errors.append(
                {
                    "example_id": row["pair_id"],
                    "occupation": row["occupation"],
                    "expected": truth,
                    "predicted": predicted,
                    "confidence": round(abs(score - 0.5) * 2, 4),
                    "likely_cause": "feature threshold or synthetic rubric boundary",
                    "recommended_correction": "review label and add adjudicated evidence",
                    "synthetic": row.get("synthetic", False),
                }
            )
    write_jsonl(
        "reports/worst_predictions.jsonl", sorted(errors, key=lambda row: -row["confidence"])
    )
    counts = Counter(row["occupation"] for row in errors)
    report = {
        "total_test_records": len(rows),
        "errors": len(errors),
        "by_occupation": dict(counts),
        "evaluation_scope": "synthetic_smoke" if config["mode"] == "smoke" else "configured_split",
    }
    write_json("reports/confusion_matrices/matching.json", report)
    table = "".join(
        f"<tr><td>{html.escape(str(row['example_id']))}</td><td>{html.escape(str(row['occupation']))}</td>"
        f"<td>{row['expected']}</td><td>{row['predicted']}</td><td>{row['confidence']:.3f}</td></tr>"
        for row in errors[:100]
    )
    page = (
        "<!doctype html><meta charset='utf-8'><title>SkillMap error analysis</title>"
        "<h1>SkillMap error analysis</h1>"
        f"<p>Scope: {html.escape(str(report['evaluation_scope']))}. Errors: {len(errors)} / {len(rows)}.</p>"
        "<table><thead><tr><th>ID</th><th>Occupation</th><th>Expected</th><th>Predicted</th><th>Confidence</th></tr></thead>"
        f"<tbody>{table}</tbody></table>"
    )
    target = ROOT / "reports/error_analysis.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
