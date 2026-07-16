"""Convert approved public data into canonical SkillMap records."""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Literal

from training.common import ROOT, stable_id, write_json, write_jsonl
from training.privacy import assert_no_pii, mask_pii
from training.schemas import CanonicalDocument, bio_spans


def _json_payload(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        return value
    for key in ("data", "records", "sentences"):
        if isinstance(value.get(key), list):
            return value[key]
    return []


def _split_name(path: Path) -> Literal["train", "validation", "test"] | None:
    lowered = path.as_posix().lower()
    if "train" in lowered:
        return "train"
    if "dev" in lowered or "valid" in lowered:
        return "validation"
    if "test" in lowered:
        return "test"
    return None


def prepare_skillspan(root: Path) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for path in root.rglob("*.json") if root.exists() else []:
        split = _split_name(path)
        if split is None:
            continue
        for sentence_index, row in enumerate(_json_payload(path)):
            tokens = row.get("tokens", [])
            skill_tags = row.get("tags_skill", [])
            knowledge_tags = row.get("tags_knowledge", [])
            if not tokens or len(tokens) != len(skill_tags) or len(tokens) != len(knowledge_tags):
                continue
            text, skills = bio_spans(tokens, skill_tags, "SKILL")
            _, knowledge = bio_spans(tokens, knowledge_tags, "KNOWLEDGE")
            safe_text = mask_pii(text)
            if safe_text != text:
                # Offsets cannot be preserved after redaction; exclude the rare affected sentence.
                continue
            assert_no_pii(safe_text)
            document = CanonicalDocument(
                document_id=f"skillspan-{stable_id(path.name, row.get('idx'), sentence_index)}",
                document_type="sentence",
                text=safe_text,
                skills=skills,
                knowledge=knowledge,
                source_dataset="skillspan",
                official_split=split,
            )
            output.append(document.model_dump(mode="json"))
    return output


def _csv_files(root: Path) -> Iterable[Path]:
    return root.rglob("*.csv") if root.exists() else []


def prepare_taxonomy(esco_root: Path, onet_root: Path) -> list[dict[str, Any]]:
    concepts: dict[tuple[str, str], dict[str, Any]] = {}
    for taxonomy, root in (("ESCO", esco_root), ("O*NET", onet_root)):
        for path in _csv_files(root):
            with path.open(encoding="utf-8-sig", errors="replace", newline="") as handle:
                for row in csv.DictReader(handle):
                    lowered = {key.lower().replace(" ", "_"): value for key, value in row.items()}
                    name = next(
                        (
                            lowered.get(key, "").strip()
                            for key in (
                                "preferredlabel",
                                "preferred_label",
                                "element_name",
                                "title",
                                "commodity_title",
                                "example",
                            )
                            if lowered.get(key, "").strip()
                        ),
                        "",
                    )
                    identifier = next(
                        (
                            lowered.get(key, "").strip()
                            for key in ("concepturi", "concept_uri", "element_id", "o*net-soc_code")
                            if lowered.get(key, "").strip()
                        ),
                        "",
                    )
                    if not name or not identifier:
                        continue
                    aliases: list[str] = []
                    for key in ("altlabels", "alt_labels", "alternate_title", "short_title"):
                        aliases.extend(
                            part.strip()
                            for part in lowered.get(key, "").split("\n")
                            if part.strip()
                        )
                    concepts[(taxonomy, identifier)] = {
                        "taxonomy": taxonomy,
                        "taxonomy_id": identifier,
                        "preferred_label": name,
                        "aliases": sorted(set(aliases)),
                        "source_file": path.name,
                    }
    return list(concepts.values())


def run() -> dict[str, Any]:
    skillspan = prepare_skillspan(ROOT / "data/raw/skillspan")
    concepts = prepare_taxonomy(ROOT / "data/raw/esco/1.2.1", ROOT / "data/raw/onet/30.3")
    write_jsonl("data/processed/skillspan.jsonl", skillspan)
    write_jsonl("data/processed/taxonomy_concepts.jsonl", concepts)
    report = {
        "skillspan_records": len(skillspan),
        "taxonomy_concepts": len(concepts),
        "official_split_counts": {
            split: sum(row["official_split"] == split for row in skillspan)
            for split in ("train", "validation", "test")
        },
    }
    write_json("reports/preparation_report.json", report)
    return report


def main() -> None:
    argparse.ArgumentParser().parse_args()
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
