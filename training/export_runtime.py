"""Package candidates and promote only after real-data acceptance gates pass."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from training.common import ROOT, git_commit, load_config, sha256, write_json
from training.modeling import candidate_dir


def _artifact_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "model_manifest.json"
    }


def run(config: dict[str, Any]) -> dict[str, Any]:
    candidate = candidate_dir(config)
    evaluation_path = ROOT / "reports/evaluation_metrics.json"
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    gates = config["promotion_gates"]
    failures = []
    if gates.get("requires_real_gold_test") and not evaluation.get("real_gold_test_count"):
        failures.append("no immutable real gold test evaluation")
    if (
        gates.get("requires_fairness_pass")
        and evaluation.get("fairness", {}).get("status") != "passed"
    ):
        failures.append("fairness outcome evaluation not passed")
    promotion_status = "eligible" if not failures else "not_promoted"
    onnx_exports: list[str] = []
    if config["mode"] != "smoke":
        import joblib
        from onnxruntime.quantization import QuantType, quantize_dynamic
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType

        reranker = joblib.load(candidate / "reranker/model.joblib")
        onnx_dir = candidate / "reranker/onnx"
        onnx_dir.mkdir(parents=True, exist_ok=True)
        model_path = onnx_dir / "model.onnx"
        model_path.write_bytes(
            convert_sklearn(
                reranker,
                initial_types=[("features", FloatTensorType([None, 5]))],
                target_opset=17,
            ).SerializeToString()
        )
        quantized_path = onnx_dir / "model.int8.onnx"
        quantize_dynamic(model_path, quantized_path, weight_type=QuantType.QInt8)
        onnx_exports = [
            str(model_path.relative_to(candidate)),
            str(quantized_path.relative_to(candidate)),
        ]
    manifest = {
        "model_name": f"skillmap-{config['name']}",
        "model_version": "0.1.0-candidate",
        "created_at": datetime.now(UTC).isoformat(),
        "training_code_commit": git_commit(),
        "datasets": ["skillmap_template_synthetic"] if config["mode"] == "smoke" else [],
        "taxonomy_versions": {
            "ESCO": "1.2.1 configured; not present in smoke artifacts",
            "O*NET": "30.3 configured; not present in smoke artifacts",
        },
        "tasks": [
            "skill_extraction",
            "canonicalization",
            "occupation",
            "matching",
            "reranking",
            "calibration",
        ],
        "metrics": evaluation,
        "thresholds": gates,
        "runtime": "scikit-learn candidate; current production remains skillmap-lite-1.0.0",
        "quantization": "none",
        "artifact_hashes": {},
        "known_limitations": failures,
        "promotion_status": promotion_status,
    }
    manifest["artifact_hashes"] = _artifact_hashes(candidate)
    write_json(candidate / "model_manifest.json", manifest)
    result = {
        "candidate_dir": str(candidate.relative_to(ROOT)),
        "promotion_status": promotion_status,
        "failed_gates": failures,
        "production_runtime_changed": False,
        "onnx_exports": onnx_exports,
    }
    write_json("reports/export_report.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
