# Training

## Prediction and data contract

Goal: extract explicit occupational evidence and rank supplied resumes/jobs for human
review. The decision owner is a human reviewer; SkillMap must not reject candidates.
Primary metrics are entity F1 and bidirectional nDCG/Recall/MRR. Guardrails are
calibration, slice regressions, privacy, duplicate leakage, fairness, p95 latency, peak RAM,
artifact size, local-only startup, and explainability. False claims of suitability,
protected-attribute influence, train/test leakage, and silent scores without evidence are
unacceptable.

The canonical contracts live in `training/schemas.py`. A record carries immutable document
and family IDs, original text after PII masking, source dataset, official split when
provided, typed spans with offsets/evidence, taxonomy mappings, and a synthetic flag.
Matching pairs retain every component label and the label-generation method.

## Environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.in
python -m pip install -r requirements-ml.in
```

The `.yaml` files are JSON-compatible YAML so the pipeline can load them with the Python
standard library. MLflow is not required. Runs record the config hash, Git commit, Python
version, seed, stage results, and resumable state under `reports/runs/`.

## Public data

Review `docs/DATASETS.md` and the registry first. The ESCO download UI generates a package
URL; export English CSV from the official page and pass it without committing it:

```bash
export SKILLMAP_ESCO_URL='https://official-package-url-from-esco'
python -m training.data.download_public
python -m training.data.audit
python -m training.data.prepare
```

Downloads are extracted with path-traversal checks. The first download creates an
immutable receipt; a later hash change fails. SkillSpan is commit-pinned; for a permanent
reproducible release, copy each verified archive hash into the registry.
Model downloads are also pinned to explicit Hugging Face revisions in each non-smoke
configuration; update those pins deliberately after reviewing upstream changes.

## Pipeline commands

```bash
python -m training.data.generate_synthetic --config configs/training/accuracy_first.yaml
python -m training.data.deduplicate --config configs/training/accuracy_first.yaml
python -m training.data.split --config configs/training/accuracy_first.yaml
python -m training.train_skill_extractor --config configs/training/accuracy_first.yaml
python -m training.train_canonicalizer --config configs/training/accuracy_first.yaml
python -m training.train_occupation_classifier --config configs/training/accuracy_first.yaml
python -m training.train_seniority --config configs/training/accuracy_first.yaml
python -m training.train_matcher --config configs/training/accuracy_first.yaml
python -m training.train_reranker --config configs/training/accuracy_first.yaml
python -m training.optimize --config configs/training/accuracy_first.yaml
python -m training.calibrate --config configs/training/accuracy_first.yaml
python -m training.evaluate_all --config configs/training/accuracy_first.yaml
python -m training.error_analysis --config configs/training/accuracy_first.yaml
python -m training.export_runtime --config configs/training/accuracy_first.yaml
python -m training.validate_runtime
```

One resumable command runs the same code:

```bash
python -m training.pipeline --config configs/training/accuracy_first.yaml
```

Use `--force` only to rerun completed stages deliberately. `low_compute.yaml` targets an M2
MacBook Air with 16 GB RAM; `colab.yaml` enables GPU-sized batches; `smoke_test.yaml` is a
quick deterministic plumbing check.

The extraction lane compares longest-span taxonomy matching with separate SKILL and
KNOWLEDGE token-classification heads, preserving nested SkillSpan spans. The retrieval lane
trains symmetric resume/job triplets with hard negatives. The offline cross-encoder teacher
is distilled into a compact feature student. Only validation data controls HPO,
calibration, early stopping, thresholds, and selection.

Synthetic generation defaults to deterministic templates. `DATA_GENERATION_PROVIDER` also
accepts `ollama` and `openrouter`; provider clients reject any input not marked synthetic.
Never send a real resume to either provider. Generated records are schema-, taxonomy-,
PII-, duplicate-, and score-validated and are never real test data.

## Promotion

`training.export_runtime` always builds a candidate manifest and hashes. It cannot replace
`models/runtime/` without a non-empty immutable real gold test, fairness/robustness pass,
no critical slice regression, and runtime budget pass. Failed gates leave the current
runtime untouched. Full runs export a float ONNX and INT8 ONNX compact reranker for
comparison; the smallest artifact is eligible only after retained real-test performance is
measured.
