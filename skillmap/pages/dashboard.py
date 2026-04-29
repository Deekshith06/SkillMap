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
            "Map talent by skill signals using transformer embeddings and UMAP clustering.",
            font_size="1.1rem",
            color=t.SECONDARY,
            font_family=t.FONT_BODY,
            max_width="680px",
            line_height="1.6",
            text_align="center",
            margin_bottom=t.SPACE_8,
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
            grid_template_columns=rx.breakpoints(initial="1fr", sm="1fr 1.8fr"), 
            spacing="4", 
            width="100%",
            margin_bottom=t.SPACE_6,
        ),
        
        # 3. System Architecture (Full Fidelity Diagram)
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Technical Architecture", size="5", font_family=t.FONT_HEADING, color=t.DARK),
                        rx.text("End-to-end intelligence pipeline and infrastructure", color=t.SECONDARY, font_size="0.9rem"),
                        spacing="1", align_items="start",
                    ),
                    rx.spacer(),
                    rx.badge("Phase 4 Production", variant="surface", color_scheme="orange"),
                    width="100%", align_items="center", margin_bottom=t.SPACE_8,
                ),
                
                # Full Diagram Container
                rx.vstack(
                    # 1. Reflex Frontend
                    rx.box(
                        rx.vstack(
                            rx.text("REFLEX FRONTEND", font_size="0.75rem", font_weight="800", color=t.PRIMARY, margin_bottom="12px"),
                            rx.grid(
                                rx.box(rx.text("/", font_size="0.7rem", font_weight="700"), rx.text("Dashboard", font_size="0.65rem"), padding="8px", border=f"1px solid {t.BORDER}", border_radius="4px", text_align="center", background_color="white"),
                                rx.box(rx.text("/analyze", font_size="0.7rem", font_weight="700"), rx.text("Analyze", font_size="0.65rem"), padding="8px", border=f"1px solid {t.BORDER}", border_radius="4px", text_align="center", background_color="white"),
                                rx.box(rx.text("/bulk", font_size="0.7rem", font_weight="700"), rx.text("Bulk Upload", font_size="0.65rem"), padding="8px", border=f"1px solid {t.BORDER}", border_radius="4px", text_align="center", background_color="white"),
                                rx.box(rx.text("/ats", font_size="0.7rem", font_weight="700"), rx.text("ATS Editor", font_size="0.65rem"), padding="8px", border=f"1px solid {t.BORDER}", border_radius="4px", text_align="center", background_color="white"),
                                columns="4", spacing="2", width="100%"
                            ),
                            # Reflex State
                            rx.box(
                                rx.vstack(
                                    rx.text("Reflex State (rx.State subclasses)", font_size="0.7rem", font_weight="700", color=t.DARK),
                                    rx.text("AppState — AnalyzeState — BulkState — ATSState", font_size="0.7rem", color=t.SECONDARY),
                                    spacing="1", align_items="center"
                                ),
                                width="95%", padding="10px", border=f"1px dashed {t.BORDER}", border_radius="4px", margin_top="12px", background_color="white"
                            ),
                            align_items="center", width="100%"
                        ),
                        width="100%", padding="20px", border=f"2px solid {t.PRIMARY_LIGHT}", border_radius=t.RADIUS_LG, background_color=t.SURFACE_HOVER
                    ),
                    
                    rx.icon("arrow-down", color=t.BORDER, size=24),
                    
                    # 2. FastAPI Service Layer
                    rx.box(
                        rx.vstack(
                            rx.text("FASTAPI SERVICE LAYER", font_size="0.75rem", font_weight="800", color=t.PRIMARY, margin_bottom="8px"),
                            rx.hstack(
                                rx.text("POST /resume/upload", font_size="0.7rem", font_weight="600"),
                                rx.text("|", color=t.BORDER),
                                rx.text("GET /resume/{id}/score", font_size="0.7rem", font_weight="600"),
                                rx.text("|", color=t.BORDER),
                                rx.text("POST /cluster", font_size="0.7rem", font_weight="600"),
                                spacing="4"
                            ),
                            align_items="center", width="100%"
                        ),
                        width="100%", padding="15px", border=f"2px solid {t.BORDER}", border_radius=t.RADIUS_LG, background_color="white"
                    ),
                    
                    rx.icon("arrow-down", color=t.BORDER, size=24),
                    
                    # 3. Processing Engines (3-column)
                    rx.grid(
                        # Ingestion
                        rx.box(
                            rx.vstack(
                                rx.text("INGESTION LAYER", font_size="0.7rem", font_weight="800", color=t.DARK),
                                rx.divider(),
                                rx.text("PDF/DOCX/TXT Parser", font_size="0.65rem"),
                                rx.text("Section Detector", font_size="0.65rem"),
                                rx.text("Text Normalizer", font_size="0.65rem"),
                                align_items="start", spacing="1"
                            ),
                            padding="15px", border=f"1px solid {t.BORDER}", border_radius=t.RADIUS_LG, background_color="white"
                        ),
                        # ATS Engine
                        rx.box(
                            rx.vstack(
                                rx.text("ATS ENGINE", font_size="0.7rem", font_weight="800", color=t.DARK),
                                rx.divider(),
                                rx.text("KeywordScorer (TF-IDF)", font_size="0.65rem"),
                                rx.text("Format Checker", font_size="0.65rem"),
                                rx.text("Section Scorer", font_size="0.65rem"),
                                align_items="start", spacing="1"
                            ),
                            padding="15px", border=f"1px solid {t.BORDER}", border_radius=t.RADIUS_LG, background_color="white"
                        ),
                        # Skill Engine
                        rx.box(
                            rx.vstack(
                                rx.text("SKILL ENGINE", font_size="0.7rem", font_weight="800", color=t.DARK),
                                rx.divider(),
                                rx.text("NER Extractor (spaCy)", font_size="0.65rem"),
                                rx.text("Skill Embedder", font_size="0.65rem"),
                                rx.text("UMAP-HDBSCAN", font_size="0.65rem"),
                                align_items="start", spacing="1"
                            ),
                            padding="15px", border=f"1px solid {t.BORDER}", border_radius=t.RADIUS_LG, background_color="white"
                        ),
                        columns="3", spacing="4", width="100%"
                    ),
                    
                    rx.icon("arrow-down", color=t.BORDER, size=24),
                    
                    # 4. ML Infrastructure
                    rx.box(
                        rx.vstack(
                            rx.text("ML INFRASTRUCTURE", font_size="0.75rem", font_weight="800", color=t.PRIMARY, margin_bottom="8px"),
                            rx.hstack(
                                rx.box(rx.text("DVC Data Versioning", font_size="0.65rem"), padding="6px 12px", border=f"1px solid {t.BORDER}", border_radius="4px"),
                                rx.box(rx.text("MLFlow Tracking", font_size="0.65rem"), padding="6px 12px", border=f"1px solid {t.BORDER}", border_radius="4px"),
                                rx.box(rx.text("Feature Store", font_size="0.65rem"), padding="6px 12px", border=f"1px solid {t.BORDER}", border_radius="4px"),
                                spacing="3"
                            ),
                            align_items="center", width="100%"
                        ),
                        width="100%", padding="15px", border=f"2px solid {t.BORDER}", border_radius=t.RADIUS_LG, background_color=t.BG
                    ),
                    
                    width="100%", spacing="0", align_items="center"
                ),
                width="100%"
            ),
            **t.card_style(), width="100%"
        ),
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
