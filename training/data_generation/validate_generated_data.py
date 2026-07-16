"""Validate schema, taxonomy IDs, PII, duplicates, and transparent scores."""

from __future__ import annotations

import json

from training.common import read_jsonl
from training.privacy import assert_no_pii
from training.schemas import CanonicalDocument, MatchPair


def run() -> dict[str, int | bool]:
    documents = [
        *read_jsonl("data/synthetic/profiles.jsonl"),
        *read_jsonl("data/synthetic/jobs.jsonl"),
    ]
    pairs = read_jsonl("data/synthetic/matching_pairs.jsonl")
    ids = set()
    for row in documents:
        document = CanonicalDocument.model_validate(row)
        assert_no_pii(document.text)
        if document.document_id in ids:
            raise ValueError(f"duplicate document ID: {document.document_id}")
        ids.add(document.document_id)
        if any(not entity.taxonomy_id for entity in document.skills):
            raise ValueError(f"missing taxonomy ID: {document.document_id}")
    for row in pairs:
        pair = MatchPair.model_validate(row)
        assert_no_pii(pair.resume_text)
        assert_no_pii(pair.job_text)
        components = pair.component_labels
        expected = (
            0.55 * components["required_skills"]
            + 0.15 * components["preferred_skills"]
            + 0.15 * components["experience"]
            + 0.15 * components["occupation_alignment"]
        )
        if components["critical_missing"]:
            expected = min(expected, 34)
        if abs(expected - pair.final_score) > 0.02:
            raise ValueError(f"score mismatch: {pair.pair_id}")
    return {"documents": len(documents), "pairs": len(pairs), "valid": True}


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
