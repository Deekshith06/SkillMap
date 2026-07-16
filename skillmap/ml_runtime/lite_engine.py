"""Low-memory taxonomy, TF-IDF, BM25, and deterministic rule inference."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from skillmap.adapters.artifact_repository import RuntimeAssets, load_runtime_assets
from skillmap.domain.models import MatchResult, PredictionResult
from skillmap.domain.scoring import score_match
from skillmap.domain.taxonomy import (
    domain_label,
    extract_taxonomy_skills,
    flatten_taxonomy,
    redact_pii,
)

_YEARS_RE = re.compile(r"\b(\d{1,2})\+?\s+years?\b", re.IGNORECASE)
_BEHAVIORAL_TERMS = (
    "leadership",
    "communication",
    "mentoring",
    "collaboration",
    "problem solving",
    "stakeholder management",
    "negotiation",
    "critical thinking",
)


class LiteEngine:
    def __init__(self, assets: RuntimeAssets | None = None) -> None:
        self.assets = assets or load_runtime_assets()
        self._domain_skills = {
            key: set(flatten_taxonomy(value)) for key, value in self.assets.taxonomy.items()
        }
        self._all_skills = sorted(set().union(*self._domain_skills.values()))
        self._clusters_by_label = {
            cluster.domain_label: cluster for cluster in self.assets.clusters
        }

    def _domain_evidence(self, text: str, skills: list[str]) -> list[dict[str, Any]]:
        counts = Counter(
            {
                key: len(set(skills) & domain_skills)
                for key, domain_skills in self._domain_skills.items()
            }
        )
        ranked = [(key, count) for key, count in counts.most_common() if count > 0]
        if not ranked:
            return []
        top_count = ranked[0][1]
        tied = [key for key, count in ranked if count == top_count]
        if len(tied) > 1:
            predicted = str(self.assets.classifier.predict([text])[0])
            if predicted in tied:
                ranked.sort(key=lambda item: (item[0] != predicted, -item[1], item[0]))
        total = sum(count for _, count in ranked)
        return [
            {
                "domain": domain_label(key),
                "key": key,
                "confidence": round(count / total * 100, 1),
                "matchedCount": count,
                "topMatches": sorted(set(skills) & self._domain_skills[key])[:8],
            }
            for key, count in ranked[:5]
        ]

    @staticmethod
    def _seniority(text: str) -> str:
        lowered = text.lower()
        years = [int(value) for value in _YEARS_RE.findall(lowered)]
        maximum = max(years, default=None)
        academic_lead = bool(
            re.search(
                r"\b(?:university|college|student|academic|capstone)\b.{0,60}\b(?:team )?lead\b|"
                r"\b(?:team )?lead\b.{0,60}\b(?:university|college|student|academic|capstone)\b",
                lowered,
            )
        )
        executive_evidence = bool(
            re.search(
                r"\b(strategy|department|organization|portfolio|budget|executive team)\b", lowered
            )
        )
        if re.search(r"\b(chief|vice president|vp|director|head of)\b", lowered) and (
            (maximum is not None and maximum >= 8) or executive_evidence
        ):
            return "Director / Executive"
        if re.search(r"\b(principal|staff|architect)\b", lowered) and (maximum or 0) >= 5:
            return "Principal / Architect"
        if (
            re.search(r"\b(lead|manager)\b", lowered)
            and not academic_lead
            and (
                (maximum or 0) >= 3
                or re.search(r"\b(managed|mentored|owned|stakeholder)\b", lowered)
            )
        ):
            return "Lead / Manager"
        if re.search(r"\b(senior|sr\.)\b", lowered):
            return "Senior"
        if re.search(r"\b(junior|jr\.|intern|graduate)\b", lowered):
            return "Junior / Entry-level"
        if maximum is not None:
            if maximum >= 8:
                return "Senior"
            if maximum >= 3:
                return "Mid-level"
            return "Junior / Entry-level"
        return "Not enough evidence"

    def analyze(self, text: str) -> PredictionResult:
        safe_text = redact_pii(text)
        skills = extract_taxonomy_skills(safe_text, self._all_skills, limit=30)
        domains = self._domain_evidence(safe_text, skills)
        if not domains:
            return PredictionResult(
                cluster_id=-1,
                cluster_name="Insufficient evidence",
                confidence=0.0,
                top_skills=[],
                domains=[],
                seniority=self._seniority(safe_text),
                behavioral_signals=[],
                adjacent_roles=[],
                evidence=["No supported taxonomy skills were found in the document."],
                model_version=self.assets.manifest.model_version,
                taxonomy_version=self.assets.manifest.taxonomy_version,
                scoring_mode="taxonomy",
                limitations=["No supported taxonomy evidence was found."],
            )

        primary = domains[0]
        cluster = self._clusters_by_label.get(primary["domain"])
        primary_count = int(primary["matchedCount"])
        share = float(primary["confidence"]) / 100
        evidence_strength = min(1.0, primary_count / 5) * share
        behavioral = [term.title() for term in _BEHAVIORAL_TERMS if term in safe_text.lower()][:5]
        return PredictionResult(
            cluster_id=cluster.id if cluster else -1,
            cluster_name=primary["domain"],
            confidence=round(evidence_strength, 4),
            top_skills=skills,
            domains=domains,
            seniority=self._seniority(safe_text),
            behavioral_signals=behavioral,
            adjacent_roles=cluster.example_roles[:5] if cluster else [],
            evidence=[
                f"{primary_count} explicit skills support {primary['domain']}.",
                "Direct identifiers were removed before classification.",
            ],
            model_version=self.assets.manifest.model_version,
            taxonomy_version=self.assets.manifest.taxonomy_version,
            scoring_mode="taxonomy",
            limitations=["Exact taxonomy matching may miss aliases and implicit skills."],
        )

    def match(self, resume_text: str, job_text: str) -> MatchResult:
        return score_match(
            resume_text,
            job_text,
            all_skills=self._all_skills,
            vectorizer=self.assets.vectorizer,
            model_version=self.assets.manifest.model_version,
            taxonomy_version=self.assets.manifest.taxonomy_version,
        )
