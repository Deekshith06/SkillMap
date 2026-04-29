"""
skills.py — Skill extraction and scoring engine.

Uses spaCy noun-chunk + NER extraction, filtered against an embedded
ESCO-derived tech/skill vocabulary. NO keyword matching — skills are
scored by frequency × positional weight (earlier mentions rank higher).

All functions carry full type hints (Python 3.10+ syntax).
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import spacy

# ── Load spaCy model ─────────────────────────────────────────────
try:
    _nlp = spacy.load("en_core_web_sm", disable=["lemmatizer"])
except OSError:
    import subprocess
    import sys

    subprocess.check_call(
        [sys.executable, "-m", "spacy", "download", "en_core_web_sm"]
    )
    _nlp = spacy.load("en_core_web_sm", disable=["lemmatizer"])


# ── ESCO skill vocabulary subset (embedded JSON) ────────────────
# This is a curated subset covering common tech / professional skills
# derived from the European Skills, Competences, Qualifications and
# Occupations (ESCO) taxonomy.  Embedded to avoid external API calls.

_ESCO_SKILLS_PATH = Path(__file__).parent / "esco_skills.json"

# Build a runtime set from the embedded asset, or fallback to a
# hardcoded core set if the JSON file isn't present.

_CORE_SKILLS: set[str] = {
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go",
    "rust", "ruby", "swift", "kotlin", "scala", "r", "matlab", "php",
    "perl", "sql", "html", "css", "sass", "less", "shell", "bash",
    "powershell", "objective-c", "dart", "lua", "haskell", "elixir",
    # Frameworks & libraries
    "react", "angular", "vue", "svelte", "next.js", "nuxt", "django",
    "flask", "fastapi", "spring", "express", "node.js", "rails",
    "laravel", ".net", "asp.net", "bootstrap", "tailwind", "jquery",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "matplotlib", "seaborn", "plotly", "opencv", "spacy", "nltk",
    "hugging face", "transformers", "langchain",
    # Cloud & infra
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
    "terraform", "ansible", "jenkins", "github actions", "ci/cd",
    "circleci", "travis ci", "gitlab ci", "nginx", "apache",
    "linux", "unix", "windows server",
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "sqlite", "oracle", "sql server",
    "firebase", "supabase", "neo4j", "graphql", "rest api",
    # Data & ML
    "machine learning", "deep learning", "natural language processing",
    "computer vision", "data science", "data engineering",
    "data analysis", "data visualization", "big data", "spark",
    "hadoop", "airflow", "kafka", "etl", "power bi", "tableau",
    "looker", "dbt", "snowflake", "databricks", "mlflow",
    "feature engineering", "model deployment", "a/b testing",
    # DevOps & SRE
    "devops", "site reliability", "monitoring", "prometheus",
    "grafana", "datadog", "new relic", "splunk", "elk stack",
    "load balancing", "microservices", "serverless",
    # Security
    "cybersecurity", "penetration testing", "siem", "soc",
    "vulnerability assessment", "encryption", "oauth", "sso",
    "identity management", "compliance", "gdpr", "hipaa",
    # Design & UX
    "figma", "sketch", "adobe xd", "photoshop", "illustrator",
    "indesign", "ui design", "ux design", "user research",
    "wireframing", "prototyping", "design systems",
    # Project & business
    "agile", "scrum", "kanban", "jira", "confluence", "trello",
    "project management", "product management", "stakeholder management",
    "risk management", "budgeting", "strategic planning",
    "business analysis", "requirements gathering",
    # Soft / professional
    "communication", "leadership", "teamwork", "problem solving",
    "critical thinking", "time management", "presentation",
    "negotiation", "mentoring", "coaching",
    # HR & operations
    "recruiting", "talent acquisition", "onboarding",
    "performance management", "employee relations",
    "compensation", "benefits administration", "hris",
    "payroll", "training and development", "organizational development",
    "supply chain", "logistics", "procurement", "inventory management",
    # Finance & accounting
    "financial analysis", "accounting", "bookkeeping", "auditing",
    "tax preparation", "forecasting", "budgeting",
    "accounts payable", "accounts receivable", "sap", "erp",
    # Marketing & sales
    "digital marketing", "seo", "sem", "content marketing",
    "social media marketing", "email marketing", "crm",
    "salesforce", "hubspot", "google analytics", "market research",
    "brand management", "copywriting", "public relations",
    # Healthcare & science
    "clinical research", "patient care", "medical terminology",
    "ehr", "fda regulations", "gmp", "laboratory skills",
    "biostatistics", "epidemiology",
    # Education
    "curriculum development", "instructional design",
    "classroom management", "assessment", "e-learning",
    # Legal
    "contract management", "intellectual property", "regulatory compliance",
    "legal research", "litigation",
    # Engineering & manufacturing
    "autocad", "solidworks", "cad", "cam", "plc programming",
    "quality control", "lean manufacturing", "six sigma",
    "iso 9001", "mechanical design",
    # Certifications (commonly listed as skills)
    "pmp", "aws certified", "azure certified", "cissp", "ceh",
    "comptia", "ccna", "cpa", "cfa", "shrm",
}

# Try loading the external JSON if available
if _ESCO_SKILLS_PATH.exists():
    try:
        with _ESCO_SKILLS_PATH.open("r", encoding="utf-8") as _f:
            _external: list[str] = json.load(_f)
        _CORE_SKILLS.update(s.lower().strip() for s in _external if s.strip())
    except (json.JSONDecodeError, TypeError):
        pass  # Fallback to hardcoded set

_SKILL_SET = frozenset(_CORE_SKILLS)

# ── Stopwords for filtering ──────────────────────────────────────

_STOP_CHUNKS: set[str] = {
    "city", "state", "company", "company name", "university",
    "college", "school", "date", "year", "years", "month",
    "experience", "work", "job", "position", "role", "summary",
    "objective", "reference", "name", "address", "email", "phone",
    "education", "skills", "skill", "highlights", "accomplishments",
    "n/a", "current", "responsibilities", "duties",
}

_MULTI_WS_RE = re.compile(r"\s+")


# ── Core extraction logic ────────────────────────────────────────


def _normalise(text: str) -> str:
    """Lowercase, collapse whitespace, strip."""
    return _MULTI_WS_RE.sub(" ", text.lower()).strip()


def _is_valid_chunk(text: str) -> bool:
    """Filter out noise chunks."""
    if not text or len(text) < 2 or len(text) > 60:
        return False
    if text in _STOP_CHUNKS:
        return False
    if text.replace(" ", "").isdigit():
        return False
    return True


def extract_skills(
    cleaned_text: str,
    max_skills: int = 15,
) -> list[dict[str, Any]]:
    """
    Extract skills from cleaned resume text using spaCy NLP.

    Returns up to *max_skills* entries, each shaped:
        { "name": str, "confidence": float, "frequency": int }

    Scoring: frequency × positional_weight (earlier = higher).
    """
    if not cleaned_text or not cleaned_text.strip():
        return []

    doc = _nlp(cleaned_text[:100_000])  # Cap to avoid OOM

    candidates: Counter[str] = Counter()
    positions: dict[str, int] = {}  # first occurrence position
    total_chars = max(len(cleaned_text), 1)

    # ── Noun chunks ──────────────────────────────────────────
    for chunk in doc.noun_chunks:
        phrase = _normalise(chunk.text)
        if _is_valid_chunk(phrase) and phrase in _SKILL_SET:
            candidates[phrase] += 1
            if phrase not in positions:
                positions[phrase] = chunk.start_char

    # ── Named entities ───────────────────────────────────────
    for ent in doc.ents:
        phrase = _normalise(ent.text)
        if _is_valid_chunk(phrase) and phrase in _SKILL_SET:
            candidates[phrase] += 1
            if phrase not in positions:
                positions[phrase] = ent.start_char

    # ── Also check individual tokens for single-word skills ──
    for token in doc:
        word = _normalise(token.text)
        if len(word) >= 2 and word in _SKILL_SET and _is_valid_chunk(word):
            candidates[word] += 1
            if word not in positions:
                positions[word] = token.idx

    if not candidates:
        return []

    # ── Score: frequency × positional weight ─────────────────
    scored: list[tuple[str, float, int]] = []
    max_freq = max(candidates.values()) if candidates else 1

    for skill, freq in candidates.items():
        pos = positions.get(skill, total_chars)
        positional_weight = 1.0 - (pos / total_chars) * 0.5  # 1.0→0.5
        normalised_freq = freq / max_freq
        score = normalised_freq * positional_weight
        scored.append((skill, round(score, 4), freq))

    scored.sort(key=lambda x: x[1], reverse=True)

    return [
        {
            "name": name,
            "confidence": min(score, 1.0),
            "frequency": freq,
        }
        for name, score, freq in scored[:max_skills]
    ]


def extract_skill_names(cleaned_text: str, max_skills: int = 15) -> list[str]:
    """Convenience: return just the skill name strings."""
    return [s["name"] for s in extract_skills(cleaned_text, max_skills)]
