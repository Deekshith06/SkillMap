# Graph Report - SkillMap  (2026-07-16)

## Corpus Check
- 74 files · ~35,236 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 577 nodes · 1190 edges · 29 communities (23 shown, 6 thin omitted)
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

## Communities (29 total, 6 thin omitted)

### Community 0 - "get_settings"
Cohesion: 0.05
Nodes (78): JSONResponse, Reflex configuration for local and split Vercel/Render deployment., _digest(), load_runtime_assets(), Path, Checksum-verified, cached loading of compact runtime artifacts., runtime_ready(), RuntimeAssets (+70 more)

### Community 1 - "skillmap.py"
Cohesion: 0.08
Nodes (46): radar_chart(), Radar chart for skill domains., file_drop_zone(), Component, file_upload.py — Drag-and-drop upload component wrapper., Component, skill_badge.py — Skill tag/badge component., skill_badge() (+38 more)

### Community 2 - "UserFacingError"
Cohesion: 0.09
Nodes (19): DatasetError, EmptyResumeError, FileTooLargeError, IngestionError, MinimumCountError, Exception, Raised when resume text is empty or too short to score., Raised when dataset validation fails. (+11 more)

### Community 3 - "parse_document"
Cohesion: 0.07
Nodes (41): DocumentValidationError, _extension(), _extract_docx(), _extract_pdf(), _extract_txt(), _normalize_text(), parse_document(), Bounded in-memory parsing for PDF, DOCX, and UTF-8 TXT uploads. (+33 more)

### Community 4 - "SkillMap"
Cohesion: 0.04
Nodes (41): Evaluation status, Known limitations, Model details, Modes, Privacy, Purpose, Scoring, SkillMap Model Card (+33 more)

### Community 5 - "train_model.py"
Cohesion: 0.07
Nodes (36): Counter, ndarray, ClusteringError, InsufficientDataError, ModelNotFoundError, Raised when clustering pipeline fails., Raised when there are not enough resumes to cluster meaningfully., Raised when a required model artifact file is missing. (+28 more)

### Community 6 - "AnalyzeState"
Cohesion: 0.07
Nodes (4): AnalyzeState, Exception, UploadFile, _safe_message()

### Community 7 - "dashboard.py"
Cohesion: 0.12
Nodes (34): page_layout(), Component, A layout component that wraps the page with the navbar., logo(), mobile_nav_link(), nav_link(), navbar(), Component (+26 more)

### Community 8 - "ATSState"
Cohesion: 0.06
Nodes (16): An internal failure with a stable, non-sensitive public message., UserFacingError, get_clusters(), get_stats(), Any, Single-resume workflow state backed by typed runtime services., AppState, ClusterItem (+8 more)

### Community 9 - "BulkState"
Cohesion: 0.11
Nodes (3): BulkResultItem, BulkState, PropsBase

### Community 10 - "ats_scorer.py"
Cohesion: 0.27
Nodes (17): Pattern, _deep_flatten(), detect_domains_nlp(), generate_suggestions(), _match_skill(), Any, ats_scorer.py — ATS scoring engine. Relocated from backend/ats_scorer.py; data p, score_achievements() (+9 more)

### Community 11 - "InsightsState"
Cohesion: 0.09
Nodes (16): cluster_pie_chart(), Component, charts.py — Recharts → rx.recharts wrappers for SkillMap., 2D scatter chart for UMAP cluster positions., Donut pie chart for cluster distribution with center total labels., Horizontal bar chart for top skills., scatter_chart_umap(), skill_bar_chart() (+8 more)

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
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UserFacingError` connect `ATSState` to `get_settings`, `UserFacingError`, `parse_document`, `AnalyzeState`, `BulkState`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Why does `AppState` connect `ATSState` to `get_settings`, `AnalyzeState`, `dashboard.py`, `BulkState`, `InsightsState`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `AnalyzeState` connect `AnalyzeState` to `ATSState`, `skillmap.py`, `get_settings`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `UserFacingError` (e.g. with `DocumentValidationError` and `AnalyzeState`) actually correct?**
  _`UserFacingError` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `AnalyzeState` (e.g. with `UserFacingError` and `AppState`) actually correct?**
  _`AnalyzeState` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ATSState` (e.g. with `UserFacingError` and `AppState`) actually correct?**
  _`ATSState` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `skillmap`, `$schema`, `framework` to the rest of the system?**
  _45 weakly-connected nodes found - possible documentation gaps or missing edges._