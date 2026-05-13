"""
pages/dashboard.py — Redesigned Project Details Page.

Layout (desktop):
  ┌────────────────────────────────────────────────────┐
  │  NAVBAR (gradient header)                          │
  ├──────────────┬─────────────────────────────────────┤
  │  SIDEBAR     │  MAIN CONTENT                       │
  │  280px fixed │  breadcrumb + overview              │
  │              │  4 stats cards                      │
  │              │  pipeline + cluster chart 2-col     │
  │              │  activity timeline                  │
  └──────────────┴─────────────────────────────────────┘
  │  FOOTER                                            │
  └────────────────────────────────────────────────────┘
"""
from __future__ import annotations
import reflex as rx
from skillmap.state.app_state import AppState
from skillmap.state.insights_state import InsightsState
from skillmap.components.navbar import navbar
from skillmap.components.cluster_card import cluster_card
from skillmap.components.charts import skill_bar_chart, cluster_pie_chart
from skillmap.components.ui import (
    status_badge, tag_chip, stats_card, section_header,
    meta_row, divider, skeleton_card, footer,
)
from skillmap.styles import theme as t


# ─────────────────────────────────────────────────────────────────────────────
# (Sidebar removed)
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Project overview hero
# ─────────────────────────────────────────────────────────────────────────────

def project_overview() -> rx.Component:
    return rx.vstack(
        rx.box(
            "AI TALENT INTELLIGENCE",
            font_size="0.75rem",
            font_weight="700",
            color=t.PRIMARY,
            background_color=t.PRIMARY_LIGHT,
            padding="0.25rem 0.75rem",
            border_radius=t.RADIUS_PILL,
            margin_bottom=t.SPACE_4,
        ),
        rx.heading(
            "Talent Intelligence Hub",
            size="9",
            font_family=t.FONT_HEADING,
            font_weight="800",
            color=t.DARK,
            letter_spacing="-0.02em",
            line_height="1.15",
            text_align="center",
            margin_bottom=t.SPACE_6,
        ),
        rx.text(
            "Map talent using multi-dimensional embeddings, HDBSCAN clustering, and Graph Adjacency algorithms across 12+ enterprise domains.",
            font_size="1.1rem",
            color=t.SECONDARY,
            font_family=t.FONT_BODY,
            max_width="680px",
            line_height="1.6",
            text_align="center",
            margin_bottom=t.SPACE_4,
        ),
        rx.box(
            rx.hstack(
                rx.icon("zap", color=t.WARNING, size=18),
                rx.text(
                    "v2.0 Expansion Live: 8 new clustering domains, Seniority/Soft-Skill Extraction, and Career Trajectory Mapping.",
                    font_size="0.85rem", color=t.DARK, font_weight="600"
                ),
                align_items="center", spacing="2"
            ),
            padding="10px 20px", background_color="#FEF3C7", border="1px solid #F59E0B", border_radius="8px", margin_bottom=t.SPACE_8
        ),
        rx.hstack(
            rx.button(
                "Quick Analyze \u2192",
                on_click=rx.redirect("/analyze"),
                **t.btn_primary(padding="0.8rem 1.8rem", font_size="1rem")
            ),
            rx.button(
                "Batch Process",
                on_click=rx.redirect("/bulk"),
                **t.btn_secondary(padding="0.8rem 1.8rem", font_size="1rem")
            ),
            spacing="4",
        ),
        spacing="1",
        align_items="center",
        justify_content="center",
        width="100%",
        padding_top=t.SPACE_8,
        padding_bottom=t.SPACE_12,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Stats row
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Stats row (Updated to 3 cards)
# ─────────────────────────────────────────────────────────────────────────────

def stats_row() -> rx.Component:
    return rx.cond(
        AppState.loading,
        rx.hstack(
            *[skeleton_card("100px") for _ in range(3)],
            spacing="4", width="100%",
        ),
        rx.grid(
            stats_card("users", AppState.stats.get("total_resumes", "0"), "Total Resumes"),
            stats_card("award", InsightsState.total_skills_count.to(str), "Skill Categories", t.BRAND),
            stats_card("activity", InsightsState.total_clusters_count.to(str), "Clusters Identified", t.PRIMARY),
            spacing="4",
            width="100%",
            columns="3",
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Mixed Insights & Dashboard Layout
# ─────────────────────────────────────────────────────────────────────────────

def cluster_list_item(cluster: dict, index: int) -> rx.Component:
    # Use consistent orange shades from theme
    color = rx.Var.create(t.ORANGE_PALETTE)[index % 10]
    
    return rx.hstack(
        rx.box(width="12px", height="12px", border_radius="2px", background_color=color, flex_shrink="0"),
        rx.text(cluster["name"], font_size="0.85rem", font_weight="500", color=t.DARK, flex="1"),
        rx.text(cluster["resume_count"].to(str), font_size="0.85rem", font_weight="700", color=t.DARK),
        rx.text(cluster["percent"], font_size="0.85rem", font_weight="700", color=t.PRIMARY, width="45px", text_align="right"),
        width="100%", align_items="center", spacing="3", margin_bottom="8px"
    )

def skill_dist_item(item: dict) -> rx.Component:
    # item is passed with "index", "skill", "count", "percent"
    return rx.vstack(
        rx.hstack(
            rx.box(
                rx.text(item["index"], color="white", font_size="0.75rem", font_weight="700"),
                width="24px", height="24px", border_radius="50%", background_color=t.PRIMARY,
                display="flex", align_items="center", justify_content="center", flex_shrink="0"
            ),
            rx.text(item["skill"], font_size="0.9rem", font_weight="700", color=t.DARK),
            rx.spacer(),
            rx.text(item["count"].to(str) + " occurrences", font_size="0.8rem", color=t.SECONDARY),
            rx.text(item["percent"], font_size="0.85rem", font_weight="700", color=t.PRIMARY, width="40px", text_align="right"),
            width="100%", align_items="center", spacing="3"
        ),
        rx.box(
            rx.box(width=item["percent"], height="8px", background_color=t.PRIMARY, border_radius="4px"),
            width="100%", height="8px", background_color=t.PRIMARY_LIGHT, border_radius="4px", overflow="hidden"
        ),
        width="100%", spacing="2", margin_bottom="16px"
    )

# ── Architecture Visualization Components ─────────────────────────────────────

def arch_label(text: str) -> rx.Component:
    return rx.text(
        text,
        font_size="10px",
        font_weight="500",
        font_family=t.FONT_MONO,
        color=t.ARCH_ORANGE_600,
        letter_spacing="0.12em",
        margin_bottom="14px",
        text_align="center",
        width="100%",
        text_transform="uppercase",
    )

def arch_box(path: str, name: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(path, font_size="13px", font_weight="500", color=t.ARCH_NEUTRAL_900, font_family=t.FONT_MONO),
            rx.text(name, font_size="11px", color=t.ARCH_NEUTRAL_500, font_weight="400"),
            spacing="1",
            align_items="start",
        ),
        padding="14px",
        border=f"1px solid {t.ARCH_NEUTRAL_300}",
        border_radius="8px",
        background_color="white",
        width="100%",
        _hover={
            "border_color": t.ARCH_NEUTRAL_200,
            "box_shadow": "0 2px 8px rgba(0,0,0,0.06)",
        },
        transition=t.TRANSITION_BASE,
    )

def arch_endpoint(method: str, path: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(method, font_size="10px", font_weight="500", color=t.ARCH_ORANGE_600, font_family=t.FONT_MONO, text_transform="uppercase"),
            rx.text(path, font_size="12px", font_weight="400", color=t.ARCH_NEUTRAL_900, font_family=t.FONT_MONO),
            spacing="1",
            align_items="start",
        ),
        padding="10px 14px",
        border=f"1px solid {t.ARCH_NEUTRAL_300}",
        border_radius="7px",
        background_color=t.ARCH_NEUTRAL_50,
        flex="1",
        _hover={"border_color": t.ARCH_ORANGE_100},
        transition=t.TRANSITION_BASE,
    )

def arch_list_item(text: str) -> rx.Component:
    return rx.hstack(
        rx.box(width="3px", height="3px", border_radius="50%", background_color=t.ARCH_ORANGE_600, opacity="0.6", margin_top="7px"),
        rx.text(text, font_size="11.5px", color=t.ARCH_NEUTRAL_500, font_weight="400", font_family=t.FONT_MONO),
        spacing="3",
        align_items="start",
    )

def arch_connector() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.box(width="1.5px", height="20px", background_color=t.ARCH_NEUTRAL_300),
            rx.icon("chevron-down", size=14, color=t.ARCH_NEUTRAL_300, margin_top="-6px"),
            spacing="0", align_items="center"
        ),
        width="100%",
        padding="8px 0",
    )

def technical_architecture() -> rx.Component:
    return rx.box(
        rx.vstack(
            # 1. Header Row
            rx.hstack(
                rx.vstack(
                    rx.heading("Technical Architecture", font_size="20px", font_weight="700", font_family=t.FONT_HEADING, color=t.ARCH_NEUTRAL_900),
                    rx.text("End-to-end intelligence pipeline and infrastructure", color=t.ARCH_NEUTRAL_500, font_size="12px", font_family=t.FONT_MONO),
                    spacing="1", align_items="start",
                ),
                rx.spacer(),
                rx.box(
                    rx.text("Phase 4 Production", font_size="11px", font_weight="500", font_family=t.FONT_MONO, color=t.ARCH_ORANGE_600),
                    background_color=t.ARCH_ORANGE_50,
                    border=f"1px solid {t.ARCH_ORANGE_100}",
                    padding="4px 10px",
                    border_radius="4px",
                ),
                width="100%", align_items="center", margin_bottom="32px",
            ),
            
            # 2. REFLEX FRONTEND Section
            rx.box(
                rx.vstack(
                    arch_label("REFLEX FRONTEND"),
                    rx.grid(
                        arch_box("/", "· Dashboard"),
                        arch_box("/analyze", "· Analyze"),
                        arch_box("/bulk", "· Bulk Upload"),
                        arch_box("/ats", "· ATS Editor"),
                        columns="4", spacing="3", width="100%"
                    ),
                    # State box
                    rx.box(
                        rx.vstack(
                            rx.text("Reflex State (rx.State subclasses)", font_size="13px", font_weight="600", font_family=t.FONT_HEADING, color=t.ARCH_NEUTRAL_900),
                            rx.hstack(
                                rx.text("AppState", font_size="11px", color=t.ARCH_NEUTRAL_500, font_family=t.FONT_MONO),
                                rx.text("—", color=t.ARCH_NEUTRAL_300),
                                rx.text("AnalyzeState", font_size="11px", color=t.ARCH_NEUTRAL_500, font_family=t.FONT_MONO),
                                rx.text("—", color=t.ARCH_NEUTRAL_300),
                                rx.text("BulkState", font_size="11px", color=t.ARCH_NEUTRAL_500, font_family=t.FONT_MONO),
                                rx.text("—", color=t.ARCH_NEUTRAL_300),
                                rx.text("ATSState", font_size="11px", color=t.ARCH_NEUTRAL_500, font_family=t.FONT_MONO),
                                spacing="2",
                            ),
                            spacing="1", align_items="start",
                        ),
                        width="100%", padding="12px 16px", border=f"1px solid {t.ARCH_NEUTRAL_300}", border_radius="8px", margin_top="12px", background_color="white"
                    ),
                    width="100%",
                ),
                width="100%", padding="20px", border_radius="12px", background_color=t.ARCH_ORANGE_50, border=f"1px solid {t.ARCH_ORANGE_100}",
            ),
            
            arch_connector(),

            # 4. FASTAPI SERVICE LAYER Section
            rx.box(
                rx.vstack(
                    arch_label("FASTAPI SERVICE LAYER"),
                    rx.grid(
                        arch_endpoint("POST", "/resume/upload"),
                        arch_endpoint("GET", "/resume/{id}/score"),
                        arch_endpoint("POST", "/cluster"),
                        columns="3", spacing="3", width="100%"
                    ),
                    width="100%",
                ),
                width="100%", padding="20px", border_radius="10px", background_color="white", border=f"1px solid {t.ARCH_NEUTRAL_300}",
            ),

            arch_connector(),

            # 5. ENGINE BOXES
            rx.grid(
                # Ingestion
                rx.box(
                    rx.text("INGESTION LAYER", font_size="11px", font_weight="700", font_family=t.FONT_HEADING, color=t.ARCH_NEUTRAL_900, border_bottom=f"1px solid {t.ARCH_NEUTRAL_300}", padding_bottom="8px", margin_bottom="12px"),
                    rx.vstack(
                        arch_list_item("PDF/DOCX/TXT Parser"),
                        arch_list_item("Section Detector"),
                        arch_list_item("Text Normalizer"),
                        spacing="3", align_items="start"
                    ),
                    padding="16px", background_color="white", border=f"1px solid {t.ARCH_NEUTRAL_300}", border_radius="10px",
                    _hover={"border_color": t.ARCH_NEUTRAL_200}, transition=t.TRANSITION_BASE,
                ),
                # ATS Engine
                rx.box(
                    rx.text("ATS ENGINE", font_size="11px", font_weight="700", font_family=t.FONT_HEADING, color=t.ARCH_NEUTRAL_900, border_bottom=f"1px solid {t.ARCH_NEUTRAL_300}", padding_bottom="8px", margin_bottom="12px"),
                    rx.vstack(
                        arch_list_item("KeywordScorer (TF-IDF)"),
                        arch_list_item("Format Checker"),
                        arch_list_item("Section Scorer"),
                        spacing="3", align_items="start"
                    ),
                    padding="16px", background_color="white", border=f"1px solid {t.ARCH_NEUTRAL_300}", border_radius="10px",
                    _hover={"border_color": t.ARCH_NEUTRAL_200}, transition=t.TRANSITION_BASE,
                ),
                # Intelligence Engine
                rx.box(
                    rx.text("INTELLIGENCE ENGINE", font_size="11px", font_weight="700", font_family=t.FONT_HEADING, color=t.ARCH_NEUTRAL_900, border_bottom=f"1px solid {t.ARCH_NEUTRAL_300}", padding_bottom="8px", margin_bottom="12px"),
                    rx.vstack(
                        arch_list_item("Multi-Dimensional Embedder"),
                        arch_list_item("UMAP-HDBSCAN Clustering"),
                        arch_list_item("Graph Adjacency Engine"),
                        spacing="3", align_items="start"
                    ),
                    padding="16px", background_color="#FFFBEB", border=f"1px solid #FCD34D", border_radius="10px",
                    _hover={"border_color": "#F59E0B"}, transition=t.TRANSITION_BASE,
                ),
                columns="3", spacing="3", width="100%", margin_bottom="8px"
            ),

            arch_connector(),

            # 6. ML INFRASTRUCTURE Section
            rx.box(
                rx.vstack(
                    arch_label("ML INFRASTRUCTURE"),
                    rx.hstack(
                        rx.box(rx.text("DVC Data Versioning", font_size="12px", font_family=t.FONT_MONO, color=t.ARCH_NEUTRAL_500), padding="8px 16px", background_color="white", border=f"1px solid {t.ARCH_NEUTRAL_300}", border_radius="6px", _hover={"border_color": t.ARCH_ORANGE_100, "color": t.ARCH_ORANGE_600}),
                        rx.box(rx.text("MLFlow Tracking", font_size="12px", font_family=t.FONT_MONO, color=t.ARCH_NEUTRAL_500), padding="8px 16px", background_color="white", border=f"1px solid {t.ARCH_NEUTRAL_300}", border_radius="6px", _hover={"border_color": t.ARCH_ORANGE_100, "color": t.ARCH_ORANGE_600}),
                        rx.box(rx.text("Feature Store", font_size="12px", font_family=t.FONT_MONO, color=t.ARCH_NEUTRAL_500), padding="8px 16px", background_color="white", border=f"1px solid {t.ARCH_NEUTRAL_300}", border_radius="6px", _hover={"border_color": t.ARCH_ORANGE_100, "color": t.ARCH_ORANGE_600}),
                        spacing="3", width="100%", justify_content="center", flex_wrap="wrap"
                    ),
                    width="100%",
                ),
                width="100%", padding="20px", border_radius="12px", background_color=t.ARCH_ORANGE_50, border=f"1px solid {t.ARCH_ORANGE_100}",
            ),

            spacing="0", width="100%",
        ),
        background_color="white",
        border_radius="16px",
        padding="40px",
        width="100%",
        box_shadow=t.SHADOW_MD,
    )

def dashboard_mixed_content() -> rx.Component:
    return rx.vstack(
        # Top Row: Distribution Cards
        rx.grid(
            # 1. Cluster Distribution
            rx.box(
                rx.vstack(
                    rx.heading("Cluster Distribution", size="5", font_family=t.FONT_HEADING, color=t.DARK),
                    rx.text("Proportional breakdown of clusters", color=t.SECONDARY, font_size="0.8rem"),
                    spacing="1", align_items="start", margin_bottom=t.SPACE_4,
                ),
                rx.cond(
                    InsightsState.cluster_dist.length() > 0,
                    rx.vstack(
                        rx.box(cluster_pie_chart(InsightsState.cluster_dist, InsightsState.total_resumes_count, height=280), display="flex", justify_content="center", width="100%"),
                        rx.box(
                            rx.vstack(
                                rx.foreach(InsightsState.cluster_dist, lambda c, i: cluster_list_item(c, i)),
                                width="100%", 
                                max_height="500px",
                                overflow_y="auto",
                                padding_right="10px",
                                custom_attrs={"style": {"scrollbar-width": "thin", "scrollbar-color": f"{t.PRIMARY} transparent"}}
                            ),
                            width="100%",
                        ),
                        spacing="4", width="100%"
                    ),
                    rx.vstack(rx.text("No cluster data available.", color=t.SECONDARY), align="center", padding=t.SPACE_12),
                ),
                **t.card_style(), height="100%", display="flex", flex_direction="column"
            ),
            
            # 2. Skill Distribution
            rx.box(
                rx.vstack(
                    rx.heading("Top 10 Skills", size="5", font_family=t.FONT_HEADING, color=t.DARK),
                    rx.text("Primary technical competencies detected", color=t.SECONDARY, font_size="0.8rem"),
                    spacing="1", align_items="start", margin_bottom=t.SPACE_4,
                ),
                rx.cond(
                    InsightsState.skill_dist.length() > 0,
                    rx.vstack(
                        rx.foreach(InsightsState.skill_dist, skill_dist_item),
                        width="100%",
                        max_height="800px",
                        overflow_y="auto",
                        padding_right="10px",
                        custom_attrs={"style": {"scrollbar-width": "thin", "scrollbar-color": f"{t.PRIMARY} transparent"}}
                    ),
                    rx.vstack(rx.text("No skill data available.", color=t.SECONDARY), align="center", padding=t.SPACE_12),
                ),
                **t.card_style(), height="100%", display="flex", flex_direction="column"
            ),
            
            # 3. Model Evaluation Metrics
            rx.box(
                rx.vstack(
                    rx.heading("Model Evaluation", size="5", font_family=t.FONT_HEADING, color=t.DARK),
                    rx.text("Clustering performance metrics", color=t.SECONDARY, font_size="0.8rem"),
                    spacing="1", align_items="start", margin_bottom=t.SPACE_4,
                ),
                rx.vstack(
                    rx.box(
                        rx.text("Silhouette Score", font_size="0.85rem", font_weight="700", color=t.SECONDARY, text_transform="uppercase"),
                        rx.heading(InsightsState.silhouette_score, size="7", color=t.PRIMARY, margin_top="4px"),
                        rx.text("Measures cluster density and separation (closer to 1 is better).", font_size="0.75rem", color=t.SECONDARY, margin_top="8px", line_height="1.4"),
                        padding="16px", background_color=t.PRIMARY_LIGHT, border_radius="10px", width="100%", margin_bottom="12px"
                    ),
                    rx.box(
                        rx.text("Noise Count (Unclustered)", font_size="0.85rem", font_weight="700", color=t.SECONDARY, text_transform="uppercase"),
                        rx.heading(InsightsState.noise_count, size="7", color=t.DARK, margin_top="4px"),
                        rx.text("Number of resumes that could not be assigned to any domain.", font_size="0.75rem", color=t.SECONDARY, margin_top="8px", line_height="1.4"),
                        padding="16px", background_color=t.SURFACE, border=f"1px solid {t.BORDER}", border_radius="10px", width="100%", margin_bottom="12px"
                    ),
                    rx.box(
                        rx.text("Knowledge Graph Taxonomy", font_size="0.85rem", font_weight="700", color=t.SECONDARY, text_transform="uppercase"),
                        rx.heading(InsightsState.taxonomy_cluster_count + " Domains", size="7", color=t.DARK, margin_top="4px"),
                        rx.text("Total enterprise clusters the system is mathematically configured to detect and map.", font_size="0.75rem", color=t.SECONDARY, margin_top="8px", line_height="1.4"),
                        padding="16px", background_color=t.SURFACE, border=f"1px solid {t.BORDER}", border_radius="10px", width="100%"
                    ),
                    width="100%", spacing="0"
                ),
                **t.card_style(), height="100%", display="flex", flex_direction="column"
            ),
            grid_template_columns=rx.breakpoints(initial="1fr", sm="1fr 1fr", lg="1.2fr 1fr 1fr"), 
            spacing="4", 
            width="100%",
            margin_bottom=t.SPACE_6,
        ),
        
        # 3. System Architecture (Full Fidelity Diagram)
        technical_architecture(),
        
        width="100%"
    )


def main_content() -> rx.Component:
    return rx.box(
        project_overview(),
        stats_row(),
        rx.box(height=t.SPACE_8),
        dashboard_mixed_content(),
        flex="1",
        padding=t.CONTENT_PADDING,
        min_width="0",
        overflow_x="hidden",
        padding_bottom="80px", # Room for sticky CTA on mobile
    )

# ─────────────────────────────────────────────────────────────────────────────
# Page
# ─────────────────────────────────────────────────────────────────────────────

def dashboard_page() -> rx.Component:
    return rx.box(
        navbar(),
        rx.hstack(
            main_content(),
            spacing="0",
            align_items="start",
            width="100%",
            max_width=t.CONTENT_MAX_W,
            margin="0 auto",
        ),
        footer(),
        background_color=t.BG,
        min_height="100vh",
        font_family=t.FONT_SANS,
        on_mount=[AppState.load_data, InsightsState.load_data],
    )
