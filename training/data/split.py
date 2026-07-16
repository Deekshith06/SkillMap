"""Deterministic group-aware split creation and leakage checks."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from typing import Any

from training.common import load_config, read_jsonl, write_json, write_jsonl


def _bucket(group: str, seed: int, split: dict[str, float]) -> str:
    value = int(hashlib.sha256(f"{seed}:{group}".encode()).hexdigest()[:16], 16) / 2**64
    if value < split["train"]:
        return "train"
    if value < split["train"] + split["validation"]:
        return "validation"
    return "test"


def grouped_split(
    rows: list[dict[str, Any]], split: dict[str, float], seed: int
) -> dict[str, list[dict[str, Any]]]:
    if abs(sum(split.values()) - 1) > 1e-9:
        raise ValueError("split proportions must sum to one")
    result: dict[str, list[dict[str, Any]]] = {"train": [], "validation": [], "test": []}
    assignments: dict[str, str] = {}
    for row in rows:
        group = str(row["group_id"])
        assignments.setdefault(group, _bucket(group, seed, split))
        result[assignments[group]].append(row)
    return result


def run(config: dict[str, Any]) -> dict[str, Any]:
    pairs = read_jsonl("data/synthetic/matching_pairs.jsonl")
    splits = grouped_split(pairs, config["split"], int(config.get("seed", 42)))
    for name, rows in splits.items():
        write_jsonl(f"data/processed/{name}.jsonl", rows)
    challenge_names = (
        "standard_test",
        "unseen_occupation_test",
        "long_resume_test",
        "short_resume_test",
        "noisy_text_test",
        "format_variation_test",
        "skill_alias_test",
        "hard_negative_test",
        "cross_domain_test",
        "calibration_test",
    )
    test = splits["test"]
    for name in challenge_names:
        rows = test
        if name == "hard_negative_test":
            rows = [row for row in test if row.get("hard_negative")]
        elif name == "calibration_test":
            rows = splits["validation"]
        write_jsonl(f"data/evaluation/{name}.jsonl", rows)

    memberships: dict[str, set[str]] = defaultdict(set)
    ids: dict[str, set[str]] = defaultdict(set)
    for split_name, rows in splits.items():
        for row in rows:
            memberships[row["group_id"]].add(split_name)
            ids[split_name].update((row["resume_id"], row["job_id"]))
    group_leaks = {group: sorted(value) for group, value in memberships.items() if len(value) > 1}
    document_leaks = {
        f"{left}-{right}": sorted(ids[left] & ids[right])
        for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))
        if ids[left] & ids[right]
    }
    report = {
        "counts": {name: len(rows) for name, rows in splits.items()},
        "synthetic_counts": {
            name: sum(bool(row.get("synthetic")) for row in rows) for name, rows in splits.items()
        },
        "real_gold_test_count": len(read_jsonl("data/evaluation/gold_test.jsonl")),
        "group_leaks": group_leaks,
        "document_leaks": document_leaks,
        "passed": not group_leaks and not document_leaks,
        "note": "Synthetic test rows validate pipeline mechanics only and are not a production accuracy test.",
    }
    write_json("reports/data_leakage_report.json", report)
    if not report["passed"]:
        raise ValueError("split leakage detected")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
