"""Shared compact-model features, metrics, and candidate artifact paths."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from training.common import ROOT

FEATURE_NAMES = (
    "required_skills",
    "preferred_skills",
    "experience",
    "occupation_alignment",
    "critical_missing",
)


def candidate_dir(config: dict[str, Any]) -> Path:
    path = ROOT / "models/candidates" / str(config["name"])
    path.mkdir(parents=True, exist_ok=True)
    return path


def pair_features(rows: Iterable[dict[str, Any]]) -> list[list[float]]:
    return [
        [float(row.get("component_labels", {}).get(name, 0.0)) for name in FEATURE_NAMES]
        for row in rows
    ]


def binary_labels(rows: Iterable[dict[str, Any]]) -> list[int]:
    return [int(row["label"] in {"STRONG_MATCH", "POTENTIAL_MATCH"}) for row in rows]


def classification_metrics(
    y_true: list[int], scores: list[float], threshold: float = 0.5
) -> dict[str, float]:
    predicted = [int(score >= threshold) for score in scores]
    tp = sum(a == b == 1 for a, b in zip(y_true, predicted, strict=True))
    tn = sum(a == b == 0 for a, b in zip(y_true, predicted, strict=True))
    fp = sum(a == 0 and b == 1 for a, b in zip(y_true, predicted, strict=True))
    fn = sum(a == 1 and b == 0 for a, b in zip(y_true, predicted, strict=True))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": (tp + tn) / max(len(y_true), 1),
        "tp": float(tp),
        "tn": float(tn),
        "fp": float(fp),
        "fn": float(fn),
    }


def calibration_metrics(
    y_true: list[int], probabilities: list[float], bins: int = 10
) -> dict[str, float]:
    if not y_true:
        return {"brier_score": 0.0, "expected_calibration_error": 0.0}
    brier = sum(
        (truth - probability) ** 2 for truth, probability in zip(y_true, probabilities, strict=True)
    ) / len(y_true)
    ece = 0.0
    for index in range(bins):
        lower, upper = index / bins, (index + 1) / bins
        members = [
            position
            for position, value in enumerate(probabilities)
            if lower <= value < upper or (index == bins - 1 and value == 1)
        ]
        if not members:
            continue
        confidence = sum(probabilities[position] for position in members) / len(members)
        accuracy = sum(y_true[position] for position in members) / len(members)
        ece += len(members) / len(y_true) * abs(confidence - accuracy)
    return {"brier_score": brier, "expected_calibration_error": ece}


def ranking_metrics(
    rows: list[dict[str, Any]], scores: list[float], ks: tuple[int, ...] = (1, 5, 10)
) -> dict[str, float]:
    groups: dict[str, list[tuple[float, int]]] = defaultdict(list)
    for row, score in zip(rows, scores, strict=True):
        groups[row["resume_id"]].append((score, int(row["label"] != "NOT_MATCH")))
    reciprocal, average_precision = [], []
    recall: dict[int, list[float]] = {k: [] for k in ks}
    ndcg: dict[int, list[float]] = {k: [] for k in ks}
    for candidates in groups.values():
        ordered = sorted(candidates, reverse=True)
        relevant = sum(label for _, label in ordered)
        ranks = [index for index, (_, label) in enumerate(ordered, 1) if label]
        reciprocal.append(1 / ranks[0] if ranks else 0.0)
        average_precision.append(
            sum(sum(label for _, label in ordered[:rank]) / rank for rank in ranks)
            / max(relevant, 1)
        )
        for k in ks:
            recall[k].append(sum(label for _, label in ordered[:k]) / max(relevant, 1))
            dcg = sum(
                label / math.log2(index + 1) for index, (_, label) in enumerate(ordered[:k], 1)
            )
            ideal = sum(1 / math.log2(index + 1) for index in range(1, min(relevant, k) + 1))
            ndcg[k].append(dcg / ideal if ideal else 0.0)
    result = {
        "mrr": sum(reciprocal) / max(len(reciprocal), 1),
        "map": sum(average_precision) / max(len(average_precision), 1),
    }
    result.update(
        {f"recall@{k}": sum(values) / max(len(values), 1) for k, values in recall.items()}
    )
    result.update({f"ndcg@{k}": sum(values) / max(len(values), 1) for k, values in ndcg.items()})
    return result


def entity_metrics(
    gold: list[set[tuple[int, int, str]]], predicted: list[set[tuple[int, int, str]]]
) -> dict[str, float]:
    tp = sum(len(left & right) for left, right in zip(gold, predicted, strict=True))
    fp = sum(len(right - left) for left, right in zip(gold, predicted, strict=True))
    fn = sum(len(left - right) for left, right in zip(gold, predicted, strict=True))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "entity_precision": precision,
        "entity_recall": recall,
        "entity_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "true_positives": float(tp),
        "false_positives": float(fp),
        "false_negatives": float(fn),
    }
