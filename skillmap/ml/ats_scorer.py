"""
ats_scorer.py — ATS scoring engine.
Relocated from backend/ats_scorer.py; data path updated to project root.
"""
from __future__ import annotations

import re
import json
import hashlib
from collections import OrderedDict
from pathlib import Path
from typing import Any

import numpy as np

# ── Data paths (co-located with this module) ────────────────────
_DATA_DIR = Path(__file__).resolve().parent / "data"
_POWER_SKILLS_PATH = _DATA_DIR / "powerSkills.json"
_ACTION_VERBS_PATH = _DATA_DIR / "actionVerbs.json"
_SECTION_KW_PATH   = _DATA_DIR / "sectionKeywords.json"

with _POWER_SKILLS_PATH.open() as f:
    POWER_SKILLS: dict = json.load(f)

with _ACTION_VERBS_PATH.open() as f:
    ACTION_VERBS_LIST: list[str] = json.load(f)

with _SECTION_KW_PATH.open() as f:
    SECTION_KEYWORDS: dict[str, list[str]] = json.load(f)


def _deep_flatten(obj: dict | list) -> list[str]:
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
    "responsible", "involved",
}

SKILL_SYNONYMS: dict[str, str] = {
    "js": "javascript",
    "reactjs": "react",
    "nodejs": "node.js",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "ux": "user experience",
    "ui": "user interface",
    "hr": "human resources",
    "jd": "job description",
}

_REGEX_CACHE: dict[str, re.Pattern] = {}


def _word_regex(term: str) -> re.Pattern:
    if term not in _REGEX_CACHE:
        escaped = re.escape(term)
        _REGEX_CACHE[term] = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
    return _REGEX_CACHE[term]


def _match_skill(skill: str, text_lower: str, word_tokens: set[str]) -> bool:
    # Check exact match
    if " " in skill:
        if bool(_word_regex(skill).search(text_lower)):
            return True
    elif len(skill) <= 2:
        if skill in word_tokens:
            return True
    else:
        if bool(_word_regex(skill).search(text_lower)):
            return True
            
    # Check synonyms
    for syn, canonical in SKILL_SYNONYMS.items():
        if skill == canonical and syn in word_tokens:
            return True
        if skill == syn and canonical in text_lower:
            return True
            
    return False


def _tokenize(text: str) -> set[str]:
    return set(re.split(r"[\s,;|/()[\]{}<>:]+", text.lower()))


def score_keywords(text: str, spacy_skills: list[str], job_description: str = "", domains: list[dict] | None = None) -> dict[str, Any]:
    lower = text.lower()
    tokens = _tokenize(text)
    regex_matched = [s for s in ALL_SKILLS if _match_skill(s, lower, tokens)]
    all_matched = list(set(regex_matched + [s.lower() for s in spacy_skills]))
    jd_terms: list[str] = []
    if job_description:
        jd_lower = job_description.lower()
        jd_tokens = _tokenize(job_description)
        jd_terms = list(set(s for s in ALL_SKILLS if _match_skill(s, jd_lower, jd_tokens)))
    
    expected = max(len(jd_terms) or 15, 15)  # industry standard expects 15+ hard skills
    
    domain_skills = []
    if not jd_terms and domains and len(domains) > 0:
        top_domain_key = domains[0].get("key")
        if top_domain_key in POWER_SKILLS:
            domain_skills = list(set(s.lower() for s in _deep_flatten(POWER_SKILLS[top_domain_key])))
            
    source = jd_terms if jd_terms else (domain_skills if domain_skills else ALL_SKILLS[:50])
    missing = [s for s in source if s not in all_matched][:15]
    
    matched_count = len(all_matched)
    density = min(100.0, (matched_count / expected) * 100.0)
    pts = min(30, round((matched_count / expected) * 30))
    
    return {
        "score": pts, 
        "max": 30, 
        "matched": all_matched[:50], 
        "missing": missing,
        "matchPct": round(density)
    }


def score_formatting(text: str) -> dict[str, Any]:
    pts = 20
    issues: list[str] = []
    if re.search(r"[│┃┆┇┊┋|]{2,}", text) or re.search(r"\t.*\t.*\t", text):
        pts -= 5; issues.append("Table-like layout detected — ATS often misreads tables")
    if re.search(r"\[image\]|\[graphic\]|\.png|\.jpg|\.svg", text, re.I):
        pts -= 5; issues.append("Image/graphic references detected")
    lines = text.split("\n")
    wide = [l for l in lines if len(l) > 120]
    if len(wide) > 3:
        pts -= min(4, len(wide)); issues.append("Lines exceed 120 characters")
    fancy = len(re.findall(r"[◆▶►★✦✧●○◉⬤⚫⬥◈▪▫]", text))
    if fancy > 0:
        pts -= min(3, fancy); issues.append("Fancy bullets detected — use standard dashes")
    found_headers = sum(1 for kws in SECTION_KEYWORDS.values() if any(kw in text.lower() for kw in kws))
    if found_headers < 3:
        pts -= 5; issues.append("Missing standard section headers")
    return {"score": max(0, pts), "max": 20, "issues": issues}


def score_contact(text: str) -> dict[str, Any]:
    pts = 0; details: dict[str, bool] = {}
    if re.search(r"[\w.-]+@[\w.-]+\.\w{2,}", text, re.I): pts += 3; details["email"] = True
    if re.search(r"(\+?\d[\d\s\-().]{7,}\d)", text): pts += 3; details["phone"] = True
    if re.search(r"linkedin\.com/in/[\w-]+", text, re.I): pts += 2; details["linkedin"] = True
    if re.search(r"\b[A-Z][a-z]+,?\s*[A-Z]{2}\b", text) or re.search(r"\b\d{5,6}\b", text):
        pts += 2; details["location"] = True
    return {"score": min(10, pts), "max": 10, "details": details}


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
    return {"score": round(len(found) * 3.75), "max": 15, "found": found, "missing": missing}


_QUANT_RE = re.compile(
    r"\d+[%x×kmb$]|\$[\d,.]+|\d+\s*(?:users|clients|projects|customers|employees|members|teams|revenue|sales|leads)",
    re.I,
)


def score_achievements(text: str) -> dict[str, Any]:
    matches = _QUANT_RE.findall(text)
    count = len(matches)
    if count == 0: pts = 0
    elif count <= 2: pts = 6
    elif count <= 5: pts = 10
    elif count <= 9: pts = 13
    else: pts = 15
    examples = [l.strip() for l in text.split("\n") if _QUANT_RE.search(l)][:5]
    return {"score": pts, "max": 15, "count": count, "examples": examples}


def score_action_verbs(text: str) -> dict[str, Any]:
    lines = [l.strip() for l in text.split("\n")
             if re.match(r"^[-•–—*]", l.strip()) or (20 < len(l.strip()) < 200)]
    if not lines:
        return {"score": 0, "max": 5, "coverage": 0, "weak": []}
    strong = 0; weak_found: list[str] = []
    for line in lines:
        first = re.sub(r"^[-•–—*\d.)]+\s*", "", line).split()[0].lower() if line else ""
        if not first: continue
        if first in ACTION_VERBS_SET: strong += 1
        elif first in WEAK_VERBS: weak_found.append(first)
    coverage = round((strong / len(lines)) * 100) if lines else 0
    if coverage >= 80: pts = 5
    elif coverage >= 60: pts = 3
    elif coverage >= 40: pts = 2
    else: pts = 0
    return {"score": pts, "max": 5, "coverage": coverage, "weak": list(set(weak_found))}


def score_length(text: str) -> dict[str, Any]:
    wc = len(text.split())
    if 400 <= wc <= 700: pts, msg = 5, "Optimal length for a 1-page resume"
    elif 701 <= wc <= 900: pts, msg = 3, "Slightly dense — consider trimming"
    elif 901 <= wc <= 1200: pts, msg = 5, "Good length for a 2-page resume"
    elif wc > 1200: pts, msg = 2, "Too long — most ATS prefer 1-2 pages"
    elif wc < 250: pts, msg = 2, "Too short — add more detail"
    else: pts, msg = 3, "Acceptable length"
    return {"score": pts, "max": 5, "wordCount": wc, "message": msg}


DOMAIN_LABELS = {
    "Computer_Science_CSE": "Computer Science (CSE)",
    "Electronics_Communication_ECE": "Electronics & Communication (ECE)",
    "Electrical_Engineering_EEE": "Electrical Engineering (EEE)",
    "Mechanical_Engineering": "Mechanical Engineering",
    "Civil_Engineering": "Civil Engineering",
    "Chemical_Engineering": "Chemical Engineering",
    "Healthcare": "Healthcare & Clinical",
    "Finance": "Finance & Accounting",
    "Marketing": "Marketing & Digital",
    "Project_Management": "Project Management",
    "Human_Resources": "Human Resources",
    "Design_UX": "Design & UX",
    "Education": "Education & Teaching",
    "Culinary": "Culinary & Chef",
    "Legal": "Legal & Law",
    "Logistics_Supply_Chain": "Logistics & Supply Chain",
    "Sales": "Sales & Business Development",
    "Aerospace_Engineering": "Aerospace Engineering",
    "Biomedical_Engineering": "Biomedical Engineering",
    "Industrial_Engineering": "Industrial Engineering",
}


def detect_domains_nlp(
    text: str,
    spacy_skills: list[str],
    embedding: Any = None,
    sentence_model: Any = None,
) -> list[dict[str, Any]]:
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
        match_count = 0; matched_terms: list[str] = []
        for skill in domain_skills:
            if _match_skill(skill, lower, tokens) or skill in spacy_lower:
                match_count += 1; matched_terms.append(skill)
        if match_count < 3:
            continue
        ratio = match_count / total
        bonus = min(0.20, match_count * 0.006)
        confidence = min(99, round((ratio + bonus) * 100))
        if confidence < 3:
            continue
            
        # Determine specific sub-domain based on detected keywords
        sub_domain = f"{DOMAIN_LABELS.get(domain_key, domain_key)} Professional"
        
        # CSE Sub-domains
        if domain_key == "Computer_Science_CSE":
            s_set = set([s.lower() for s in matched_terms])
            
            scores = {
                "MERN Stack Developer": len({"mongodb", "express", "react", "node.js", "nodejs"}.intersection(s_set)) * 1.5,
                "AI/ML Data Analyst": len({"pandas", "numpy", "machine learning", "tensorflow", "pytorch", "scikit-learn", "data science"}.intersection(s_set)),
                "Cybersecurity Specialist": len({"cybersecurity", "ethical hacking", "penetration testing", "network security", "firewalls"}.intersection(s_set)),
                "Cloud/DevOps Engineer": len({"aws", "docker", "kubernetes", "ci/cd", "terraform"}.intersection(s_set)),
                "React Specialist": len({"react", "reactjs"}.intersection(s_set)),
                "Frontend Developer": len({"angular", "vue", "javascript", "html", "css", "tailwind"}.intersection(s_set)) * 0.5,
                "Java Backend Developer": len({"java", "spring"}.intersection(s_set)),
                "Python Backend Developer": len({"python", "django", "flask"}.intersection(s_set)),
            }
            
            # Find the category with the highest score
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0:
                sub_domain = best_match[0]
            else:
                sub_domain = "Software Engineer"
                
        # ECE Sub-domains
        elif domain_key == "Electronics_Communication_ECE":
            s_set = set([s.lower() for s in matched_terms])
            scores = {
                "VLSI Engineer": len({"vlsi design", "verilog", "vhdl", "asic", "fpga"}.intersection(s_set)),
                "IoT Specialist": len({"iot", "arduino", "raspberry pi", "sensors"}.intersection(s_set)),
                "Embedded Systems Developer": len({"microprocessors", "embedded systems", "dsp", "c"}.intersection(s_set)),
            }
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0: sub_domain = best_match[0]
            else: sub_domain = "Electronics Engineer"

        # Civil Sub-domains
        elif domain_key == "Civil_Engineering":
            s_set = set([s.lower() for s in matched_terms])
            scores = {
                "Structural Engineer": len({"structural analysis", "staad.pro", "revit", "etabs"}.intersection(s_set)),
                "Project Manager (Civil)": len({"construction management", "project estimation", "ms project"}.intersection(s_set)),
                "BIM Specialist": len({"bim", "revit", "civil 3d"}.intersection(s_set)),
            }
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0: sub_domain = best_match[0]
            else: sub_domain = "Civil Engineer"

        # Legal Sub-domains
        elif domain_key == "Legal":
            s_set = set([s.lower() for s in matched_terms])
            scores = {
                "Corporate Lawyer": len({"corporate law", "contract law", "compliance", "due diligence"}.intersection(s_set)),
                "IP Attorney": len({"intellectual property", "patents", "trademarks"}.intersection(s_set)),
                "Litigation Specialist": len({"litigation", "legal research", "case analysis"}.intersection(s_set)),
            }
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0: sub_domain = best_match[0]
            else: sub_domain = "Legal Professional"
        # Chemical Engineering Sub-domains
        elif domain_key == "Chemical_Engineering":
            s_set = set([s.lower() for s in matched_terms])
            scores = {
                "Process Engineer": len({"process control", "unit operations", "distillation"}.intersection(s_set)),
                "Safety Engineer": len({"safety engineering", "hazop"}.intersection(s_set)),
                "Simulation Specialist": len({"aspen plus", "aspen hysys", "matlab"}.intersection(s_set)),
            }
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0: sub_domain = best_match[0]
            else: sub_domain = "Chemical Engineer"

        # Logistics & Supply Chain Sub-domains
        elif domain_key == "Logistics_Supply_Chain":
            s_set = set([s.lower() for s in matched_terms])
            scores = {
                "Supply Chain Manager": len({"supply chain management", "strategic sourcing", "demand forecasting"}.intersection(s_set)),
                "Logistics Coordinator": len({"logistics", "warehousing", "distribution"}.intersection(s_set)),
                "Procurement Specialist": len({"procurement", "vendor management", "sap scm"}.intersection(s_set)),
            }
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0: sub_domain = best_match[0]
            else: sub_domain = "Logistics Professional"

        # Sales Sub-domains
        elif domain_key == "Sales":
            s_set = set([s.lower() for s in matched_terms])
            scores = {
                "Business Development Manager": len({"business development", "lead generation", "sales strategy"}.intersection(s_set)),
                "Account Executive": len({"account management", "relationship building", "negotiation"}.intersection(s_set)),
                "Sales Specialist": len({"closings", "prospecting", "salesforce"}.intersection(s_set)),
            }
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0: sub_domain = best_match[0]
            else: sub_domain = "Sales Professional"

        # Aerospace Engineering Sub-domains
        elif domain_key == "Aerospace_Engineering":
            s_set = set([s.lower() for s in matched_terms])
            scores = {
                "Aerodynamics Engineer": len({"aerodynamics", "propulsion", "flight mechanics"}.intersection(s_set)),
                "Avionics Specialist": len({"avionics", "orbital mechanics"}.intersection(s_set)),
                "Structural Dynamics Engineer": len({"structural mechanics", "ansys", "catia"}.intersection(s_set)),
            }
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0: sub_domain = best_match[0]
            else: sub_domain = "Aerospace Engineer"

        # Biomedical Engineering Sub-domains
        elif domain_key == "Biomedical_Engineering":
            s_set = set([s.lower() for s in matched_terms])
            scores = {
                "Medical Device Engineer": len({"medical devices", "biosensors", "biomaterials"}.intersection(s_set)),
                "Rehabilitation Engineer": len({"rehabilitation engineering", "biomechanics"}.intersection(s_set)),
                "Imaging Specialist": len({"medical imaging", "mimics", "labview"}.intersection(s_set)),
            }
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0: sub_domain = best_match[0]
            else: sub_domain = "Biomedical Engineer"

        # Industrial Engineering Sub-domains
        elif domain_key == "Industrial_Engineering":
            s_set = set([s.lower() for s in matched_terms])
            scores = {
                "Operations Analyst": len({"operations research", "production planning", "supply chain optimization"}.intersection(s_set)),
                "Quality Engineer": len({"quality control", "six sigma", "minitab"}.intersection(s_set)),
                "Ergonomics Specialist": len({"ergonomics", "facilities design", "arena"}.intersection(s_set)),
            }
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0: sub_domain = best_match[0]
            else: sub_domain = "Industrial Engineer"
                
        # EEE Sub-domains
        elif domain_key == "Electrical_Engineering_EEE":
            s_set = set([s.lower() for s in matched_terms])
            scores = {
                "Power Electronics Engineer": len({"power electronics", "inverters", "converters", "smart grid"}.intersection(s_set)),
                "Automation Engineer": len({"plc", "scada", "industrial automation"}.intersection(s_set))
            }
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0:
                sub_domain = best_match[0]
            else:
                sub_domain = "Electrical Engineer"
                
        # Mechanical Sub-domains
        elif domain_key == "Mechanical_Engineering":
            s_set = set([s.lower() for s in matched_terms])
            scores = {
                "Mechanical Design Engineer": len({"autocad", "solidworks", "catia", "3d modeling"}.intersection(s_set)),
                "CAE Analyst": len({"ansys", "cfd", "fea"}.intersection(s_set)),
                "Manufacturing Engineer": len({"cnc", "gd&t", "lean manufacturing"}.intersection(s_set)),
                "Thermal/HVAC Engineer": len({"thermodynamics", "hvac", "heat transfer"}.intersection(s_set))
            }
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0:
                sub_domain = best_match[0]
            else:
                sub_domain = "Mechanical Engineer"
                
        results.append({
            "domain": DOMAIN_LABELS.get(domain_key, domain_key),
            "key": domain_key,
            "sub_domain": sub_domain,
            "confidence": confidence,
            "matchedCount": match_count,
            "totalKeywords": total,
            "topMatches": list(set(matched_terms))[:8],
        })
    results.sort(key=lambda d: d["confidence"], reverse=True)
    return results[:5]


def generate_suggestions(cats: dict[str, dict[str, Any]], domains: list[dict] | None = None) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    _id = 0

    def add(priority: str, category: str, title: str, detail: str,
            section_target: str | None = None, diff: dict | None = None):
        nonlocal _id
        suggestions.append({"id": f"s{_id}", "priority": priority, "category": category,
                             "title": title, "detail": detail,
                             "sectionTarget": section_target, "diff": diff})
        _id += 1

    kw = cats["keywords"]; fmt = cats["formatting"]; contact = cats["contact"]
    struct = cats["structure"]; ach = cats["achievements"]
    av = cats["actionVerbs"]; ln = cats["length"]

    domain_key = domains[0]["key"] if domains else "General"

    # 1. Keywords / Skills to Improve
    if kw["score"] < 15:
        add("critical", "keywords", "Skills to Improve: Core Skills",
            f"Only {len(kw['matched'])} skills detected. Focus on adding: {', '.join(kw['missing'][:5])}.", "skills")
    elif kw["score"] < 24:
        add("important", "keywords", "Skills to Improve: Competitive Edge",
            f"To better match the industry benchmark, add: {', '.join(kw['missing'][:4])}.", "skills")

    # 2. Formatting
    for issue in fmt.get("issues", [])[:2]:
        add("critical" if fmt["score"] < 10 else "important", "formatting", "Formatting Optimization", issue)

    # 3. Contact Info (Redundancy Check)
    d = contact.get("details", {})
    if not d.get("email"): add("critical", "contact", "Missing Contact: Email", "Include a professional email address for ATS parsers.")
    if not d.get("phone"): add("critical", "contact", "Missing Contact: Phone", "A phone number is essential for recruiter outreach.")
    if not d.get("linkedin") and domain_key in ["Computer_Science_CSE", "Marketing", "Sales", "Design_UX"]: 
        add("nice", "contact", "Social Proof: LinkedIn", "For your domain, a LinkedIn profile significantly improves credibility.")

    # 4. Structure
    for m in struct.get("missing", []):
        add("critical", "structure", f"Missing Section: {m.title()}", f'A dedicated "{m.title()}" section is required for optimal ATS parsing.')

    # 5. Achievements (Contextual)
    if ach["count"] == 0:
        detail = 'Quantify your impact. Metrics (%, $, #) are the most important factor for high ATS scores.'
        if domain_key == "Sales":
            detail += ' E.g., "Exceeded sales targets by 25% ($2M+ revenue)".'
        elif domain_key == "Computer_Science_CSE":
            detail += ' E.g., "Reduced server latency by 40% via query optimization".'
            
        add("critical", "achievements", "Impact Quantification", detail, "experience",
             {"before": "Responsible for managing project timelines.",
              "after": "Spearheaded project delivery 15% ahead of schedule by optimizing resource allocation and using Agile Scrum methodologies."})
    elif ach["count"] < 4:
        add("important", "achievements", "Strengthen Metrics",
            f"Detected {ach['count']} metrics. Aim for at least 5 quantified bullet points across your experience.", "experience")

    # 6. Action Verbs
    if av.get("weak"):
        weak_str = '", "'.join(av["weak"][:2])
        add("important", "actionVerbs", "Dynamic Action Verbs",
            f'Replace passive terms like "{weak_str}" with high-impact verbs like "Orchestrated" or "Engineered".', "experience")

    # 7. Domain-Specific Templates
    if domain_key == "Healthcare":
        add("important", "keywords", "Healthcare Compliance", "Ensure FHIR or HL7 standards are mentioned if relevant to your clinical tech role.")
    elif domain_key == "Finance":
        add("important", "keywords", "FinTech Exposure", "Mention experience with RegTech or FinTech APIs to align with modern finance roles.")
    elif domain_key == "Computer_Science_CSE":
        add("important", "keywords", "System Architecture", "Include experience with design tokens or design systems if applying for frontend-heavy roles.")
        add("nice", "keywords", "Open Source", "Include a link to your GitHub profile or mention open-source contributions to demonstrate coding active-ness.")
    elif domain_key == "Data_Science":
        add("important", "keywords", "ML Deployment", "Mention experience with model deployment and monitoring (MLOps) using tools like MLflow or Kubeflow.")
        add("important", "keywords", "Big Data", "Highlight experience with big data technologies like Spark or Hadoop if targeting enterprise data roles.")

    # 8. Length
    wc = ln.get("wordCount", 0)
    if wc < 250: add("critical", "length", "Content Depth", "Your resume is too brief. Expand on your responsibilities and technical projects.")
    elif wc > 1200: add("important", "length", "Conciseness", "Resume exceeds 1,200 words. Aim for a max of 2 pages (approx. 900-1000 words).")

    suggestions.sort(key=lambda s: {"critical": 0, "important": 1, "nice": 2}.get(s["priority"], 2))
    return suggestions[:10]


_SCORE_CACHE: OrderedDict[str, dict] = OrderedDict()
_CACHE_MAX = 64


def score_resume(
    text: str,
    job_description: str = "",
    spacy_skills: list[str] | None = None,
    embedding: Any = None,
    sentence_model: Any = None,
) -> dict[str, Any]:
    if not text or len(text.strip()) < 10:
        return {"total": 0, "categories": {}, "suggestions": [], "domains": [],
                "keywords": {"matched": [], "missing": []}}

    text_hash = hashlib.md5((text + job_description).encode()).hexdigest()
    if text_hash in _SCORE_CACHE:
        return _SCORE_CACHE[text_hash]

    skills = spacy_skills or []
    
    # Calculate domains FIRST so we can use them to find missing keywords
    domains = detect_domains_nlp(text, skills, embedding, sentence_model)
    
    keywords = score_keywords(text, skills, job_description, domains)
    formatting = score_formatting(text)
    contact = score_contact(text)
    structure = score_structure(text)
    achievements = score_achievements(text)
    action_verbs = score_action_verbs(text)
    length = score_length(text)

    categories = {
        "keywords": keywords, "formatting": formatting, "contact": contact,
        "structure": structure, "achievements": achievements,
        "actionVerbs": action_verbs, "length": length,
    }
    total = min(100, sum(c["score"] for c in categories.values()))
    suggestions = generate_suggestions(categories, domains)

    result = {
        "total": total, "categories": categories,
        "suggestions": suggestions, "domains": domains,
        "keywords": {"matched": keywords["matched"], "missing": keywords["missing"]},
    }
    _SCORE_CACHE[text_hash] = result
    if len(_SCORE_CACHE) > _CACHE_MAX:
        _SCORE_CACHE.popitem(last=False)
    return result
