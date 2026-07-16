# Security review

Scope: offline dataset/training code and the existing resume upload/runtime boundary.

Implemented controls include archive traversal checks, immutable download receipts,
environment-only provider keys, a hard block on sending non-synthetic records to external
generators, typed PII masking, processed-data PII assertions, metadata-only logs, bounded
uploads/parsers, checksum verification before joblib loading, local-only full-model loading,
and an isolated assertion that lite mode does not import Torch.

The annotation API binds to loopback and validates IDs, labels, evidence counts, notes, and
file paths. It intentionally has no authentication and must never be exposed to a network.

Residual risks: joblib is executable serialization, so integrity depends on the trusted
repository plus SHA-256 manifest; signatures are not implemented. Regex PII masking cannot
guarantee removal of unlabelled names/addresses. Model and dataset downloads remain supply-
chain inputs and require pinned hashes/commits.

Measured checks on 2026-07-17:

- Bandit scanned `skillmap`, `training`, and `tools`: 0 high, medium, or low findings.
- `pip-audit` found no known vulnerabilities in the fully pinned runtime requirements.
  The audit used `--no-deps` because the file already contains the resolved transitive graph;
  hashes are not yet embedded in the lock file.
- Hugging Face candidates are pinned to explicit revisions in non-smoke configurations.
