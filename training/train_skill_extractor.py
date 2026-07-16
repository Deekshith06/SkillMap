"""Evaluate the taxonomy extractor and optionally fine-tune token classifiers."""

from __future__ import annotations

import argparse
import json
from typing import Any

from skillmap.domain.taxonomy import extract_taxonomy_skills
from training.common import load_config, read_jsonl, write_json
from training.modeling import candidate_dir, entity_metrics


def _baseline_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    skillspan = read_jsonl("data/processed/skillspan.jsonl")
    if skillspan:
        return [row for row in skillspan if row.get("official_split") == "test"]
    return read_jsonl("data/synthetic/profiles.jsonl")


def run(config: dict[str, Any]) -> dict[str, Any]:
    rows = _baseline_rows(config)
    vocabulary = sorted(
        {
            (entity.get("normalized_name") or entity["text"]).lower()
            for row in rows
            for entity in [*row.get("skills", []), *row.get("knowledge", [])]
        }
    )
    gold: list[set[tuple[int, int, str]]] = []
    predicted: list[set[tuple[int, int, str]]] = []
    for row in rows:
        expected = {
            (entity["start"], entity["end"], entity["text"].lower())
            for entity in [*row.get("skills", []), *row.get("knowledge", [])]
        }
        found = extract_taxonomy_skills(row["text"], vocabulary, limit=200)
        actual = set()
        lowered = row["text"].lower()
        for skill in found:
            start = lowered.find(skill)
            if start >= 0:
                actual.add((start, start + len(skill), skill))
        gold.append(expected)
        predicted.append(actual)
    metrics = entity_metrics(gold, predicted)
    requested = config.get("models", {}).get("skill_extractor", "")
    candidates = config.get("models", {}).get("skill_extractor_candidates", [])
    requested_candidates = candidates or (
        [requested] if requested and requested != "taxonomy_baseline" else []
    )
    executed = []
    if config["mode"] != "smoke" and requested_candidates:
        from training.neural import train_token_classifier

        skillspan_rows = read_jsonl("data/processed/skillspan.jsonl")
        if not skillspan_rows:
            raise ValueError("SkillSpan must be prepared before neural extractor training")
        for model_name in requested_candidates:
            model_metrics = train_token_classifier(
                model_name,
                skillspan_rows,
                candidate_dir(config) / "skill_extractor" / model_name.replace("/", "--"),
                config,
            )
            executed.append({"model": model_name, "metrics": model_metrics})
    result = {
        "model": "longest_span_taxonomy_baseline",
        "records": len(rows),
        "metrics": metrics,
        "evaluation_scope": "official_skillspan_test"
        if read_jsonl("data/processed/skillspan.jsonl")
        else "synthetic_smoke",
        "neural_candidates_requested": requested_candidates,
        "neural_candidates_executed": executed,
        "best_neural_candidate": max(
            executed, key=lambda row: row["metrics"]["mean_entity_f1"], default=None
        ),
        "note": "SkillSpan labels SKILL and KNOWLEDGE; it does not directly provide reliable hard-versus-soft labels.",
    }
    write_json(candidate_dir(config) / "skill_extractor/evaluation.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
