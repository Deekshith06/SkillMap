"""insights.py — Charts: UMAP scatter, cluster donut, skill bar, heatmap."""
import reflex as rx
from skillmap.state.insights_state import InsightsState
from skillmap.components.charts import (
    cluster_pie_chart, skill_bar_chart, scatter_chart_umap,
)
from skillmap.styles import theme as t


def heatmap_cell(point: dict, max_val: int = 1) -> rx.Component:
    val = point.get("value", 0)
    intensity = val / max(max_val, 1)
    return rx.box(
        rx.cond(val > 0, rx.text(str(val), font_size="0.75rem", font_weight="700"), rx.box()),
        width="48px", height="48px",
        border_radius=t.RADIUS_SM,
        display="flex", align_items="center", justify_content="center",
        background_color=f"rgba(255, 119, 28, {intensity * 0.8 + 0.05})",
        title=f"{point.get('yLabel', '')} × {point.get('xLabel', '')}: {val}",
        transition=f"transform {t.TRANSITION_FAST}",
        _hover={"transform": "scale(1.1)"},
        flex_shrink="0",
        margin_right="2px",
    )


def insights_page() -> rx.Component:
    return rx.box(
        # Header
        rx.vstack(
            rx.heading("Insights", size="8", font_family=t.FONT_HEADING,
                       color=t.DARK),
            rx.text("Cluster distribution, skill analytics, and co-occurrence patterns.",
                    color=t.SECONDARY),
            spacing="1", align_items="start", margin_bottom=t.SPACE_8,
        ),



        # Cluster Distribution Donut
        rx.box(
            rx.vstack(
                rx.heading("Cluster Distribution", size="5", font_family=t.FONT_HEADING,
                           color=t.DARK),
                rx.text("Proportional breakdown of resume clusters.", color=t.SECONDARY),
                spacing="1", align_items="start", margin_bottom=t.SPACE_4,
            ),
            rx.cond(
                InsightsState.cluster_dist.length() > 0,
                cluster_pie_chart(InsightsState.cluster_dist),
                rx.vstack(
                    rx.text("📊", font_size="2rem"),
                    rx.text("No cluster data available.", color=t.SECONDARY),
                    align="center", padding=t.SPACE_12,
                ),
            ),
            background_color=t.SURFACE,
            border=f"1px solid {t.SURFACE_BORDER}",
            border_radius=t.RADIUS_LG,
            padding=t.SPACE_6,
            box_shadow=t.SHADOW_SM,
            margin_bottom=t.SPACE_6,
        ),

        # Skill Distribution Bar
        rx.box(
            rx.vstack(
                rx.heading("Skill Distribution", size="5", font_family=t.FONT_HEADING,
                           color=t.DARK),
                rx.text("Top-15 skills across all analysed resumes.", color=t.SECONDARY),
                spacing="1", align_items="start", margin_bottom=t.SPACE_4,
            ),
            rx.cond(
                InsightsState.skill_dist.length() > 0,
                skill_bar_chart(InsightsState.skill_dist, height=400),
                rx.vstack(
                    rx.text("📉", font_size="2rem"),
                    rx.text("No skill data available.", color=t.SECONDARY),
                    align="center", padding=t.SPACE_12,
                ),
            ),
            background_color=t.SURFACE,
            border=f"1px solid {t.SURFACE_BORDER}",
            border_radius=t.RADIUS_LG,
            padding=t.SPACE_6,
            box_shadow=t.SHADOW_SM,
            margin_bottom=t.SPACE_6,
        ),

        # Skill Co-occurrence Heatmap
        rx.box(
            rx.vstack(
                rx.heading("Skill Co-occurrence", size="5", font_family=t.FONT_HEADING,
                           color=t.DARK),
                rx.text("How often skills appear together across clusters.", color=t.SECONDARY),
                spacing="1", align_items="start", margin_bottom=t.SPACE_4,
            ),
            rx.cond(
                InsightsState.heatmap_labels.length() > 0,
                rx.box(
                    # Header row
                    rx.hstack(
                        rx.box(width="120px", flex_shrink="0"),
                        rx.foreach(
                            InsightsState.heatmap_labels,
                            lambda label: rx.box(
                                label[:8],
                                width="48px",
                                font_size="0.7rem",
                                font_weight="600",
                                color=t.SECONDARY,
                                text_align="center",
                                flex_shrink="0",
                                overflow="hidden",
                                title=label,
                            ),
                        ),
                        spacing="0",
                        margin_bottom=t.SPACE_2,
                    ),
                    overflow_x="auto",
                ),
                rx.vstack(
                    rx.text("🔥", font_size="2rem"),
                    rx.text("No co-occurrence data available.", color=t.SECONDARY),
                    align="center", padding=t.SPACE_12,
                ),
            ),
            background_color=t.SURFACE,
            border=f"1px solid {t.SURFACE_BORDER}",
            border_radius=t.RADIUS_LG,
            padding=t.SPACE_6,
            box_shadow=t.SHADOW_SM,
        ),

        on_mount=InsightsState.load_data,
        max_width="1200px",
        margin="0 auto",
        padding=f"{t.SPACE_8} {t.SPACE_6}",
    )
