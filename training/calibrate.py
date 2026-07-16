"""Fit validation-only score calibration for the compact reranker."""

from __future__ import annotations

import argparse
import json
from typing import Any

import joblib
from sklearn.isotonic import IsotonicRegression

from training.common import load_config, read_jsonl, write_json
from training.modeling import binary_labels, calibration_metrics, candidate_dir, pair_features


def run(config: dict[str, Any]) -> dict[str, Any]:
    validation = read_jsonl("data/processed/validation.jsonl")
    target = candidate_dir(config)
    reranker = joblib.load(target / "reranker/model.joblib")
    truth = binary_labels(validation)
    raw = list(reranker.predict_proba(pair_features(validation))[:, 1]) if validation else []
    if len(set(truth)) < 2:
        result = {
            "status": "skipped",
            "reason": "validation split needs positive and negative labels",
            "before": calibration_metrics(truth, raw),
        }
    else:
        calibrator = IsotonicRegression(out_of_bounds="clip")
        calibrated = list(calibrator.fit_transform(raw, truth))
        output = target / "calibrators"
        output.mkdir(parents=True, exist_ok=True)
        joblib.dump(calibrator, output / "isotonic.joblib", compress=3)
        result = {
            "status": "trained",
            "method": "isotonic",
            "fit_scope": "validation_only",
            "before": calibration_metrics(truth, raw),
            "after": calibration_metrics(truth, calibrated),
        }
    write_json(target / "calibrators/evaluation.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
