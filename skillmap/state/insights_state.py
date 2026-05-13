"""insights_state.py — Charts, cluster stats, UMAP-like scatter data."""
from __future__ import annotations
import reflex as rx
from skillmap.state.app_state import AppState


class InsightsState(AppState):
    """Derives chart data from loaded stats."""

    @rx.var
    def cluster_dist(self) -> list[dict]:
        raw = self.stats.get("cluster_distribution", [])
        
        # Merge duplicates by exact name
        merged: dict[str, dict] = {}
        for c in raw:
            name = c.get("name", "Unknown").strip()
            if name.startswith("Cluster ") or name == "Unknown" or name == "Noise":
                name = "General Professionals"

            if name not in merged:
                merged[name] = c.copy()
                merged[name]["name"] = name
            else:
                merged[name]["resume_count"] += c.get("resume_count", 0)
                # Keep unique top skills
                existing_skills = set(merged[name].get("top_skills", []))
                for s in c.get("top_skills", []):
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
        return int(self.model_metrics.get("n_clusters", len(self.cluster_dist)))

    @rx.var
    def taxonomy_cluster_count(self) -> str:
        return "29"

    @rx.var
    def total_skills_count(self) -> int:
        data = self.stats.get("skill_distribution") or self.stats.get("top_skills") or []
        return len(data)

    @rx.var
    def model_metrics(self) -> dict:
        return self.stats.get("metrics", {})

    @rx.var
    def silhouette_score(self) -> str:
        score = self.model_metrics.get("silhouette_score", 0.0)
        return f"{score:.4f}" if score else "N/A"

    @rx.var
    def noise_count(self) -> str:
        noise = self.model_metrics.get("noise_count", 0)
        return str(noise)

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
