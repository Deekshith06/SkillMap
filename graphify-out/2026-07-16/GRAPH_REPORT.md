# Graph Report - SkillMap  (2026-07-16)

## Corpus Check
- 74 files · ~39,284 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 576 nodes · 1183 edges · 29 communities (22 shown, 7 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 70 edges (avg confidence: 0.64)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `911811a6`
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

## God Nodes (most connected - your core abstractions)
1. `UserFacingError` - 33 edges
2. `AnalyzeState` - 33 edges
3. `ATSState` - 32 edges
4. `parse_document()` - 28 edges
5. `get_settings()` - 25 edges
6. `BulkState` - 25 edges
7. `DocumentValidationError` - 22 edges
8. `load_runtime_assets()` - 21 edges
9. `parse_upload()` - 21 edges
10. `SkillMap` - 19 edges

## Surprising Connections (you probably didn't know these)
- `FakeUpload` --uses--> `DocumentValidationError`  [INFERRED]
  tests/security/test_upload_security.py → skillmap/adapters/document_parser.py
- `test_async_upload_reader_is_bounded_and_closed()` --indirect_call--> `DocumentValidationError`  [INFERRED]
  tests/security/test_upload_security.py → skillmap/adapters/document_parser.py
- `test_rejects_docx_zip_path_traversal()` --indirect_call--> `DocumentValidationError`  [INFERRED]
  tests/security/test_upload_security.py → skillmap/adapters/document_parser.py
- `test_rejects_empty_document()` --indirect_call--> `DocumentValidationError`  [INFERRED]
  tests/unit/test_document_parser.py → skillmap/adapters/document_parser.py
- `test_rejects_invalid_file_types()` --indirect_call--> `DocumentValidationError`  [INFERRED]
  tests/unit/test_document_parser.py → skillmap/adapters/document_parser.py

## Import Cycles
- None detected.

## Communities (29 total, 7 thin omitted)

### Community 0 - "get_settings"
Cohesion: 0.05
Nodes (78): JSONResponse, Reflex configuration for local and split Vercel/Render deployment., _digest(), load_runtime_assets(), Path, Checksum-verified, cached loading of compact runtime artifacts., runtime_ready(), RuntimeAssets (+70 more)

### Community 1 - "skillmap.py"
Cohesion: 0.05
Nodes (62): file_drop_zone(), Component, file_upload.py — Drag-and-drop upload component wrapper., page_layout(), Component, A layout component that wraps the page with the navbar., logo(), nav_link() (+54 more)

### Community 2 - "UserFacingError"
Cohesion: 0.06
Nodes (43): ClusteringError, DatasetError, EmptyResumeError, FileTooLargeError, IngestionError, InsufficientDataError, MinimumCountError, Exception (+35 more)

### Community 3 - "parse_document"
Cohesion: 0.08
Nodes (36): DocumentValidationError, _extension(), _extract_docx(), _extract_pdf(), _extract_txt(), _normalize_text(), parse_document(), Bounded in-memory parsing for PDF, DOCX, and UTF-8 TXT uploads. (+28 more)

### Community 4 - "SkillMap"
Cohesion: 0.04
Nodes (41): Evaluation status, Known limitations, Model details, Modes, Privacy, Purpose, Scoring, SkillMap Model Card (+33 more)

### Community 5 - "train_model.py"
Cohesion: 0.09
Nodes (32): Counter, ndarray, ModelNotFoundError, Raised when a required model artifact file is missing., domain_label(), build_cluster_pipeline(), get_cluster_metrics(), get_cluster_names() (+24 more)

### Community 6 - "AnalyzeState"
Cohesion: 0.07
Nodes (5): input_panel(), AnalyzeState, Exception, UploadFile, _safe_message()

### Community 7 - "dashboard.py"
Cohesion: 0.13
Nodes (29): cluster_pie_chart(), Component, radar_chart(), charts.py — Recharts → rx.recharts wrappers for SkillMap., 2D scatter chart for UMAP cluster positions., Donut pie chart for cluster distribution with center total labels., Radar chart for skill domains., Horizontal bar chart for top skills. (+21 more)

### Community 9 - "BulkState"
Cohesion: 0.11
Nodes (3): BulkResultItem, BulkState, PropsBase

### Community 10 - "ats_scorer.py"
Cohesion: 0.27
Nodes (17): Pattern, _deep_flatten(), detect_domains_nlp(), generate_suggestions(), _match_skill(), Any, ats_scorer.py — ATS scoring engine. Relocated from backend/ats_scorer.py; data p, score_achievements() (+9 more)

### Community 11 - "InsightsState"
Cohesion: 0.14
Nodes (3): InsightsState, Derives chart data from loaded stats., Lite mode has no 2D embedding artifact, so no scatter is returned.

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

## Knowledge Gaps
- **45 isolated node(s):** `skillmap`, `$schema`, `framework`, `installCommand`, `buildCommand` (+40 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UserFacingError` connect `UserFacingError` to `get_settings`, `parse_document`, `AnalyzeState`, `ATSState`, `BulkState`?**
  _High betweenness centrality (0.149) - this node is a cross-community bridge._
- **Why does `AppState` connect `UserFacingError` to `skillmap.py`, `AnalyzeState`, `dashboard.py`, `ATSState`, `BulkState`, `InsightsState`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `AnalyzeState` connect `AnalyzeState` to `get_settings`, `skillmap.py`, `UserFacingError`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `UserFacingError` (e.g. with `DocumentValidationError` and `AnalyzeState`) actually correct?**
  _`UserFacingError` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `AnalyzeState` (e.g. with `UserFacingError` and `AppState`) actually correct?**
  _`AnalyzeState` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ATSState` (e.g. with `UserFacingError` and `AppState`) actually correct?**
  _`ATSState` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `skillmap`, `$schema`, `framework` to the rest of the system?**
  _45 weakly-connected nodes found - possible documentation gaps or missing edges._