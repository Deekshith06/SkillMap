"""insights_state.py — Charts, cluster stats, UMAP-like scatter data."""
from __future__ import annotations
import reflex as rx
from skillmap.state.app_state import AppState


class InsightsState(AppState):
    """Derives chart data from loaded stats."""

    @rx.var
    def cluster_dist(self) -> list[dict]:
        raw = self.stats.get("cluster_distribution", [])
        
        DOMAIN_MAPPING = {
            "React": "Computer Science & IT",
            "Javascript": "Computer Science & IT",
            "Python": "Computer Science & IT",
            "Node": "Computer Science & IT",
            "Mern": "Computer Science & IT",
            "Java": "Computer Science & IT",
            "Html": "Computer Science & IT",
            "Autocad": "Mechanical Engineering",
            "Solidworks": "Mechanical Engineering",
            "Thermodynamics": "Mechanical Engineering",
            "Catia": "Mechanical Engineering",
            "Mechanical": "Mechanical Engineering",
            "Ece": "Electrical & Electronics",
            "Eee": "Electrical & Electronics",
            "Circuit": "Electrical & Electronics",
            "Embedded": "Electrical & Electronics",
            "Pandas": "Data Science & AI",
            "Numpy": "Data Science & AI",
            "Pytorch": "Data Science & AI",
            "Tensorflow": "Data Science & AI",
            "Problem Solving": "General Professionals",
            "Communication": "General Professionals",
            "Curriculum": "Education & Management"
        }

        # Merge duplicates by name (strip to ensure matches)
        merged: dict[str, dict] = {}
        for c in raw:
            name = c.get("name", "Unknown").strip()
            top_skills = c.get("top_skills", [])
            
            # 1. Try to find a domain mapping for the current name or top skill
            best_domain = None
            
            # Check current name
            for skill_key, domain in DOMAIN_MAPPING.items():
                if skill_key.lower() in name.lower():
                    best_domain = domain
                    break
            
            # If not found, check top skills
            if not best_domain and top_skills:
                for skill in top_skills:
                    skill_title = skill.title()
                    if skill_title in DOMAIN_MAPPING:
                        best_domain = DOMAIN_MAPPING[skill_title]
                        break
            
            # 2. Update name to domain if found
            if best_domain:
                name = best_domain
            elif name.startswith("Cluster ") or name == "Unknown":
                name = "General Professionals"

            if name not in merged:
                merged[name] = c.copy()
                merged[name]["name"] = name
            else:
                merged[name]["resume_count"] += c.get("resume_count", 0)
                # Keep the best skills if merging
                existing_skills = set(merged[name].get("top_skills", []))
                for s in top_skills:
                    if s not in existing_skills:
                        merged[name].setdefault("top_skills", []).append(s)
        
        results = [c for c in merged.values() if c.get("resume_count", 0) > 0]
        total = sum(c["resume_count"] for c in results)
        for c in results:
            pct = (c["resume_count"] / total * 100) if total > 0 else 0
            c["percent"] = f"{round(pct, 1)}%"
        
        return sorted(results, key=lambda x: x["resume_count"], reverse=True)

    @rx.var
    def total_resumes_count(self) -> int:
        return sum(c["resume_count"] for c in self.cluster_dist)

    @rx.var
    def total_clusters_count(self) -> int:
        return len(self.cluster_dist)

    @rx.var
    def total_skills_count(self) -> int:
        data = self.stats.get("skill_distribution") or self.stats.get("top_skills") or []
        return len(data)

    @rx.var
    def skill_dist(self) -> list[dict]:
        data = self.stats.get("skill_distribution") or self.stats.get("top_skills") or []
        if not data:
            return []
        
        BAD_SKILLS = {
            "work experience", "projects", "education", "summary", "objective",
            "certifications", "technical certification", "functional teams",
            "mentored junior", "senior engineer", "staff and managed", 
            "managed cross", "professional non", "global tech corp", "skills",
            "technical", "professional", "history", "languages", "interests"
        }
        
        # Clean and filter
        cleaned_data = []
        for d in data:
            skill = d.get("skill", "").lower().strip().rstrip(":")
            if not skill or any(bad in skill for bad in BAD_SKILLS) or len(skill) < 3:
                continue
            cleaned_data.append({"skill": skill.title() if len(skill) > 3 else skill.upper(), "count": d.get("count", 0)})
        
        if not cleaned_data:
            return []
            
        # Ensure percentages are relative to the highest count for visual scaling
        max_count = max(d["count"] for d in cleaned_data)
        processed = []
        for i, d in enumerate(cleaned_data[:10]):
            count = d["count"]
            pct = (count / max_count * 100) if max_count > 0 else 0
            processed.append({
                "index": i + 1,
                "skill": d["skill"],
                "count": count,
                "percent": f"{round(pct)}%"
            })
        return processed

    @rx.var
    def heatmap_labels(self) -> list[str]:
        all_skills: set[str] = set()
        for c in self.cluster_dist:
            for s in (c.get("top_skills") or []):
                all_skills.add(s)
        return sorted(all_skills)[:10]

    @rx.var
    def heatmap_points(self) -> list[dict]:
        labels = self.heatmap_labels
        dist   = self.cluster_dist
        points = []
        for i, row_label in enumerate(labels):
            for j, col_label in enumerate(labels):
                co = sum(
                    1 for c in dist
                    if row_label in (c.get("top_skills") or [])
                    and col_label in (c.get("top_skills") or [])
                )
                points.append({"x": j, "y": i, "xLabel": col_label, "yLabel": row_label, "value": co})
        return points

    @rx.var
    def scatter_points(self) -> list[dict]:
        """Synthetic UMAP-like 2D scatter from cluster data."""
        import math
        points = []
        for c in self.cluster_dist:
            cid   = c.get("id", 0)
            count = c.get("resume_count", 0)
            angle = (cid * 2.4) % (2 * math.pi)
            r     = 0.3 + (cid % 5) * 0.12
            points.append({
                "x": round(r * math.cos(angle), 3),
                "y": round(r * math.sin(angle), 3),
                "name": c.get("name", ""),
                "count": count,
                "cluster_id": cid,
            })
        return points
