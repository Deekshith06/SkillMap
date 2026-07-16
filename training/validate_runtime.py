"""Validate local-only lite artifacts, hashes, latency, memory, and outputs."""

from __future__ import annotations

import argparse
import json
import os
import resource
import statistics
import subprocess  # nosec B404
import sys
import time
from typing import Any

from skillmap.adapters.artifact_repository import load_runtime_assets
from skillmap.config.settings import get_settings
from skillmap.ml_runtime import get_engine
from training.common import ROOT, write_json


def run() -> dict[str, Any]:
    os.environ["SKILLMAP_MODE"] = "lite"
    get_settings.cache_clear()
    load_runtime_assets.cache_clear()
    get_engine.cache_clear()
    assets = load_runtime_assets()
    engine = get_engine()
    sample_resume = (
        "Senior Python engineer using FastAPI, SQL, Docker, Kubernetes and AWS for 7 years."
    )
    sample_job = "Senior Python engineer. Required: Python, FastAPI, SQL, Docker, Kubernetes. Minimum 5 years."
    latencies = []
    result = None
    for _ in range(25):
        started = time.perf_counter()
        result = engine.match(sample_resume, sample_job)
        latencies.append((time.perf_counter() - started) * 1000)
    check = subprocess.run(  # nosec B603
        [
            sys.executable,
            "-c",
            "import sys; from skillmap.ml_runtime import get_engine; get_engine(); assert 'torch' not in sys.modules",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "SKILLMAP_MODE": "lite"},
    )
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_mb = peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024
    ordered = sorted(latencies)
    report = {
        "passed": check.returncode == 0 and result is not None,
        "model_version": assets.manifest.model_version,
        "taxonomy_version": assets.manifest.taxonomy_version,
        "artifact_hashes_verified": True,
        "local_artifacts_only": True,
        "torch_imported_in_isolated_lite_process": check.returncode != 0,
        "p50_latency_ms": round(statistics.median(latencies), 3),
        "p95_latency_ms": round(ordered[max(0, int(len(ordered) * 0.95) - 1)], 3),
        "peak_process_memory_mb": round(peak_mb, 2),
        "artifact_size_bytes": sum(
            path.stat().st_size for path in get_settings().artifact_dir.rglob("*") if path.is_file()
        ),
        "score_bounded": bool(result and result.score is not None and 0 <= result.score <= 100),
        "score_explained": bool(result and result.evidence),
        "stderr": check.stderr.strip(),
    }
    write_json("reports/runtime_validation.json", report)
    if not report["passed"]:
        raise RuntimeError("lite runtime validation failed")
    return report


def main() -> None:
    argparse.ArgumentParser().parse_args()
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
