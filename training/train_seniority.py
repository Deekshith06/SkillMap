"""Evaluate deterministic seniority constraints on available labels."""

from __future__ import annotations

import argparse
import json
from typing import Any

from skillmap.ml_runtime.lite_engine import LiteEngine
from training.common import load_config, read_jsonl, write_json

ORDER = ["Intern", "Entry level", "Junior", "Mid-level", "Senior", "Lead", "Manager", "Director"]


def _coarse(value: str) -> int | None:
    lowered = value.lower()
    for index, label in enumerate(ORDER):
        if label.lower() in lowered:
            return index
    if "entry" in lowered:
        return 1
    return None


def run(config: dict[str, Any]) -> dict[str, Any]:
    profiles = read_jsonl("data/synthetic/profiles.jsonl")
    engine = LiteEngine()
    expected, predicted = [], []
    for row in profiles:
        left, right = _coarse(row.get("seniority", "")), _coarse(engine._seniority(row["text"]))
        if left is not None and right is not None:
            expected.append(left)
            predicted.append(right)
    exact = sum(a == b for a, b in zip(expected, predicted, strict=True)) / max(len(expected), 1)
    adjacent = sum(abs(a - b) <= 1 for a, b in zip(expected, predicted, strict=True)) / max(
        len(expected), 1
    )
    report = {
        "records": len(expected),
        "exact_accuracy": exact,
        "adjacent_level_accuracy": adjacent,
        "macro_f1": None,
        "evaluation_scope": "synthetic_smoke",
    }
    write_json("reports/seniority_evaluation.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
