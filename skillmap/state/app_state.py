"""app_state.py — Global AppState: dark mode, navigation, stats, clusters."""

from __future__ import annotations

import reflex as rx
from reflex_base.components.props import PropsBase

from skillmap.core.exceptions import UserFacingError


class ClusterItem(PropsBase):
    id: int = 0
    name: str = ""
    size: int = 0
    top_skills: list[str] = []
    avg_confidence: float = 0.0


class AppState(rx.State):
    clusters: list[ClusterItem] = []
    stats: dict = {}
    loading: bool = False
    error: str = ""
    score_history: list[dict] = []

    def add_to_history(self, entry: dict):
        self.score_history = [entry, *self.score_history[:19]]

    def load_data(self) -> None:
        self.loading = True
        self.error = ""
        try:
            from skillmap.services.analysis_service import get_clusters, get_stats

            raw_clusters = get_clusters()
            stats = get_stats()
            clusters = [
                ClusterItem(
                    id=c.get("id", 0),
                    name=c.get("name", ""),
                    size=c.get("size", 0),
                    top_skills=c.get("top_skills", []),
                    avg_confidence=c.get("avg_confidence", 0.0),
                )
                for c in raw_clusters
            ]
            self.clusters = clusters
            self.stats = stats
        except Exception as exc:
            self.error = (
                exc.public_message
                if isinstance(exc, UserFacingError)
                else UserFacingError(
                    "Dashboard data is temporarily unavailable.",
                    category="dashboard_load_failure",
                ).public_message
            )
        finally:
            self.loading = False
