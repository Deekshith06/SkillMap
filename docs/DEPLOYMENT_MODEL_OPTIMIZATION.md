# Deployment model optimization

Render Free runs only the local lite backend; Vercel hosts the static Reflex frontend.
Training dependencies, datasets, checkpoints, and teacher models must never enter either
runtime image.

The candidate comparison order is full teacher, compact student, ONNX student, INT8 ONNX
student, then lexical fallback. Measure real-test entity F1 and nDCG/Recall/MRR alongside
startup, p95 latency, peak RAM, and artifact bytes. The configured 97% retention threshold
is a starting policy, not an automatic truth: critical domains and privacy/fairness gates
must not regress even when aggregate retention passes.

Full exports place float and INT8 ONNX rerankers in the candidate bundle. Promotion copies
only verified inference/preprocessing artifacts, manifest, taxonomy, calibrator, and
evaluation summary into `models/runtime/`. The backend verifies every listed SHA-256 before
deserializing. Lite mode must start offline and must not import Torch, Transformers, pandas,
UMAP, HDBSCAN, training CSVs, or downloaded taxonomies.

```bash
python -m training.export_runtime --config configs/training/accuracy_first.yaml
python -m training.validate_runtime
SKILLMAP_MODE=lite reflex run
```

Current status: the smoke candidate is `not_promoted` because no real gold or fairness
outcome evaluation exists. `skillmap-lite-1.0.0` remains the rollback artifact.
