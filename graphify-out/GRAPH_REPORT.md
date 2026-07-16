# Graph Report - SkillMap  (2026-07-17)

## Corpus Check
- 139 files · ~50,273 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 865 nodes · 1917 edges · 69 communities (49 shown, 20 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 76 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f45576af`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- get_settings
- skillmap.py
- UserFacingError
- parse_document
- SkillMap
- train_model.py
- AnalyzeState
- dashboard.py
- ATSState
- BulkState
- ats_scorer.py
- InsightsState
- logging.py
- vercel.json
- score_meter.py
- cluster_card.py
- __init__.py
- __init__.py
- __init__.py
- __init__.py
- tokens.py
- skillmap
- generate_synthetic.py
- modeling.py
- read_jsonl
- models.py
- lite_engine.py
- load_config
- write_json
- ats_editor.py
- UserFacingError
- AppState
- test_scoring.py
- InsightsState
- deduplicate.py
- train_matcher.py
- ui.py
- skillmap.py
- neural.py
- navbar
- SkillMap Model Card
- README.md
- LiteEngine
- Privacy
- Training
- theme.py
- evaluate_all.py
- train_skill_extractor.py
- Data annotation guide
- Responsible AI
- FullEngine
- Evaluation
- providers.py
- README.md
- DEPLOYMENT_MODEL_OPTIMIZATION.md
- ablation_summary.md
- fairness_report.md
- security_review.md
- README.md
- __init__.py
- __init__.py
- __init__.py

## God Nodes (most connected - your core abstractions)
1. `read_jsonl()` - 45 edges
2. `write_json()` - 42 edges
3. `load_config()` - 37 edges
4. `UserFacingError` - 33 edges
5. `AnalyzeState` - 33 edges
6. `ATSState` - 32 edges
7. `parse_document()` - 28 edges
8. `get_settings()` - 27 edges
9. `BulkState` - 25 edges
10. `load_runtime_assets()` - 23 edges

## Surprising Connections (you probably didn't know these)
- `FakeUpload` --uses--> `DocumentValidationError`  [INFERRED]
  tests/security/test_upload_security.py → skillmap/adapters/document_parser.py
- `test_async_upload_reader_is_bounded_and_closed()` --indirect_call--> `DocumentValidationError`  [INFERRED]
  tests/security/test_upload_security.py → skillmap/adapters/document_parser.py
- `test_rejects_docx_zip_path_traversal()` --indirect_call--> `DocumentValidationError`  [INFERRED]
  tests/security/test_upload_security.py → skillmap/adapters/document_parser.py
- `test_no_artificial_fifty_percent_fallback()` --calls--> `match_job()`  [EXTRACTED]
  tests/unit/test_scoring.py → skillmap/services/analysis_service.py
- `test_no_score_when_job_has_no_supported_requirement_evidence()` --calls--> `match_job()`  [EXTRACTED]
  tests/unit/test_scoring.py → skillmap/services/analysis_service.py

## Import Cycles
- None detected.

## Communities (69 total, 20 thin omitted)

### Community 0 - "get_settings"
Cohesion: 0.16
Nodes (20): JSONResponse, Reflex configuration for local and split Vercel/Render deployment., _digest(), load_runtime_assets(), Path, Checksum-verified, cached loading of compact runtime artifacts., runtime_ready(), health() (+12 more)

### Community 1 - "skillmap.py"
Cohesion: 0.20
Nodes (16): file_drop_zone(), Component, file_upload.py — Drag-and-drop upload component wrapper., error_alert(), analyze_page(), input_panel(), Component, analyze.py — Single resume analysis page. (+8 more)

### Community 2 - "UserFacingError"
Cohesion: 0.09
Nodes (19): DatasetError, EmptyResumeError, FileTooLargeError, IngestionError, MinimumCountError, Exception, Raised when resume text is empty or too short to score., Raised when dataset validation fails. (+11 more)

### Community 3 - "parse_document"
Cohesion: 0.10
Nodes (29): DocumentValidationError, _extension(), _extract_docx(), _extract_pdf(), _extract_txt(), _normalize_text(), parse_document(), Bounded in-memory parsing for PDF, DOCX, and UTF-8 TXT uploads. (+21 more)

### Community 4 - "SkillMap"
Cohesion: 0.10
Nodes (20): Accuracy-first training pipeline, Architecture, Contributing, Development commands, Environment variables, Free-tier limitations, Implemented features, License (+12 more)

### Community 5 - "train_model.py"
Cohesion: 0.07
Nodes (36): Counter, ndarray, ClusteringError, InsufficientDataError, ModelNotFoundError, Raised when clustering pipeline fails., Raised when there are not enough resumes to cluster meaningfully., Raised when a required model artifact file is missing. (+28 more)

### Community 7 - "dashboard.py"
Cohesion: 0.32
Nodes (15): stats_card(), arch_box(), arch_connector(), arch_endpoint(), arch_label(), arch_list_item(), cluster_list_item(), dashboard_mixed_content() (+7 more)

### Community 9 - "BulkState"
Cohesion: 0.11
Nodes (3): BulkResultItem, BulkState, PropsBase

### Community 10 - "ats_scorer.py"
Cohesion: 0.27
Nodes (17): Pattern, _deep_flatten(), detect_domains_nlp(), generate_suggestions(), _match_skill(), Any, ats_scorer.py — ATS scoring engine. Relocated from backend/ats_scorer.py; data p, score_achievements() (+9 more)

### Community 11 - "InsightsState"
Cohesion: 0.20
Nodes (15): cluster_pie_chart(), Component, radar_chart(), charts.py — Recharts → rx.recharts wrappers for SkillMap., 2D scatter chart for UMAP cluster positions., Donut pie chart for cluster distribution with center total labels., Radar chart for skill domains., Horizontal bar chart for top skills. (+7 more)

### Community 12 - "logging.py"
Cohesion: 0.29
Nodes (8): Logger, LogRecord, configure_logging(), JsonFormatter, log_analysis_event(), Minimal structured logging without document content or personal data., Log only the allowlisted operational metadata in this signature., test_structured_logs_cannot_include_resume_pii()

### Community 13 - "vercel.json"
Cohesion: 0.25
Nodes (7): buildCommand, cleanUrls, framework, headers, installCommand, outputDirectory, $schema

### Community 14 - "score_meter.py"
Cohesion: 0.33
Nodes (6): Component, score_meter.py — ATS score ring/progress component (Var-safe)., Var-safe sub-score bar.      score must be a numeric Var or plain int.     pct =, Simple score display ring., score_ring(), sub_score_bar()

### Community 15 - "cluster_card.py"
Cohesion: 0.40
Nodes (4): cluster_card(), Component, cluster_card.py — Cluster summary card using new design tokens., Accepts a ClusterItem rx.Base object from AppState.clusters.

### Community 29 - "generate_synthetic.py"
Cohesion: 0.06
Nodes (54): EntityCategory, test_bio_alignment_and_schema_offsets(), test_canonical_schema_rejects_misaligned_span(), test_grouped_split_never_crosses_families(), test_matching_pair_rejects_unbounded_score(), test_pii_is_typed_and_job_relevant_dates_are_preserved(), _audit_csv(), main() (+46 more)

### Community 30 - "modeling.py"
Cohesion: 0.16
Nodes (23): main(), Any, Feature ablations evaluated on validation only., run(), main(), Any, Fit validation-only score calibration for the compact reranker., run() (+15 more)

### Community 31 - "read_jsonl"
Cohesion: 0.11
Nodes (24): Annotation, _file(), BaseModel, Path, queue(), Local-only annotation queue API with explicit annotator IDs and adjudication., save(), agreement() (+16 more)

### Community 32 - "models.py"
Cohesion: 0.06
Nodes (57): RuntimeAssets, FullModeUnavailableError, ClusterSummary, MatchResult, PredictionResult, BaseModel, Validated contracts returned by SkillMap runtime services., RuntimeManifest (+49 more)

### Community 33 - "lite_engine.py"
Cohesion: 0.14
Nodes (13): ParsedDocument, _close_upload(), parse_upload(), Any, Upload orchestration with bounded reads, timeout, cleanup, and safe logging., _read_bounded(), Exception, UploadFile (+5 more)

### Community 34 - "load_config"
Cohesion: 0.15
Nodes (18): Small shared utilities for offline pipeline commands., run_metadata(), seed_everything(), Reproducible offline training and evaluation for SkillMap., main(), Any, Resumable end-to-end training orchestration., run() (+10 more)

### Community 35 - "write_json"
Cohesion: 0.33
Nodes (10): Path, resolve(), sha256(), write_json(), main(), Any, Path, Download only registry-approved public datasets with immutable receipts. (+2 more)

### Community 36 - "ats_editor.py"
Cohesion: 0.23
Nodes (15): Component, skill_badge.py — Skill tag/badge component., skill_badge(), skill_pill_muted(), skill_pill_primary(), ats_editor_page(), Component, ats_editor.py — Upload → Score → Suggestions ATS page. (+7 more)

### Community 37 - "UserFacingError"
Cohesion: 0.12
Nodes (21): new_request_id(), core/exceptions.py — Custom exception hierarchy for SkillMap.  Hierarchy:   Skil, An internal failure with a stable, non-sensitive public message., UserFacingError, analyze_resume(), get_clusters(), get_stats(), match_job() (+13 more)

### Community 38 - "AppState"
Cohesion: 0.29
Nodes (9): git_commit(), _artifact_hashes(), main(), Any, Path, Package candidates and promote only after real-data acceptance gates pass., run(), candidate_dir() (+1 more)

### Community 39 - "test_scoring.py"
Cohesion: 0.39
Nodes (6): _fingerprint(), main(), Any, Select uncertain, rare, and textually diverse examples for review., run(), stable_id()

### Community 40 - "InsightsState"
Cohesion: 0.14
Nodes (3): InsightsState, Derives chart data from loaded stats., Lite mode has no 2D embedding artifact, so no scatter is returned.

### Community 41 - "deduplicate.py"
Cohesion: 0.33
Nodes (6): test_exact_and_near_duplicates_share_a_cluster(), char_ngrams(), cluster_texts(), normalize_text(), similarity(), _UnionFind

### Community 42 - "train_matcher.py"
Cohesion: 0.23
Nodes (13): TfidfVectorizer, load_config(), Load JSON-compatible YAML without adding a YAML runtime dependency., main(), Any, Train and evaluate the fast retrieval baseline., run(), _scores() (+5 more)

### Community 43 - "ui.py"
Cohesion: 0.30
Nodes (11): divider(), meta_row(), pipeline_step(), Component, components/ui.py — Reusable UI component library matching the design spec. Cover, section_header(), skeleton_bar(), skeleton_card() (+3 more)

### Community 44 - "skillmap.py"
Cohesion: 0.32
Nodes (11): footer(), dashboard_page(), analyze(), ats(), backend_exception_handler(), bulk(), index(), _page_shell() (+3 more)

### Community 45 - "neural.py"
Cohesion: 0.29
Nodes (10): Any, Path, Optional heavy teacher lanes; imported only by offline non-smoke runs., Train symmetric resume/job triplets with taxonomy-derived hard negatives., Train an offline pair-scoring teacher and return train/test soft labels., Train separate SKILL and KNOWLEDGE BIO heads so nested spans remain representabl, _revision(), train_biencoder() (+2 more)

### Community 46 - "navbar"
Cohesion: 0.33
Nodes (9): page_layout(), Component, A layout component that wraps the page with the navbar., logo(), mobile_nav_link(), nav_link(), navbar(), Component (+1 more)

### Community 47 - "SkillMap Model Card"
Cohesion: 0.20
Nodes (10): Evaluation status, Known limitations, Model details, Modes, Privacy, Purpose, Scoring, SkillMap Model Card (+2 more)

### Community 48 - "README.md"
Cohesion: 0.25
Nodes (4): Datasets and licences, Local restricted data, Rejected or restricted sources, Selected sources

### Community 50 - "Privacy"
Cohesion: 0.29
Nodes (7): Data handled, Incident handling, Logging, Personal information, Privacy, Processing and retention, User controls

### Community 51 - "Training"
Cohesion: 0.29
Nodes (6): Environment, Pipeline commands, Prediction and data contract, Promotion, Public data, Training

### Community 53 - "evaluate_all.py"
Cohesion: 0.39
Nodes (7): _load(), main(), Any, Path, Aggregate comparable metrics without treating smoke data as real accuracy., rows_metric_fields(), run()

### Community 54 - "train_skill_extractor.py"
Cohesion: 0.48
Nodes (6): entity_metrics(), _baseline_rows(), main(), Any, Evaluate the taxonomy extractor and optionally fine-tune token classifiers., run()

### Community 55 - "Data annotation guide"
Cohesion: 0.33
Nodes (5): Data annotation guide, Decisions and examples, Matching labels, Quality control, Unit and workflow

### Community 56 - "Responsible AI"
Cohesion: 0.33
Nodes (5): Human oversight, Intended use, Limitations and monitoring, Prohibited use, Responsible AI

### Community 57 - "FullEngine"
Cohesion: 0.67
Nodes (3): MonkeyPatch, test_environment_configuration_parses_origins(), test_rejects_unknown_application_mode()

### Community 58 - "Evaluation"
Cohesion: 0.40
Nodes (4): Current measured results, Evaluation, Required real evaluation, Retained production runtime

## Knowledge Gaps
- **66 isolated node(s):** `skillmap`, `$schema`, `framework`, `installCommand`, `buildCommand` (+61 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `get_settings` to `models.py`, `lite_engine.py`, `parse_document`, `UserFacingError`, `logging.py`, `LiteEngine`, `FullEngine`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Why does `write_json()` connect `write_json` to `get_settings`, `load_config`, `AppState`, `train_matcher.py`, `evaluate_all.py`, `train_skill_extractor.py`, `generate_synthetic.py`, `modeling.py`, `read_jsonl`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Why does `load_runtime_assets()` connect `get_settings` to `models.py`, `UserFacingError`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `UserFacingError` (e.g. with `DocumentValidationError` and `AnalyzeState`) actually correct?**
  _`UserFacingError` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `AnalyzeState` (e.g. with `UserFacingError` and `AppState`) actually correct?**
  _`AnalyzeState` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `skillmap`, `$schema`, `framework` to the rest of the system?**
  _66 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `UserFacingError` be split into smaller, more focused modules?**
  _Cohesion score 0.08923076923076922 - nodes in this community are weakly interconnected._