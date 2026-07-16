"""Exact and MinHash/LSH-assisted near-duplicate clustering before splitting."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from typing import Any

from training.common import load_config, read_jsonl, write_json, write_jsonl


def normalize_text(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def char_ngrams(text: str, size: int = 5) -> set[str]:
    normalized = normalize_text(text)
    return {normalized[index : index + size] for index in range(max(0, len(normalized) - size + 1))}


def similarity(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left or right else 1.0


class _UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[max(a, b)] = min(a, b)


def cluster_texts(texts: list[str], threshold: float = 0.9) -> list[int]:
    shingles = [char_ngrams(text) for text in texts]
    union = _UnionFind(len(texts))
    exact: dict[str, int] = {}
    for index, text in enumerate(texts):
        digest = hashlib.sha256(normalize_text(text).encode()).hexdigest()
        if digest in exact:
            union.union(index, exact[digest])
        else:
            exact[digest] = index

    signatures = []
    for values in shingles:
        hashed = sorted(
            int.from_bytes(hashlib.blake2b(value.encode(), digest_size=8).digest())
            for value in values
        )
        signatures.append(tuple(hashed[:16]))
    buckets: dict[tuple[int, tuple[int, ...]], list[int]] = defaultdict(list)
    for index, signature in enumerate(signatures):
        for band in range(4):
            buckets[(band, signature[band * 4 : (band + 1) * 4])].append(index)
    if len(texts) <= 1_000:
        # ponytail: exhaustive small-corpus recall; LSH keeps larger runs bounded.
        candidates = {
            (left, right) for left in range(len(texts)) for right in range(left + 1, len(texts))
        }
    else:
        candidates = {
            (min(left, right), max(left, right))
            for bucket in buckets.values()
            for position, left in enumerate(bucket)
            for right in bucket[position + 1 :]
        }
    for left, right in candidates:
        if similarity(shingles[left], shingles[right]) >= threshold:
            union.union(left, right)
    roots = [union.find(index) for index in range(len(texts))]
    labels = {root: cluster for cluster, root in enumerate(sorted(set(roots)))}
    return [labels[root] for root in roots]


def run(config: dict[str, Any]) -> dict[str, Any]:
    documents = [
        *read_jsonl("data/synthetic/profiles.jsonl"),
        *read_jsonl("data/synthetic/jobs.jsonl"),
    ]
    labels = cluster_texts(
        [row["text"] for row in documents], float(config.get("near_duplicate_threshold", 0.9))
    )
    for row, label in zip(documents, labels, strict=True):
        row["duplicate_cluster"] = f"duplicate-{label:06d}"
    clusters: dict[str, list[str]] = defaultdict(list)
    for row in documents:
        clusters[row["duplicate_cluster"]].append(row["document_id"])
    duplicate_rows: list[dict[str, Any]] = [
        {"cluster_id": key, "document_ids": values, "size": len(values)}
        for key, values in clusters.items()
        if len(values) > 1
    ]
    write_jsonl("data/interim/documents_deduplicated.jsonl", documents)
    write_jsonl("reports/duplicate_clusters.jsonl", duplicate_rows)
    report = {
        "records": len(documents),
        "clusters": len(clusters),
        "duplicate_clusters": len(duplicate_rows),
        "duplicates_removed": sum(int(row["size"]) - 1 for row in duplicate_rows),
        "algorithm": "normalized_sha256_plus_minhash_lsh_char_5gram_jaccard",
        "threshold": config.get("near_duplicate_threshold", 0.9),
    }
    write_json("reports/deduplication_report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
