# SkillMap Model Card

## Model details

- Runtime model version: `skillmap-lite-1.0.0`
- Taxonomy version: `2026.07`
- Default mode: `lite`
- Artifact manifest: `models/runtime/model_manifest.json`

## Purpose

SkillMap identifies explicit taxonomy skills, suggests an evidence-supported domain, and
compares resume text with a job description. It supports human review and resume editing;
it is not a hiring decision model.

## Modes

Lite mode uses exact normalized taxonomy matches, a small scikit-learn TF-IDF vectorizer,
BM25, and deterministic experience and seniority rules. The classifier is used only to
break tied domain-evidence counts.

Full mode adds cosine similarity from a locally provisioned sentence-transformer. Its
dependencies and model are intentionally excluded from free-tier production. Missing full
assets cause an explicit error, not a fabricated result or silent fallback.

## Scoring

Lexical mode weights available components as 65% required-skill overlap, 25% lexical
similarity, and 10% experience alignment. TF-IDF and BM25 are averaged for lexical
similarity. Components lacking explicit evidence are removed and remaining weights are
renormalized.

Semantic mode weights 45% semantic similarity, 35% skill overlap, 15% experience, and 5%
role alignment. Scores are clamped to 0 through 100. Result confidence describes job-text
evidence coverage, not probability of candidate success.

## Training data and artifacts

The included source CSV is a small research/demo dataset with uneven occupational coverage.
Its category counts and role labels are exported as aggregate catalogue metadata. Complete
resume text is not included in runtime artifacts. The compact classifier is trained on the
curated taxonomy phrases, not employment outcomes.

## Evaluation status

Automated tests cover normalization, evidence monotonicity, unsupported-text behavior,
contract validation, typed PII masking, group leakage, counterfactual identifiers, and the
absence of a fixed 50% fallback. The retained runtime measured 2.931 ms p95 latency,
118.58 MB peak process memory, and 206,304 artifact bytes in a 25-call local smoke run on
2026-07-17. This release has not been
validated for hiring outcomes, fairness across demographic groups, multilingual use, or
cross-industry generalization.

The new training pipeline completed a synthetic-only smoke run. Its metrics are documented
in `docs/EVALUATION.md`; they are not real-world accuracy. The candidate was not promoted
because there are zero immutable real gold test records and no outcome fairness evaluation.

## Known limitations

- Exact taxonomy matching misses synonyms and implicit experience.
- The project taxonomy is not yet normalized to downloaded ESCO/O*NET concepts.
- Parsed layout and reading order can differ from the original document.
- Years-of-experience rules cannot determine whether experience applies to a specific skill.
- The domain catalogue is incomplete and its aggregate counts are not market statistics.
- Semantic mode depends on the provenance and limitations of the separately provisioned
  embedding model.
- A score is withheld when the job text contains no supported required-skill evidence.
- Displayed scores are evidence-alignment heuristics, not probabilities of hiring success.

## Privacy

Email addresses, phone numbers, and URLs are removed before inference. Protected or personal
attributes are not scoring features. Uploaded bytes and document text are excluded from
structured logs and runtime catalogues.

## Versioning and change control

Any taxonomy, scoring-weight, model, or training change must update the corresponding
version, regenerate checksums, add evaluation coverage, and document behavior changes.
