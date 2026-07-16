# Evaluation

## Current measured results

The 2026-07-17 smoke run completed on 32 deterministic profiles, 64 jobs, and 64 matching
pairs (32 hard negatives). All 12 test pairs and all four validation pairs are synthetic.
There are zero real gold test records. These values test code paths and must not be reported
as real-world accuracy.

| Metric | Smoke candidate | Scope |
| --- | ---: | --- |
| Exact entity F1 | 0.9769 | Synthetic spans only |
| Entity precision / recall | 0.9645 / 0.9896 | Synthetic spans only |
| Occupation macro F1 | 0.0909 | Synthetic; 83.33% occupations unseen in training |
| Occupation top-1 | 0.1667 | Synthetic |
| TF-IDF Recall@10 / nDCG@10 / MRR | 1.0 / 1.0 / 1.0 | Trivial synthetic positive/hard-negative groups |
| Reranker F1 / nDCG@10 / MRR | 1.0 / 1.0 / 1.0 | Labels generated from the same transparent components |
| Calibration ECE / Brier | 0.0 / 0.0 | Four synthetic validation pairs; not outcome calibration |

The poor occupation result is retained rather than hidden. The perfect synthetic ranking
and calibration values are expected from separable template pairs and are not evidence of
employment validity. No teacher, student transformer, ONNX, real-domain, or demographic
outcome benchmark was executed in this environment.

## Retained production runtime

The existing `skillmap-lite-1.0.0` runtime remains active. In the same run, 25 local match
calls measured 2.842 ms median and 2.931 ms p95 latency, 118.58 MB peak process memory, and
206,304 bytes of runtime artifacts. Checksums passed; an isolated lite process did not
import Torch; artifacts loaded locally; explanations and score bounds passed.

This is a process-level memory reading, not incremental model RSS. Hardware and concurrent
load will change latency/memory. Real extraction F1, occupation/seniority F1, ranking,
calibration, cross-domain robustness, and demographic fairness remain unmeasured for the
production runtime.

## Required real evaluation

Before promotion, report exact and partial entity F1 per type; hard/soft/knowledge and rare
span results; occupation macro/weighted F1 and top-1/top-3; seniority macro F1 and adjacent
accuracy; symmetric Recall@1/5/10, MAP, MRR, nDCG@5/10; pair macro F1/PR-AUC; score
MAE/Spearman where labels support regression; ECE/Brier/reliability curves; p50/p95
latency, peak RAM, startup, and artifact size.

Slice every metric by occupation, industry, seniority, source, document length/format,
rare/common skill, real/synthetic, alias/implicit evidence, career change/gap, education,
format/OCR noise, and hard-negative type. Thresholds and hyperparameters use validation
only. Run the final test once for the promotion decision; preserve errors for the next
training iteration without relabelling test data from predictions.

Machine-readable reports are in `reports/evaluation_metrics.json`,
`reports/metric_comparison.csv`, `reports/data_leakage_report.json`, and
`reports/runtime_validation.json`.
