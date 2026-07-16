"""Audit registry completeness, local provenance, PII, duplicates, and hashes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from training.common import ROOT, resolve, sha256, write_json
from training.privacy import find_pii

REQUIRED_FIELDS = {
    "name",
    "version",
    "source",
    "retrieved_at",
    "license",
    "attribution",
    "redistribution_allowed",
    "contains_pii",
    "synthetic",
    "language",
    "task",
    "record_count",
    "approved_for_training",
    "approved_for_validation",
    "approved_for_testing",
    "sha256",
    "notes",
}


def _normalized(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def _audit_csv(path: Path) -> dict[str, Any]:
    rows = list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))
    text_field = next(
        (name for name in ("Resume_str", "text", "description") if rows and name in rows[0]), None
    )
    texts = [row.get(text_field, "") for row in rows] if text_field else []
    hashes = Counter(hashlib.sha256(_normalized(text).encode()).hexdigest() for text in texts)
    pii = Counter(kind for text in texts for kind in find_pii(text))
    word_shingles = []
    for text in texts:
        tokens = _normalized(text).split()
        word_shingles.append(
            {" ".join(tokens[index : index + 5]) for index in range(max(0, len(tokens) - 4))}
        )
    similarities = [
        len(left & right) / len(left | right)
        for index, left in enumerate(word_shingles)
        for right in word_shingles[index + 1 :]
        if left or right
    ]
    return {
        "record_count": len(rows),
        "fields": list(rows[0]) if rows else [],
        "text_field": text_field,
        "exact_duplicate_records": sum(count - 1 for count in hashes.values() if count > 1),
        "exact_duplicate_clusters": sum(count > 1 for count in hashes.values()),
        "near_duplicate_pairs": {
            "word_5gram_jaccard_gte_0_8": sum(value >= 0.8 for value in similarities),
            "word_5gram_jaccard_gte_0_9": sum(value >= 0.9 for value in similarities),
        },
        "pii_pattern_counts": dict(pii),
        "text_length": {
            "min": min(map(len, texts), default=0),
            "max": max(map(len, texts), default=0),
            "mean": round(sum(map(len, texts)) / max(len(texts), 1), 2),
        },
    }


def run() -> dict[str, Any]:
    registry_path = ROOT / "data/manifests/dataset_registry.yaml"
    entries = json.loads(registry_path.read_text(encoding="utf-8"))["datasets"]
    names = [entry.get("name") for entry in entries]
    issues: list[str] = []
    if len(names) != len(set(names)):
        issues.append("duplicate dataset names")
    audits = []
    for entry in entries:
        missing = sorted(REQUIRED_FIELDS - entry.keys())
        if missing:
            issues.append(f"{entry.get('name', '<unknown>')}: missing {missing}")
        if entry.get("approved_for_training") and entry.get("license") in {None, "", "unknown"}:
            issues.append(f"{entry['name']}: training approval requires known license")
        local = entry.get("local_path")
        path = resolve(local) if local else None
        item: dict[str, Any] = {
            "name": entry.get("name"),
            "approved": {
                "training": entry.get("approved_for_training"),
                "validation": entry.get("approved_for_validation"),
                "testing": entry.get("approved_for_testing"),
            },
            "exists": bool(path and path.exists()),
        }
        if path and path.is_file():
            item["sha256"] = sha256(path)
            item["hash_matches"] = not entry.get("sha256") or item["sha256"] == entry["sha256"]
            if path.suffix.lower() == ".csv":
                item.update(_audit_csv(path))
        audits.append(item)
    report = {
        "registry": str(registry_path.relative_to(ROOT)),
        "registry_complete": not issues,
        "issues": issues,
        "datasets": audits,
        "production_training_approved": False,
        "reason": "No immutable, independently reviewed real gold evaluation set is registered.",
    }
    write_json("reports/data_quality_report.json", report)
    return report


def main() -> None:
    argparse.ArgumentParser().parse_args()
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
