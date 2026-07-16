from __future__ import annotations

import json
from pathlib import Path

import pytest

from training.data.audit import REQUIRED_FIELDS
from training.data.deduplicate import cluster_texts
from training.data.split import grouped_split
from training.privacy import assert_no_pii, mask_pii
from training.schemas import CanonicalDocument, Entity, MatchPair, bio_spans


def test_dataset_registry_is_complete_and_unknown_data_is_rejected() -> None:
    registry = json.loads(Path("data/manifests/dataset_registry.yaml").read_text())["datasets"]

    assert registry
    assert all(row.keys() >= REQUIRED_FIELDS for row in registry)
    legacy = next(row for row in registry if row["name"] == "skillmap_resume_csv")
    assert legacy["license"] == "unknown"
    assert not any(
        legacy[key]
        for key in ("approved_for_training", "approved_for_validation", "approved_for_testing")
    )
    skillspan = next(row for row in registry if row["name"] == "skillspan")
    assert skillspan["version"] in skillspan["download_url"]
    assert "refs/heads" not in skillspan["download_url"]


def test_pii_is_typed_and_job_relevant_dates_are_preserved() -> None:
    text = "Name: Ada Example\nEmail: ada@example.com\nPhone: +91 9876543210\nExperience: 2018-2024"
    masked = mask_pii(text)

    assert "[NAME]" in masked
    assert "[EMAIL]" in masked
    assert "[PHONE]" in masked
    assert "2018-2024" in masked
    assert_no_pii(masked)


def test_exact_and_near_duplicates_share_a_cluster() -> None:
    labels = cluster_texts(
        [
            "Python engineer builds reliable REST APIs and data services.",
            "Python engineer builds reliable REST APIs and data services.",
            "Python engineer builds reliable REST APIs & data services.",
            "Nurse coordinates clinical patient care.",
        ],
        threshold=0.8,
    )

    assert labels[0] == labels[1] == labels[2]
    assert labels[3] != labels[0]


def test_grouped_split_never_crosses_families() -> None:
    rows = [{"group_id": f"family-{index // 2}", "row": index} for index in range(40)]
    splits = grouped_split(rows, {"train": 0.7, "validation": 0.15, "test": 0.15}, 42)
    membership: dict[str, set[str]] = {}
    for split_name, values in splits.items():
        for row in values:
            membership.setdefault(row["group_id"], set()).add(split_name)

    assert all(len(values) == 1 for values in membership.values())


def test_bio_alignment_and_schema_offsets() -> None:
    text, entities = bio_spans(
        ["Build", "REST", "APIs", "with", "Python"],
        ["O", "B-SKILL", "I-SKILL", "O", "B-SKILL"],
        "SKILL",
    )
    document = CanonicalDocument(
        document_id="example",
        document_type="sentence",
        text=text,
        skills=entities,
        source_dataset="test",
    )

    assert [entity.text for entity in document.skills] == ["REST APIs", "Python"]
    with pytest.raises(ValueError):
        bio_spans(["Python"], ["O", "B-SKILL"], "SKILL")


def test_canonical_schema_rejects_misaligned_span() -> None:
    with pytest.raises(ValueError, match="span does not match"):
        CanonicalDocument(
            document_id="bad",
            document_type="resume",
            text="Python",
            skills=[Entity(text="Java", category="SKILL", start=0, end=4)],
            source_dataset="test",
        )


def test_matching_pair_rejects_unbounded_score() -> None:
    with pytest.raises(ValueError):
        MatchPair(
            pair_id="p",
            resume_id="r",
            job_id="j",
            group_id="g",
            occupation="Engineer",
            resume_text="Python",
            job_text="Python",
            component_labels={},
            final_score=101,
            label="STRONG_MATCH",
            evidence=["test"],
            label_generation_method="test",
            confidence="high",
            taxonomy_concepts=[],
            synthetic=True,
        )
