"""graph_engine.py - Advanced graph relationships, adjacency, and career trajectory."""
import json
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data"
_POWER_SKILLS_PATH = _DATA_DIR / "powerSkills.json"

try:
    with _POWER_SKILLS_PATH.open() as f:
        POWER_SKILLS = json.load(f)
except Exception:
    POWER_SKILLS = {}

def build_adjacency_map():
    adjacency = {}
    for domain, subcats in POWER_SKILLS.items():
        if isinstance(subcats, dict):
            for subcat, skills in subcats.items():
                skills_lower = [s.lower() for s in skills]
                for skill in skills_lower:
                    if skill not in adjacency:
                        adjacency[skill] = set()
                    for other in skills_lower:
                        if skill != other:
                            adjacency[skill].add(other)
    return adjacency

_ADJACENCY = build_adjacency_map()

def get_adjacent_skills(user_skills: list[str], top_n=5) -> list[str]:
    """Find missing skills that are adjacent to the user's current skillset."""
    recommendations = {}
    user_skills_set = set(s.lower() for s in user_skills)
    
    for skill in user_skills_set:
        neighbors = _ADJACENCY.get(skill, set())
        for neighbor in neighbors:
            if neighbor not in user_skills_set:
                recommendations[neighbor] = recommendations.get(neighbor, 0) + 1
                
    # Sort by frequency of connection
    sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
    return [r[0].title() for r in sorted_recs[:top_n]]

def extract_seniority(text: str) -> str:
    """Extract seniority level from resume text."""
    lower_text = text.lower()
    
    if "director" in lower_text or "vp" in lower_text or "head of" in lower_text:
        return "Director / Head"
    if "principal" in lower_text or "architect" in lower_text:
        return "Principal / Architect"
    if "lead" in lower_text or "manager" in lower_text:
        return "Lead / Manager"
    if "senior" in lower_text or "sr." in lower_text or "sr " in lower_text:
        return "Senior"
    if "junior" in lower_text or "jr " in lower_text or "intern" in lower_text:
        return "Junior / Entry-level"
        
    return "Mid-level"

def extract_soft_skills(text: str) -> list[str]:
    """Extract soft skills and behavioral traits."""
    soft_skills = [
        "leadership", "communication", "agile", "scrum", "teamwork",
        "project management", "cross-functional", "mentoring", "problem solving",
        "strategic planning", "stakeholder management", "negotiation", "collaboration",
        "analytical", "empathy", "adaptability", "critical thinking"
    ]
    lower = text.lower()
    found = []
    for skill in soft_skills:
        if skill in lower:
            found.append(skill.title())
    return found[:5]

def get_career_trajectory(cluster_name: str, seniority: str) -> list[str]:
    """Predict logical next career steps based on cluster and seniority."""
    base = cluster_name.replace(" Professional", "").replace(" Specialists", "").strip()
    if not base or base == "Unknown" or base.startswith("Cluster"):
        return []
        
    if seniority in ["Junior / Entry-level"]:
        return [f"Mid-level {base}", f"{base} Specialist", f"Senior {base}"]
    elif seniority in ["Mid-level"]:
        return [f"Senior {base}", f"Lead {base}", f"{base} Architect"]
    elif seniority in ["Senior"]:
        return [f"Lead {base}", f"{base} Architect", f"{base} Manager"]
    elif seniority in ["Lead / Manager"]:
        return [f"Director of {base}", f"Principal {base}", "VP of Engineering/Operations"]
    else:
        return ["Executive Leadership", "VP / Head of Department", "C-Suite"]
