"""Aggregate comparable metrics without treating smoke data as real accuracy."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from training.common import ROOT, load_config, read_jsonl, write_json
from training.modeling import candidate_dir


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def run(config: dict[str, Any]) -> dict[str, Any]:
    candidate = candidate_dir(config)
    skill = _load(candidate / "skill_extractor/evaluation.json")
    occupation = _load(candidate / "occupation/evaluation.json")
    matcher = _load(candidate / "matcher/evaluation.json")
    reranker = _load(candidate / "reranker/evaluation.json")
    calibration = _load(candidate / "calibrators/evaluation.json")
    seniority = _load(ROOT / "reports/seniority_evaluation.json")
    runtime = _load(ROOT / "reports/runtime_validation.json")
    gold = read_jsonl("data/evaluation/gold_test.jsonl")
    scope = "real_gold" if gold else "synthetic_smoke_only"
    report = {
        "evaluation_scope": scope,
        "real_gold_test_count": len(gold),
        "promotion_eligible": bool(gold),
        "skill_extraction": skill,
        "occupation": occupation,
        "matching": matcher,
        "reranker": reranker,
        "calibration": calibration,
        "seniority": {
            **seniority,
            "status": "synthetic_smoke_only" if seniority else "no_gold_labels",
        },
        "fairness": {"status": "counterfactual_tests_only; no demographic outcome evaluation"},
        "warning": "Synthetic smoke metrics test mechanics and must not be described as real-world accuracy."
        if not gold
        else None,
    }
    write_json("reports/evaluation_metrics.json", report)
    write_json(candidate / "evaluation_summary.json", report)

    rows = [
        {
            "model": "current_baseline",
            "skill_f1": "not measured on real gold",
            "occupation_macro_f1": "not measured on real gold",
            "seniority_macro_f1": "not measured on real gold",
            "recall_at_10": "not measured on real gold",
            "ndcg_at_10": "not measured on real gold",
            "mrr": "not measured on real gold",
            "calibration_error": "not calibrated to hiring outcomes",
            "peak_memory_mb": runtime.get("peak_process_memory_mb", "not measured"),
            "p95_latency_ms": runtime.get("p95_latency_ms", "not measured"),
            "artifact_size_bytes": runtime.get("artifact_size_bytes", "not measured"),
        },
        {
            "model": "strong_lexical_baseline_synthetic_smoke",
            "skill_f1": skill.get("metrics", {}).get("entity_f1"),
            "occupation_macro_f1": occupation.get("metrics", {}).get("macro_f1"),
            "seniority_macro_f1": "not measured",
            "recall_at_10": reranker.get("ranking", {}).get("recall@10"),
            "ndcg_at_10": reranker.get("ranking", {}).get("ndcg@10"),
            "mrr": reranker.get("ranking", {}).get("mrr"),
            "calibration_error": calibration.get("after", {}).get("expected_calibration_error"),
            "peak_memory_mb": "not production-benchmarked",
            "p95_latency_ms": "not production-benchmarked",
            "artifact_size_bytes": "not production-benchmarked",
        },
        {
            "model": "best_teacher_model",
            **{key: "not executed" for key in rows_metric_fields()},
        },
        {
            "model": "best_compact_student",
            **{key: "not executed" for key in rows_metric_fields()},
        },
        {
            "model": "quantized_production_model",
            **{key: "not exported; promotion gates failed" for key in rows_metric_fields()},
        },
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    target = ROOT / "reports/metric_comparison.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(buffer.getvalue(), encoding="utf-8")
    return report


def rows_metric_fields() -> tuple[str, ...]:
    return (
        "skill_f1",
        "occupation_macro_f1",
        "seniority_macro_f1",
        "recall_at_10",
        "ndcg_at_10",
        "mrr",
        "calibration_error",
        "peak_memory_mb",
        "p95_latency_ms",
        "artifact_size_bytes",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
