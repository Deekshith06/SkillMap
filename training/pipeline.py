"""Resumable end-to-end training orchestration."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from typing import Any

from training import (
    ablation,
    calibrate,
    error_analysis,
    evaluate_all,
    export_runtime,
    optimize,
    validate_runtime,
)
from training.common import ROOT, load_config, run_metadata, seed_everything, write_json
from training.data import audit, deduplicate, download_public, generate_synthetic, prepare, split
from training.data_generation import validate_generated_data
from training.train_canonicalizer import run as train_canonicalizer
from training.train_matcher import run as train_matcher
from training.train_occupation_classifier import run as train_occupation
from training.train_reranker import run as train_reranker
from training.train_seniority import run as train_seniority
from training.train_skill_extractor import run as train_skill_extractor


def run(config: dict[str, Any], *, force: bool = False) -> dict[str, Any]:
    seed_everything(int(config.get("seed", 42)))
    state_path = ROOT / "reports/runs" / config["name"] / "pipeline_state.json"
    state = (
        json.loads(state_path.read_text(encoding="utf-8"))
        if state_path.exists() and not force
        else {
            "metadata": run_metadata(config),
            "completed": {},
        }
    )
    stages: list[tuple[str, Callable[[], Any]]] = [("audit", audit.run)]
    if config.get("download_public"):
        stages.append(("download_public", download_public.run))
    if config.get("prepare_public"):
        stages.append(("prepare", prepare.run))
    stages.extend(
        [
            ("generate_synthetic", lambda: generate_synthetic.run(config)),
            ("validate_synthetic", validate_generated_data.run),
            ("deduplicate", lambda: deduplicate.run(config)),
            ("split", lambda: split.run(config)),
            ("train_skill_extractor", lambda: train_skill_extractor(config)),
            ("train_canonicalizer", lambda: train_canonicalizer(config)),
            ("train_occupation", lambda: train_occupation(config)),
            ("train_seniority", lambda: train_seniority(config)),
            ("train_matcher", lambda: train_matcher(config)),
            ("train_reranker", lambda: train_reranker(config)),
            ("optimize", lambda: optimize.run(config)),
            ("ablation", lambda: ablation.run(config)),
            ("calibrate", lambda: calibrate.run(config)),
            ("evaluate", lambda: evaluate_all.run(config)),
            ("error_analysis", lambda: error_analysis.run(config)),
            ("export_candidate", lambda: export_runtime.run(config)),
            ("validate_current_runtime", validate_runtime.run),
        ]
    )
    for name, action in stages:
        if config.get("resume") and name in state["completed"] and not force:
            continue
        state["completed"][name] = action()
        write_json(state_path, state)
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    result = run(load_config(args.config), force=args.force)
    print(json.dumps({"completed": list(result["completed"])}, indent=2))


if __name__ == "__main__":
    main()
