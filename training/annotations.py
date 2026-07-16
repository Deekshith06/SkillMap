"""Two-annotator agreement and adjudication helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any

from training.common import read_jsonl, write_jsonl


def agreement(left_path: str, right_path: str, label_field: str = "label") -> dict[str, float]:
    left = {row["annotation_id"]: row[label_field] for row in read_jsonl(left_path)}
    right = {row["annotation_id"]: row[label_field] for row in read_jsonl(right_path)}
    shared = sorted(left.keys() & right.keys())
    observed = sum(left[key] == right[key] for key in shared) / max(len(shared), 1)
    left_counts, right_counts = (
        Counter(left[key] for key in shared),
        Counter(right[key] for key in shared),
    )
    labels = set(left_counts) | set(right_counts)
    expected = sum(
        left_counts[label] / max(len(shared), 1) * right_counts[label] / max(len(shared), 1)
        for label in labels
    )
    kappa = (observed - expected) / (1 - expected) if expected < 1 else 1.0
    return {"records": float(len(shared)), "observed_agreement": observed, "cohen_kappa": kappa}


def merge(
    left_path: str, right_path: str, adjudicated_path: str | None, output_path: str
) -> list[dict[str, Any]]:
    left = {row["annotation_id"]: row for row in read_jsonl(left_path)}
    right = {row["annotation_id"]: row for row in read_jsonl(right_path)}
    adjudicated = (
        {row["annotation_id"]: row for row in read_jsonl(adjudicated_path)}
        if adjudicated_path
        else {}
    )
    merged = []
    for key in sorted(left.keys() & right.keys()):
        if left[key].get("label") == right[key].get("label"):
            merged.append({**left[key], "adjudication": "annotator_agreement"})
        elif key in adjudicated:
            merged.append({**adjudicated[key], "adjudication": "independent_adjudicator"})
    write_jsonl(output_path, merged)
    return merged
