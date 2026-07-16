"""Generate deterministic taxonomy-backed smoke/training augmentation records."""

from __future__ import annotations

import argparse
import json
import os
import random
import re
from collections import defaultdict
from typing import Any, Literal

from skillmap.domain.taxonomy import domain_label, flatten_taxonomy
from training.common import ROOT, load_config, read_jsonl, stable_id, write_json, write_jsonl
from training.privacy import assert_no_pii
from training.schemas import CanonicalDocument, Entity, MatchPair

SENIORITY = (
    "Intern",
    "Entry level",
    "Junior",
    "Mid-level",
    "Senior",
    "Lead",
    "Manager",
    "Director",
)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _taxonomy(config: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    prepared = read_jsonl("data/processed/taxonomy_concepts.jsonl")
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for concept in prepared:
        group = concept.get("occupation_group") or concept.get("taxonomy")
        grouped[str(group)].append(concept)
    usable = {key: values for key, values in grouped.items() if len(values) >= 6}
    if usable:
        return usable
    if not config.get("allow_legacy_taxonomy_for_smoke"):
        raise ValueError("Prepared ESCO/O*NET concepts are required outside smoke mode")
    taxonomy = json.loads((ROOT / "skillmap/ml/data/powerSkills.json").read_text(encoding="utf-8"))
    return {
        domain_label(key): [
            {
                "preferred_label": skill,
                "taxonomy": "SkillMap legacy smoke taxonomy",
                "taxonomy_id": f"skillmap:{_slug(skill)}",
            }
            for skill in sorted(set(flatten_taxonomy(value)))
        ]
        for key, value in taxonomy.items()
        if len(set(flatten_taxonomy(value))) >= 6
    }


def _entities(text: str, concepts: list[dict[str, str]]) -> list[Entity]:
    entities = []
    cursor = 0
    for concept in concepts:
        name = concept["preferred_label"]
        start = text.lower().find(name.lower(), cursor)
        if start < 0:
            start = text.lower().find(name.lower())
        if start < 0:
            continue
        end = start + len(name)
        entities.append(
            Entity(
                text=text[start:end],
                normalized_name=name,
                taxonomy=concept["taxonomy"],
                taxonomy_id=concept["taxonomy_id"],
                category="SKILL",
                start=start,
                end=end,
                confidence=1,
                evidence=text[start:end],
                mapping_method="generated_from_taxonomy",
            )
        )
        cursor = end
    return entities


def _label(
    score: float,
) -> Literal["STRONG_MATCH", "POTENTIAL_MATCH", "WEAK_MATCH", "NOT_MATCH"]:
    if score >= 80:
        return "STRONG_MATCH"
    if score >= 60:
        return "POTENTIAL_MATCH"
    if score >= 35:
        return "WEAK_MATCH"
    return "NOT_MATCH"


def _pair(
    profile: CanonicalDocument,
    job: CanonicalDocument,
    *,
    occupation: str,
    group_id: str,
    hard_negative: bool,
) -> MatchPair:
    resume_ids = {skill.taxonomy_id for skill in profile.skills}
    required = [skill.taxonomy_id for skill in job.skills[:5]]
    preferred = [skill.taxonomy_id for skill in job.skills[5:]]
    required_coverage = sum(identifier in resume_ids for identifier in required) / max(
        len(required), 1
    )
    preferred_coverage = sum(identifier in resume_ids for identifier in preferred) / max(
        len(preferred), 1
    )
    experience = 1.0 if profile.seniority == job.seniority else 0.6
    occupation_alignment = 0.25 if hard_negative else 1.0
    critical_missing = required_coverage < 0.4
    final = 100 * (
        0.55 * required_coverage
        + 0.15 * preferred_coverage
        + 0.15 * experience
        + 0.15 * occupation_alignment
    )
    if critical_missing:
        final = min(final, 34)
    components = {
        "required_skills": round(required_coverage * 100, 2),
        "preferred_skills": round(preferred_coverage * 100, 2),
        "experience": round(experience * 100, 2),
        "occupation_alignment": round(occupation_alignment * 100, 2),
        "critical_missing": float(critical_missing),
    }
    return MatchPair(
        pair_id=f"pair-{stable_id(profile.document_id, job.document_id)}",
        resume_id=profile.document_id,
        job_id=job.document_id,
        group_id=group_id,
        occupation=occupation,
        resume_text=profile.text,
        job_text=job.text,
        component_labels=components,
        final_score=round(final, 2),
        label=_label(final),
        evidence=[
            f"Required skill coverage: {components['required_skills']:.0f}%.",
            f"Occupation alignment: {components['occupation_alignment']:.0f}%.",
        ],
        label_generation_method="transparent_taxonomy_rubric_v1",
        confidence="high",
        taxonomy_concepts=sorted(identifier for identifier in required + preferred if identifier),
        synthetic=True,
        hard_negative=hard_negative,
    )


def run(config: dict[str, Any]) -> dict[str, Any]:
    provider = os.getenv("DATA_GENERATION_PROVIDER", "template").lower()
    if provider not in {"template", "ollama", "openrouter"}:
        raise ValueError("DATA_GENERATION_PROVIDER must be template, ollama, or openrouter")
    # External providers may paraphrase only these synthetic seeds in the dedicated scripts.
    # The core generator remains deterministic so labels are reproducible.
    taxonomy = _taxonomy(config)
    occupations = sorted(taxonomy)
    count = int(config.get("synthetic_profiles", 32))
    rng = random.Random(int(config.get("seed", 42)))  # nosec B311
    profiles: list[CanonicalDocument] = []
    jobs: list[CanonicalDocument] = []
    for index in range(count):
        occupation = occupations[index % len(occupations)]
        concepts = taxonomy[occupation]
        selected = [concepts[(index + offset) % len(concepts)] for offset in range(7)]
        seniority = SENIORITY[index % len(SENIORITY)]
        years = max(0, index % 12)
        style = index % 3
        if style == 0:
            resume_text = (
                f"Summary\n{seniority} {occupation} professional.\nExperience\n"
                f"{years} years delivering projects with {', '.join(c['preferred_label'] for c in selected[:6])}."
            )
        elif style == 1:
            resume_text = (
                f"EXPERIENCE • {occupation} • {years} years\n"
                f"Built and improved work using {'; '.join(c['preferred_label'] for c in selected[:6])}.\n"
                f"LEVEL: {seniority}"
            )
        else:
            resume_text = (
                f"{occupation} | {seniority}\nSkills: {', '.join(c['preferred_label'] for c in selected[:6])}\n"
                f"Evidence: applied these capabilities across {years} years of relevant projects."
            )
        job_text = (
            f"{seniority} {occupation}\nRequired skills: {', '.join(c['preferred_label'] for c in selected[:5])}.\n"
            f"Preferred skills: {', '.join(c['preferred_label'] for c in selected[5:])}.\n"
            f"Minimum experience: {max(0, years - 1)} years. Responsibilities are location-neutral."
        )
        assert_no_pii(resume_text)
        assert_no_pii(job_text)
        family = f"synthetic-family-{index:05d}"
        profiles.append(
            CanonicalDocument(
                document_id=f"resume-{stable_id(family, occupation)}",
                document_type="resume",
                text=resume_text,
                sections=[{"name": "experience"}, {"name": "skills"}],
                skills=_entities(resume_text, selected[:6]),
                occupations=[{"name": occupation}],
                experience=[{"years": years}],
                seniority=seniority,
                source_dataset="skillmap_template_synthetic",
                family_id=family,
                synthetic=True,
            )
        )
        jobs.append(
            CanonicalDocument(
                document_id=f"job-{stable_id(family, occupation)}",
                document_type="job",
                text=job_text,
                sections=[{"name": "required_skills"}, {"name": "preferred_skills"}],
                skills=_entities(job_text, selected),
                occupations=[{"name": occupation}],
                experience=[{"minimum_years": max(0, years - 1)}],
                seniority=seniority,
                source_dataset="skillmap_template_synthetic",
                family_id=family,
                synthetic=True,
            )
        )

    pairs: list[MatchPair] = []
    hard_negative_jobs: list[CanonicalDocument] = []
    for index, profile in enumerate(profiles):
        family = profile.family_id or profile.document_id
        occupation = profile.occupations[0]["name"]
        pairs.append(
            _pair(profile, jobs[index], occupation=occupation, group_id=family, hard_negative=False)
        )
        source_negative = jobs[(index + max(1, len(jobs) // 2)) % len(jobs)]
        negative_concepts = [
            {
                "preferred_label": entity.normalized_name or entity.text,
                "taxonomy": entity.taxonomy or "unknown",
                "taxonomy_id": entity.taxonomy_id or f"unknown:{_slug(entity.text)}",
            }
            for entity in source_negative.skills
        ]
        negative_text = (
            f"Opportunity: {source_negative.occupations[0]['name']}\n"
            f"The role owns operational outcomes and uses {' | '.join(c['preferred_label'] for c in negative_concepts[:5])}.\n"
            f"Additional capability: {', '.join(c['preferred_label'] for c in negative_concepts[5:])}. "
            f"Evidence of {index % 10} years in this occupation is requested."
        )
        negative_job = CanonicalDocument(
            document_id=f"job-hard-negative-{stable_id(family, source_negative.document_id)}",
            document_type="job",
            text=negative_text,
            sections=[{"name": "requirements"}],
            skills=_entities(negative_text, negative_concepts),
            occupations=source_negative.occupations,
            experience=[{"minimum_years": index % 10}],
            seniority=source_negative.seniority,
            source_dataset="skillmap_template_synthetic",
            family_id=family,
            synthetic=True,
        )
        hard_negative_jobs.append(negative_job)
        pairs.append(
            _pair(profile, negative_job, occupation=occupation, group_id=family, hard_negative=True)
        )

    # Shuffle record order only; content and labels remain deterministic.
    rng.shuffle(pairs)
    write_jsonl("data/synthetic/profiles.jsonl", (row.model_dump(mode="json") for row in profiles))
    write_jsonl(
        "data/synthetic/jobs.jsonl",
        (row.model_dump(mode="json") for row in [*jobs, *hard_negative_jobs]),
    )
    write_jsonl(
        "data/synthetic/matching_pairs.jsonl", (row.model_dump(mode="json") for row in pairs)
    )
    report = {
        "provider": provider,
        "profiles": len(profiles),
        "jobs": len(jobs) + len(hard_negative_jobs),
        "pairs": len(pairs),
        "hard_negatives": sum(pair.hard_negative for pair in pairs),
        "real_records": 0,
        "evaluation_approved": False,
    }
    write_json("reports/synthetic_generation_report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/training/smoke_test.yaml")
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
