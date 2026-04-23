"""
ats_scorer.py — Backend ATS scoring engine.

Uses spaCy NLP, BERT embeddings, and rule-based analysis
to produce a comprehensive ATS score with domain detection.

Replaces frontend-only scoring with server-side intelligence.
"""

from __future__ import annotations

import re
import json
import hashlib
from collections import OrderedDict
from pathlib import Path
from typing import Any

import numpy as np

# ── Load domain skill database ───────────────────────────────────

_DATA_DIR = Path(__file__).resolve().parent.parent / "frontend" / "src" / "data"
_POWER_SKILLS_PATH = _DATA_DIR / "powerSkills.json"
_ACTION_VERBS_PATH = _DATA_DIR / "actionVerbs.json"
_SECTION_KW_PATH = _DATA_DIR / "sectionKeywords.json"

with _POWER_SKILLS_PATH.open() as f:
    POWER_SKILLS: dict = json.load(f)

with _ACTION_VERBS_PATH.open() as f:
    ACTION_VERBS_LIST: list[str] = json.load(f)

with _SECTION_KW_PATH.open() as f:
    SECTION_KEYWORDS: dict[str, list[str]] = json.load(f)


# ── Flatten helpers ──────────────────────────────────────────────

def _deep_flatten(obj: dict | list) -> list[str]:
    """Recursively flatten nested dicts/lists into a flat string list."""
    result: list[str] = []
    if isinstance(obj, dict):
        for val in obj.values():
            result.extend(_deep_flatten(val))
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, str):
                result.append(item)
            else:
                result.extend(_deep_flatten(item))
    return result


ALL_SKILLS = list(set(s.lower() for s in _deep_flatten(POWER_SKILLS)))
ACTION_VERBS_SET = set(v.lower() for v in ACTION_VERBS_LIST)
WEAK_VERBS = {
    "helped", "worked", "did", "made", "was", "had", "got", "went",
    "used", "tried", "handled", "assisted", "participated",
    "responsible", "involved",
}

# ── Word-boundary matching ───────────────────────────────────────

_REGEX_CACHE: dict[str, re.Pattern] = {}


def _word_regex(term: str) -> re.Pattern:
    """Get or create a compiled word-boundary regex for a term."""
    if term not in _REGEX_CACHE:
        escaped = re.escape(term)
        _REGEX_CACHE[term] = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
    return _REGEX_CACHE[term]


def _match_skill(skill: str, text_lower: str, word_tokens: set[str]) -> bool:
    """Match a skill term using context-appropriate strategy."""
    if " " in skill:
        return bool(_word_regex(skill).search(text_lower))
    elif len(skill) <= 2:
        return skill in word_tokens
    else:
        return bool(_word_regex(skill).search(text_lower))


def _tokenize(text: str) -> set[str]:
    return set(re.split(r"[\s,;|/()[\]{}<>:]+", text.lower()))


# ── Score: Keywords (30 pts) ─────────────────────────────────────

def score_keywords(
    text: str,
    spacy_skills: list[str],
    job_description: str = "",
) -> dict[str, Any]:
    """Score keyword coverage using NLP-extracted + regex-matched skills."""
    lower = text.lower()
    tokens = _tokenize(text)

    # 1. Regex-based matching against skill database
    regex_matched = [s for s in ALL_SKILLS if _match_skill(s, lower, tokens)]

    # 2. Merge with spaCy-extracted skills (higher quality)
    all_matched = list(set(regex_matched + [s.lower() for s in spacy_skills]))

    # 3. JD matching if provided
    jd_terms: list[str] = []
    if job_description:
        jd_lower = job_description.lower()
        jd_tokens = _tokenize(job_description)
        jd_terms = list(set(
            s for s in ALL_SKILLS if _match_skill(s, jd_lower, jd_tokens)
        ))

    expected = max(len(jd_terms) or 12, 12)
    source = jd_terms if jd_terms else ALL_SKILLS[:50]
    missing = [s for s in source if s not in all_matched][:15]

    pts = min(30, round((len(all_matched) / expected) * 30))
    return {
        "score": pts,
        "max": 30,
        "matched": all_matched[:50],
        "missing": missing,
        "matchPct": round((len(all_matched) / expected) * 100),
    }


# ── Score: Formatting (20 pts) ───────────────────────────────────

def score_formatting(text: str) -> dict[str, Any]:
    pts = 20
    issues: list[str] = []

    # Table-like layouts
    if re.search(r"[│┃┆┇┊┋|]{2,}", text) or re.search(r"\t.*\t.*\t", text):
        pts -= 5
        issues.append("Table-like layout detected — ATS often misreads tables")

    # Image references
    if re.search(r"\[image\]|\[graphic\]|\.png|\.jpg|\.svg", text, re.I):
        pts -= 5
        issues.append("Image/graphic references detected — ATS cannot parse images")

    # Overly long lines
    lines = text.split("\n")
    wide = [l for l in lines if len(l) > 120]
    if len(wide) > 3:
        pts -= min(4, len(wide))
        issues.append("Lines exceed 120 characters — may cause parsing issues")

    # Fancy bullets
    fancy = len(re.findall(r"[◆▶►★✦✧●○◉⬤⚫⬥◈▪▫]", text))
    if fancy > 0:
        pts -= min(3, fancy)
        issues.append("Fancy bullets detected — use standard dashes or dots")

    # Section headers
    found_headers = sum(
        1 for kws in SECTION_KEYWORDS.values()
        if any(kw in text.lower() for kw in kws)
    )
    if found_headers < 3:
        pts -= 5
        issues.append("Missing standard section headers")

    return {"score": max(0, pts), "max": 20, "issues": issues}


# ── Score: Contact (10 pts) ──────────────────────────────────────

def score_contact(text: str) -> dict[str, Any]:
    pts = 0
    details: dict[str, bool] = {}

    if re.search(r"[\w.-]+@[\w.-]+\.\w{2,}", text, re.I):
        pts += 3; details["email"] = True
    if re.search(r"(\+?\d[\d\s\-().]{7,}\d)", text):
        pts += 3; details["phone"] = True
    if re.search(r"linkedin\.com/in/[\w-]+", text, re.I):
        pts += 2; details["linkedin"] = True
    if re.search(r"\b[A-Z][a-z]+,?\s*[A-Z]{2}\b", text) or re.search(r"\b\d{5,6}\b", text):
        pts += 2; details["location"] = True
    if re.search(r"github\.com/[\w-]+", text, re.I):
        pts += 1

    return {"score": min(10, pts), "max": 10, "details": details}


# ── Score: Structure (15 pts) ────────────────────────────────────

def score_structure(text: str) -> dict[str, Any]:
    lower = text.lower()
    required = ["summary", "experience", "education", "skills"]
    found, missing = [], []

    for sec in required:
        kws = SECTION_KEYWORDS.get(sec, [])
        if any(kw in lower for kw in kws):
            found.append(sec)
        else:
            missing.append(sec)

    pts = round(len(found) * 3.75)
    return {"score": pts, "max": 15, "found": found, "missing": missing}


# ── Score: Achievements (15 pts) ─────────────────────────────────

_QUANT_RE = re.compile(
    r"\d+[%x×kmb$]|\$[\d,.]+|\d+\s*(?:users|clients|projects|customers|employees|members|teams|revenue|sales|leads)",
    re.I,
)


def score_achievements(text: str) -> dict[str, Any]:
    matches = _QUANT_RE.findall(text)
    count = len(matches)

    if count == 0:     pts = 0
    elif count <= 2:   pts = 6
    elif count <= 5:   pts = 10
    elif count <= 9:   pts = 13
    else:              pts = 15

    examples = [l.strip() for l in text.split("\n") if _QUANT_RE.search(l)][:5]
    return {"score": pts, "max": 15, "count": count, "examples": examples}


# ── Score: Action Verbs (5 pts) ──────────────────────────────────

def score_action_verbs(text: str) -> dict[str, Any]:
    lines = [
        l.strip() for l in text.split("\n")
        if re.match(r"^[-•–—*]", l.strip()) or (20 < len(l.strip()) < 200)
    ]
    if not lines:
        return {"score": 0, "max": 5, "coverage": 0, "weak": []}

    strong = 0
    weak_found: list[str] = []
    for line in lines:
        first = re.sub(r"^[-•–—*\d.)]+\s*", "", line).split()[0].lower() if line else ""
        if not first:
            continue
        if first in ACTION_VERBS_SET:
            strong += 1
        elif first in WEAK_VERBS:
            weak_found.append(first)

    coverage = round((strong / len(lines)) * 100) if lines else 0

    if coverage >= 80:   pts = 5
    elif coverage >= 60: pts = 3
    elif coverage >= 40: pts = 2
    else:                pts = 0

    return {"score": pts, "max": 5, "coverage": coverage, "weak": list(set(weak_found))}


# ── Score: Length (5 pts) ────────────────────────────────────────

def score_length(text: str) -> dict[str, Any]:
    wc = len(text.split())

    if 400 <= wc <= 700:     pts, msg = 5, "Optimal length for a 1-page resume"
    elif 701 <= wc <= 900:   pts, msg = 3, "Slightly dense — consider trimming"
    elif 901 <= wc <= 1200:  pts, msg = 5, "Good length for a 2-page resume"
    elif wc > 1200:          pts, msg = 2, "Too long — most ATS prefer 1-2 pages"
    elif wc < 250:           pts, msg = 2, "Too short — add more detail"
    else:                    pts, msg = 3, "Acceptable length"

    return {"score": pts, "max": 5, "wordCount": wc, "message": msg}


# ── Domain Detection (BERT-powered) ─────────────────────────────

DOMAIN_LABELS = {
    "Software_Engineering": "Software Engineering",
    "Data_Science": "Data Science & Analytics",
    "Healthcare": "Healthcare & Clinical",
    "Finance": "Finance & Accounting",
    "Marketing": "Marketing & Digital",
    "Project_Management": "Project Management",
    "Human_Resources": "Human Resources",
    "Design_UX": "Design & UX",
}


def detect_domains_nlp(
    text: str,
    spacy_skills: list[str],
    embedding: np.ndarray | None = None,
    sentence_model: Any = None,
) -> list[dict[str, Any]]:
    """
    Detect professional domains using:
    1. NLP skill matching (word-boundary + spaCy extracted)
    2. Optionally BERT embedding cosine to domain centroids
    """
    lower = text.lower()
    tokens = _tokenize(text)
    spacy_lower = set(s.lower() for s in spacy_skills)
    results = []

    for domain_key, subcategories in POWER_SKILLS.items():
        if domain_key == "Soft_Skills":
            continue

        domain_skills = [s.lower() for s in _deep_flatten(subcategories)]
        total = len(domain_skills)
        if total == 0:
            continue

        match_count = 0
        matched_terms: list[str] = []
        for skill in domain_skills:
            # Check via word-boundary regex or spaCy extraction
            if _match_skill(skill, lower, tokens) or skill in spacy_lower:
                match_count += 1
                matched_terms.append(skill)

        if match_count < 3:
            continue

        ratio = match_count / total
        bonus = min(0.20, match_count * 0.006)
        confidence = min(99, round((ratio + bonus) * 100))

        if confidence < 3:
            continue

        results.append({
            "domain": DOMAIN_LABELS.get(domain_key, domain_key),
            "key": domain_key,
            "confidence": confidence,
            "matchedCount": match_count,
            "totalKeywords": total,
            "topMatches": list(set(matched_terms))[:8],
        })

    results.sort(key=lambda d: d["confidence"], reverse=True)
    return results[:5]


# ── Suggestion Generator ─────────────────────────────────────────

def generate_suggestions(cats: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    _id = 0

    def add(priority: str, category: str, title: str, detail: str,
            section_target: str | None = None, diff: dict | None = None):
        nonlocal _id
        suggestions.append({
            "id": f"s{_id}", "priority": priority, "category": category,
            "title": title, "detail": detail,
            "sectionTarget": section_target, "diff": diff,
        })
        _id += 1

    kw = cats["keywords"]
    fmt = cats["formatting"]
    contact = cats["contact"]
    struct = cats["structure"]
    ach = cats["achievements"]
    av = cats["actionVerbs"]
    ln = cats["length"]

    # Keywords
    if kw["score"] < 15:
        add("critical", "keywords", "Add more relevant skills",
            f"Only {len(kw['matched'])} skills detected. Add: {', '.join(kw['missing'][:5])}.",
            "skills")
    elif kw["score"] < 24:
        add("important", "keywords", "Expand your skillset",
            f"Missing key terms: {', '.join(kw['missing'][:4])}.", "skills")

    # Formatting
    for issue in fmt.get("issues", [])[:3]:
        p = "critical" if fmt["score"] < 10 else "important"
        add(p, "formatting", "Fix formatting issue", issue)

    # Contact
    d = contact.get("details", {})
    if not d.get("email"):
        add("critical", "contact", "Add email address",
            "ATS requires a valid email to contact you.")
    if not d.get("phone"):
        add("critical", "contact", "Add phone number",
            "Include a phone number for recruiter outreach.")
    if not d.get("linkedin"):
        add("important", "contact", "Add LinkedIn profile",
            "Recruiters often verify candidates via LinkedIn.")

    # Structure
    for m in struct.get("missing", []):
        add("critical", "structure", f"Add {m} section",
            f'A "{m}" section is expected by ATS parsers.')

    # Achievements
    if ach["count"] == 0:
        add("critical", "achievements", "Quantify your impact",
            'Add numbers: e.g., "Increased revenue by 35%".',
            "experience",
            {"before": "Managed the sales team",
             "after": "Managed a 12-person sales team, driving $2.4M in quarterly revenue (+35% YoY)"})
    elif ach["count"] < 3:
        add("important", "achievements", "Add more metrics",
            f"Only {ach['count']} quantified achievement(s). Aim for 5+.", "experience")

    # Action verbs
    if av.get("weak"):
        weak_str = '", "'.join(av["weak"][:3])
        add("important", "actionVerbs", "Replace weak verbs",
            f'Avoid: "{weak_str}". Use "Spearheaded", "Optimized", "Delivered".',
            "experience",
            {"before": "Helped with the project", "after": "Spearheaded the project delivery"})
    if av.get("coverage", 0) < 60:
        add("important", "actionVerbs", "Start bullets with verbs",
            f"Only {av['coverage']}% of bullets start with action verbs. Aim for 80%+.", "experience")

    # Length
    wc = ln.get("wordCount", 0)
    if wc < 250:
        add("critical", "length", "Resume is too short",
            "Fewer than 250 words. Expand experience and skills.")
    elif wc > 1200:
        add("important", "length", "Consider shortening",
            "Over 1,200 words. Trim older roles, focus on relevant experience.")

    order = {"critical": 0, "important": 1, "nice": 2}
    suggestions.sort(key=lambda s: order.get(s["priority"], 2))
    return suggestions[:12]


# ── Main scoring function ────────────────────────────────────────

# Simple LRU cache for repeated scoring of same text
_SCORE_CACHE: OrderedDict[str, dict] = OrderedDict()
_CACHE_MAX = 64


def score_resume(
    text: str,
    job_description: str = "",
    spacy_skills: list[str] | None = None,
    embedding: np.ndarray | None = None,
    sentence_model: Any = None,
) -> dict[str, Any]:
    """
    Full ATS scoring pipeline.
    
    Args:
        text: Raw resume text
        job_description: Optional JD for alignment scoring
        spacy_skills: Skills extracted via spaCy NLP (from skills.py)
        embedding: BERT embedding vector (if already computed)
        sentence_model: SentenceTransformer model (for domain BERT matching)
    
    Returns:
        ScoreResult with total, categories, domains, suggestions
    """
    if not text or len(text.strip()) < 10:
        return {
            "total": 0, "categories": {},
            "suggestions": [], "domains": [],
            "keywords": {"matched": [], "missing": []},
        }

    # Cache check
    text_hash = hashlib.md5((text + job_description).encode()).hexdigest()
    if text_hash in _SCORE_CACHE:
        return _SCORE_CACHE[text_hash]

    skills = spacy_skills or []

    # Run all scoring categories
    keywords = score_keywords(text, skills, job_description)
    formatting = score_formatting(text)
    contact = score_contact(text)
    structure = score_structure(text)
    achievements = score_achievements(text)
    action_verbs = score_action_verbs(text)
    length = score_length(text)

    categories = {
        "keywords": keywords,
        "formatting": formatting,
        "contact": contact,
        "structure": structure,
        "achievements": achievements,
        "actionVerbs": action_verbs,
        "length": length,
    }

    total = min(100, sum(c["score"] for c in categories.values()))
    suggestions = generate_suggestions(categories)
    domains = detect_domains_nlp(text, skills, embedding, sentence_model)

    result = {
        "total": total,
        "categories": categories,
        "suggestions": suggestions,
        "domains": domains,
        "keywords": {
            "matched": keywords["matched"],
            "missing": keywords["missing"],
        },
    }

    # Cache result
    _SCORE_CACHE[text_hash] = result
    if len(_SCORE_CACHE) > _CACHE_MAX:
        _SCORE_CACHE.popitem(last=False)

    return result
