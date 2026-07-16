"""Build a versioned exact/alias canonicalization index."""

from __future__ import annotations

import argparse
import json
import re
from typing import Any

from skillmap.domain.taxonomy import flatten_taxonomy
from training.common import ROOT, load_config, read_jsonl, write_json
from training.modeling import candidate_dir


def _normalize(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9+#.]+", " ", value.lower()).split())


def run(config: dict[str, Any]) -> dict[str, Any]:
    concepts = read_jsonl("data/processed/taxonomy_concepts.jsonl")
    source = "ESCO/O*NET"
    if not concepts and config.get("allow_legacy_taxonomy_for_smoke"):
        taxonomy = json.loads(
            (ROOT / "skillmap/ml/data/powerSkills.json").read_text(encoding="utf-8")
        )
        concepts = [
            {
                "taxonomy": "SkillMap legacy smoke taxonomy",
                "taxonomy_id": f"skillmap:{_normalize(name).replace(' ', '-')}",
                "preferred_label": name,
                "aliases": [],
            }
            for name in sorted(
                {skill for value in taxonomy.values() for skill in flatten_taxonomy(value)}
            )
        ]
        source = "legacy_smoke_only"
    aliases: dict[str, dict[str, str]] = {}
    collisions: dict[str, list[str]] = {}
    for concept in concepts:
        for label in [concept["preferred_label"], *concept.get("aliases", [])]:
            key = _normalize(label)
            candidate = {
                "canonical_name": concept["preferred_label"],
                "taxonomy": concept["taxonomy"],
                "taxonomy_id": concept["taxonomy_id"],
                "mapping_method": "preferred_label"
                if label == concept["preferred_label"]
                else "alias",
            }
            if key in aliases and aliases[key]["taxonomy_id"] != candidate["taxonomy_id"]:
                collisions.setdefault(key, [aliases[key]["taxonomy_id"]]).append(
                    candidate["taxonomy_id"]
                )
                aliases.pop(key, None)
            elif key not in collisions:
                aliases[key] = candidate
    artifact = {
        "version": "1",
        "source": source,
        "unknown_fallback": True,
        "aliases": aliases,
        "ambiguous_aliases": collisions,
    }
    write_json(candidate_dir(config) / "canonicalizer/aliases.json", artifact)
    result = {
        "concepts": len(concepts),
        "unambiguous_aliases": len(aliases),
        "ambiguous_aliases": len(collisions),
        "recall_at_1": None,
        "recall_at_5": None,
        "mrr": None,
        "evaluation_scope": "not_measured_no_real_canonicalization_gold",
    }
    write_json(candidate_dir(config) / "canonicalizer/evaluation.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
