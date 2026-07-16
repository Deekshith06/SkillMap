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

from skillmap.components.charts import cluster_pie_chart
from skillmap.components.navbar import navbar
from skillmap.components.ui import (
    footer,
    skeleton_card,
    stats_card,
)
from skillmap.state.app_state import AppState
from skillmap.state.insights_state import InsightsState
from skillmap.styles import theme as t

# ─────────────────────────────────────────────────────────────────────────────
# (Sidebar removed)
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Project overview hero
# ─────────────────────────────────────────────────────────────────────────────


def project_overview() -> rx.Component:
    return rx.grid(
        rx.vstack(
            rx.hstack(
                rx.box(
                    width="8px",
                    height="8px",
                    border_radius="50%",
                    background_color="#6FD0B5",
                ),
                rx.text(
                    "SKILLMAP LITE",
                    font_family=t.FONT_MONO,
                    font_size="0.72rem",
                    font_weight=t.W_BOLD,
                    color="#A9C0C3",
                ),
                spacing="2",
                align="center",
            ),
            rx.heading(
                "SkillMap",
                font_size=rx.breakpoints(initial="2.35rem", md="3.25rem"),
                font_family=t.FONT_HEADING,
                font_weight=t.W_BOLD,
                color="white",
                letter_spacing="0",
                line_height="1.1",
            ),
            rx.text(
                "Evidence-first talent matching for resumes and job requirements.",
                font_size=rx.breakpoints(initial="1rem", md="1.12rem"),
                color="#D5E1E2",
                font_family=t.FONT_BODY,
                max_width="580px",
                line_height="1.6",
            ),
            rx.flex(
                rx.button(
                    rx.icon("scan", size=17),
                    "Analyze resume",
                    on_click=rx.redirect("/analyze"),
                    width=rx.breakpoints(initial="100%", sm="auto"),
                    **t.btn_primary(padding="0.75rem 1.25rem"),
                ),
                rx.button(
                    rx.icon("files", size=17),
                    "Batch analysis",
                    on_click=rx.redirect("/bulk"),
                    width=rx.breakpoints(initial="100%", sm="auto"),
                    **t.btn_secondary(
                        padding="0.75rem 1.25rem",
                        background_color="transparent",
                        color="white",
                        border="1px solid rgba(255,255,255,0.28)",
                        _hover={"background_color": "rgba(255,255,255,0.08)"},
                    ),
                ),
                flex_direction=rx.breakpoints(initial="column", sm="row"),
                gap=t.SPACE_3,
                width=rx.breakpoints(initial="100%", sm="auto"),
                margin_top=t.SPACE_3,
            ),
            spacing="3",
            align_items="start",
        ),
        rx.vstack(
            rx.text(
                "RUNTIME PROFILE",
                font_family=t.FONT_MONO,
                font_size="0.7rem",
                font_weight=t.W_BOLD,
                color="#A9C0C3",
            ),
            *[
                rx.hstack(
                    rx.icon(icon, size=17, color="#6FD0B5"),
                    rx.text(label, color="#A9C0C3", font_size="0.85rem"),
                    rx.spacer(),
                    rx.text(value, color="white", font_weight=t.W_SEMI, font_size="0.88rem"),
                    width="100%",
                    align="center",
                    spacing="3",
                    padding="0.7rem 0",
                    border_bottom="1px solid rgba(255,255,255,0.12)",
                )
                for icon, label, value in [
                    ("cpu", "Inference", "Lexical"),
                    ("shield-check", "Processing", "In memory"),
                    ("database", "Taxonomy", "Versioned"),
                ]
            ],
            width="100%",
            spacing="0",
            padding=rx.breakpoints(initial=f"{t.SPACE_5} 0 0", lg=f"0 0 0 {t.SPACE_6}"),
            border_top=rx.breakpoints(initial="1px solid rgba(255,255,255,0.14)", lg="none"),
            border_left=rx.breakpoints(initial="none", lg="1px solid rgba(255,255,255,0.14)"),
            align_items="start",
        ),
        grid_template_columns=rx.breakpoints(
            initial="1fr", lg="minmax(0, 1.7fr) minmax(260px, 0.8fr)"
        ),
        gap=rx.breakpoints(initial=t.SPACE_5, lg=t.SPACE_7),
        align_items="center",
        width="100%",
        background_color=t.DARK,
        border_radius=t.RADIUS_LG,
        padding=rx.breakpoints(initial=t.SPACE_5, md=t.SPACE_7),
        margin_top=rx.breakpoints(initial="0", md=t.SPACE_4),
        margin_bottom=t.SPACE_5,
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
        rx.grid(
            *[skeleton_card("100px") for _ in range(3)],
            grid_template_columns=rx.breakpoints(initial="1fr", sm="repeat(3, minmax(0, 1fr))"),
            gap=t.SPACE_3,
            width="100%",
        ),
        rx.grid(
            stats_card("users", AppState.stats.get("total_resumes", "0"), "Total Resumes"),
            stats_card(
                "award",
                InsightsState.taxonomy_cluster_count,
                "Taxonomy Domains",
                t.BRAND,
            ),
            stats_card(
                "activity",
                InsightsState.total_clusters_count.to(str),
                "Clusters Identified",
                t.PRIMARY,
            ),
            grid_template_columns=rx.breakpoints(initial="1fr", sm="repeat(3, minmax(0, 1fr))"),
            gap=t.SPACE_3,
            width="100%",
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Mixed Insights & Dashboard Layout
# ─────────────────────────────────────────────────────────────────────────────


def cluster_list_item(cluster: dict, index: int) -> rx.Component:
    # Use consistent orange shades from theme
    color = rx.Var.create(t.ORANGE_PALETTE)[index % 10]

    return rx.hstack(
        rx.box(
            width="12px",
            height="12px",
            border_radius="2px",
            background_color=color,
            flex_shrink="0",
        ),
        rx.text(cluster["name"], font_size="0.85rem", font_weight="500", color=t.DARK, flex="1"),
        rx.text(
            cluster["resume_count"].to(str), font_size="0.85rem", font_weight="700", color=t.DARK
        ),
        rx.text(
            cluster["percent"],
            font_size="0.85rem",
            font_weight="700",
            color=t.PRIMARY,
            width="45px",
            text_align="right",
        ),
        width="100%",
        align_items="center",
        spacing="3",
        margin_bottom="8px",
    )


def skill_dist_item(item: dict) -> rx.Component:
    # item is passed with "index", "skill", "count", "percent"
    return rx.vstack(
        rx.hstack(
            rx.box(
                rx.text(item["index"], color="white", font_size="0.75rem", font_weight="700"),
                width="24px",
                height="24px",
                border_radius="50%",
                background_color=t.PRIMARY,
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
            ),
            rx.text(item["skill"], font_size="0.9rem", font_weight="700", color=t.DARK),
            rx.spacer(),
            rx.text(item["count"].to(str) + " occurrences", font_size="0.8rem", color=t.SECONDARY),
            rx.text(
                item["percent"],
                font_size="0.85rem",
                font_weight="700",
                color=t.PRIMARY,
                width="40px",
                text_align="right",
            ),
            width="100%",
            align_items="center",
            spacing="3",
        ),
        rx.box(
            rx.box(
                width=item["percent"], height="8px", background_color=t.PRIMARY, border_radius="4px"
            ),
            width="100%",
            height="8px",
            background_color=t.PRIMARY_LIGHT,
            border_radius="4px",
            overflow="hidden",
        ),
        width="100%",
        spacing="2",
        margin_bottom="16px",
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
            rx.text(
                path,
                font_size="13px",
                font_weight="500",
                color=t.ARCH_NEUTRAL_900,
                font_family=t.FONT_MONO,
            ),
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
            rx.text(
                method,
                font_size="10px",
                font_weight="500",
                color=t.ARCH_ORANGE_600,
                font_family=t.FONT_MONO,
                text_transform="uppercase",
            ),
            rx.text(
                path,
                font_size="12px",
                font_weight="400",
                color=t.ARCH_NEUTRAL_900,
                font_family=t.FONT_MONO,
            ),
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
        rx.box(
            width="3px",
            height="3px",
            border_radius="50%",
            background_color=t.ARCH_ORANGE_600,
            opacity="0.6",
            margin_top="7px",
        ),
        rx.text(
            text,
            font_size="11.5px",
            color=t.ARCH_NEUTRAL_500,
            font_weight="400",
            font_family=t.FONT_MONO,
        ),
        spacing="3",
        align_items="start",
    )


def arch_connector() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.box(width="1.5px", height="20px", background_color=t.ARCH_NEUTRAL_300),
            rx.icon("chevron-down", size=14, color=t.ARCH_NEUTRAL_300, margin_top="-6px"),
            spacing="0",
            align_items="center",
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
                    rx.heading(
                        "Technical Architecture",
                        font_size="20px",
                        font_weight="700",
                        font_family=t.FONT_HEADING,
                        color=t.ARCH_NEUTRAL_900,
                    ),
                    rx.text(
                        "Deployed frontend, state backend, and inference runtime",
                        color=t.ARCH_NEUTRAL_500,
                        font_size="12px",
                        font_family=t.FONT_MONO,
                    ),
                    spacing="1",
                    align_items="start",
                ),
                rx.spacer(),
                rx.box(
                    rx.text(
                        "Lite Runtime",
                        font_size="11px",
                        font_weight="500",
                        font_family=t.FONT_MONO,
                        color=t.ARCH_ORANGE_600,
                    ),
                    background_color=t.ARCH_ORANGE_50,
                    border=f"1px solid {t.ARCH_ORANGE_100}",
                    padding="4px 10px",
                    border_radius="4px",
                ),
                width="100%",
                align_items="center",
                margin_bottom="32px",
            ),
            # 2. REFLEX FRONTEND Section
            rx.box(
                rx.vstack(
                    arch_label("STATIC REFLEX FRONTEND · VERCEL"),
                    rx.grid(
                        arch_box("/", "· Dashboard"),
                        arch_box("/analyze", "· Analyze"),
                        arch_box("/bulk", "· Bulk Upload"),
                        arch_box("/ats", "· ATS Editor"),
                        columns="4",
                        spacing="3",
                        width="100%",
                    ),
                    # State box
                    rx.box(
                        rx.vstack(
                            rx.text(
                                "Reflex State (rx.State subclasses)",
                                font_size="13px",
                                font_weight="600",
                                font_family=t.FONT_HEADING,
                                color=t.ARCH_NEUTRAL_900,
                            ),
                            rx.hstack(
                                rx.text(
                                    "AppState",
                                    font_size="11px",
                                    color=t.ARCH_NEUTRAL_500,
                                    font_family=t.FONT_MONO,
                                ),
                                rx.text("—", color=t.ARCH_NEUTRAL_300),
                                rx.text(
                                    "AnalyzeState",
                                    font_size="11px",
                                    color=t.ARCH_NEUTRAL_500,
                                    font_family=t.FONT_MONO,
                                ),
                                rx.text("—", color=t.ARCH_NEUTRAL_300),
                                rx.text(
                                    "BulkState",
                                    font_size="11px",
                                    color=t.ARCH_NEUTRAL_500,
                                    font_family=t.FONT_MONO,
                                ),
                                rx.text("—", color=t.ARCH_NEUTRAL_300),
                                rx.text(
                                    "ATSState",
                                    font_size="11px",
                                    color=t.ARCH_NEUTRAL_500,
                                    font_family=t.FONT_MONO,
                                ),
                                spacing="2",
                            ),
                            spacing="1",
                            align_items="start",
                        ),
                        width="100%",
                        padding="12px 16px",
                        border=f"1px solid {t.ARCH_NEUTRAL_300}",
                        border_radius="8px",
                        margin_top="12px",
                        background_color="white",
                    ),
                    width="100%",
                ),
                width="100%",
                padding="20px",
                border_radius="12px",
                background_color=t.ARCH_ORANGE_50,
                border=f"1px solid {t.ARCH_ORANGE_100}",
            ),
            arch_connector(),
            # 4. Reflex backend workflow layer
            rx.box(
                rx.vstack(
                    arch_label("REFLEX STATE BACKEND · RENDER"),
                    rx.grid(
                        arch_endpoint("EVENT", "secure upload"),
                        arch_endpoint("EVENT", "resume analysis"),
                        arch_endpoint("EVENT", "job matching"),
                        columns="3",
                        spacing="3",
                        width="100%",
                    ),
                    width="100%",
                ),
                width="100%",
                padding="20px",
                border_radius="10px",
                background_color="white",
                border=f"1px solid {t.ARCH_NEUTRAL_300}",
            ),
            arch_connector(),
            # 5. ENGINE BOXES
            rx.grid(
                # Ingestion
                rx.box(
                    rx.text(
                        "INGESTION LAYER",
                        font_size="11px",
                        font_weight="700",
                        font_family=t.FONT_HEADING,
                        color=t.ARCH_NEUTRAL_900,
                        border_bottom=f"1px solid {t.ARCH_NEUTRAL_300}",
                        padding_bottom="8px",
                        margin_bottom="12px",
                    ),
                    rx.vstack(
                        arch_list_item("PDF/DOCX/TXT Parser"),
                        arch_list_item("Section Detector"),
                        arch_list_item("Text Normalizer"),
                        spacing="3",
                        align_items="start",
                    ),
                    padding="16px",
                    background_color="white",
                    border=f"1px solid {t.ARCH_NEUTRAL_300}",
                    border_radius="10px",
                    _hover={"border_color": t.ARCH_NEUTRAL_200},
                    transition=t.TRANSITION_BASE,
                ),
                # ATS Engine
                rx.box(
                    rx.text(
                        "ATS ENGINE",
                        font_size="11px",
                        font_weight="700",
                        font_family=t.FONT_HEADING,
                        color=t.ARCH_NEUTRAL_900,
                        border_bottom=f"1px solid {t.ARCH_NEUTRAL_300}",
                        padding_bottom="8px",
                        margin_bottom="12px",
                    ),
                    rx.vstack(
                        arch_list_item("TF-IDF + BM25 Matcher"),
                        arch_list_item("Format Checker"),
                        arch_list_item("Section Scorer"),
                        spacing="3",
                        align_items="start",
                    ),
                    padding="16px",
                    background_color="white",
                    border=f"1px solid {t.ARCH_NEUTRAL_300}",
                    border_radius="10px",
                    _hover={"border_color": t.ARCH_NEUTRAL_200},
                    transition=t.TRANSITION_BASE,
                ),
                # Intelligence Engine
                rx.box(
                    rx.text(
                        "INTELLIGENCE ENGINE",
                        font_size="11px",
                        font_weight="700",
                        font_family=t.FONT_HEADING,
                        color=t.ARCH_NEUTRAL_900,
                        border_bottom=f"1px solid {t.ARCH_NEUTRAL_300}",
                        padding_bottom="8px",
                        margin_bottom="12px",
                    ),
                    rx.vstack(
                        arch_list_item("Taxonomy Skill Extractor"),
                        arch_list_item("Versioned Lite Classifier"),
                        arch_list_item("Evidence & Seniority Rules"),
                        spacing="3",
                        align_items="start",
                    ),
                    padding="16px",
                    background_color="#FFFBEB",
                    border="1px solid #FCD34D",
                    border_radius="10px",
                    _hover={"border_color": "#F59E0B"},
                    transition=t.TRANSITION_BASE,
                ),
                columns="3",
                spacing="3",
                width="100%",
                margin_bottom="8px",
            ),
            arch_connector(),
            # 6. Runtime artifacts
            rx.box(
                rx.vstack(
                    arch_label("VERSIONED RUNTIME ARTIFACTS"),
                    rx.hstack(
                        rx.box(
                            rx.text(
                                "Checksum Manifest",
                                font_size="12px",
                                font_family=t.FONT_MONO,
                                color=t.ARCH_NEUTRAL_500,
                            ),
                            padding="8px 16px",
                            background_color="white",
                            border=f"1px solid {t.ARCH_NEUTRAL_300}",
                            border_radius="6px",
                        ),
                        rx.box(
                            rx.text(
                                "Skill Taxonomy",
                                font_size="12px",
                                font_family=t.FONT_MONO,
                                color=t.ARCH_NEUTRAL_500,
                            ),
                            padding="8px 16px",
                            background_color="white",
                            border=f"1px solid {t.ARCH_NEUTRAL_300}",
                            border_radius="6px",
                        ),
                        rx.box(
                            rx.text(
                                "Compact Classifier",
                                font_size="12px",
                                font_family=t.FONT_MONO,
                                color=t.ARCH_NEUTRAL_500,
                            ),
                            padding="8px 16px",
                            background_color="white",
                            border=f"1px solid {t.ARCH_NEUTRAL_300}",
                            border_radius="6px",
                        ),
                        spacing="3",
                        width="100%",
                        justify_content="center",
                        flex_wrap="wrap",
                    ),
                    width="100%",
                ),
                width="100%",
                padding="20px",
                border_radius="12px",
                background_color=t.ARCH_ORANGE_50,
                border=f"1px solid {t.ARCH_ORANGE_100}",
            ),
            spacing="0",
            width="100%",
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
                    rx.heading(
                        "Cluster Distribution", size="5", font_family=t.FONT_HEADING, color=t.DARK
                    ),
                    rx.text(
                        "Proportional breakdown of clusters", color=t.SECONDARY, font_size="0.8rem"
                    ),
                    spacing="1",
                    align_items="start",
                    margin_bottom=t.SPACE_4,
                ),
                rx.cond(
                    InsightsState.cluster_dist.length() > 0,
                    rx.vstack(
                        rx.box(
                            cluster_pie_chart(
                                InsightsState.cluster_dist,
                                InsightsState.total_resumes_count,
                                height=280,
                            ),
                            display="flex",
                            justify_content="center",
                            width="100%",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.foreach(
                                    InsightsState.cluster_dist, lambda c, i: cluster_list_item(c, i)
                                ),
                                width="100%",
                                max_height="500px",
                                overflow_y="auto",
                                padding_right="10px",
                                custom_attrs={
                                    "style": {
                                        "scrollbarWidth": "thin",
                                        "scrollbarColor": f"{t.PRIMARY} transparent",
                                    }
                                },
                            ),
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.icon("inbox", size=24, color=t.SECONDARY),
                        rx.text("No analyses yet", color=t.DARK, font_weight=t.W_SEMI),
                        rx.text(
                            "Cluster distribution appears after resumes are analyzed.",
                            color=t.SECONDARY,
                            font_size="0.82rem",
                            text_align="center",
                        ),
                        rx.link(
                            "Analyze a resume",
                            href="/analyze",
                            color=t.PRIMARY,
                            font_weight=t.W_SEMI,
                            font_size="0.85rem",
                        ),
                        spacing="2",
                        align="center",
                        padding=t.SPACE_7,
                    ),
                ),
                **t.card_style(),
                display="flex",
                flex_direction="column",
            ),
            # 2. Skill Distribution
            rx.box(
                rx.vstack(
                    rx.heading("Top 10 Skills", size="5", font_family=t.FONT_HEADING, color=t.DARK),
                    rx.text(
                        "Primary technical competencies detected",
                        color=t.SECONDARY,
                        font_size="0.8rem",
                    ),
                    spacing="1",
                    align_items="start",
                    margin_bottom=t.SPACE_4,
                ),
                rx.cond(
                    InsightsState.skill_dist.length() > 0,
                    rx.vstack(
                        rx.foreach(InsightsState.skill_dist, skill_dist_item),
                        width="100%",
                        max_height="800px",
                        overflow_y="auto",
                        padding_right="10px",
                        custom_attrs={
                            "style": {
                                "scrollbarWidth": "thin",
                                "scrollbarColor": f"{t.PRIMARY} transparent",
                            }
                        },
                    ),
                    rx.vstack(
                        rx.icon("list-filter", size=24, color=t.SECONDARY),
                        rx.text("No skill evidence yet", color=t.DARK, font_weight=t.W_SEMI),
                        rx.text(
                            "Detected skills will be ranked here.",
                            color=t.SECONDARY,
                            font_size="0.82rem",
                            text_align="center",
                        ),
                        spacing="2",
                        align="center",
                        padding=t.SPACE_7,
                    ),
                ),
                **t.card_style(),
                display="flex",
                flex_direction="column",
            ),
            # 3. Model Evaluation Metrics
            rx.box(
                rx.vstack(
                    rx.heading(
                        "Runtime Integrity", size="5", font_family=t.FONT_HEADING, color=t.DARK
                    ),
                    rx.text(
                        "Production inference properties", color=t.SECONDARY, font_size="0.8rem"
                    ),
                    spacing="1",
                    align_items="start",
                    margin_bottom=t.SPACE_4,
                ),
                rx.vstack(
                    rx.box(
                        rx.text(
                            "Production Mode",
                            font_size="0.85rem",
                            font_weight="700",
                            color=t.SECONDARY,
                            text_transform="uppercase",
                        ),
                        rx.heading("Lite", size="7", color=t.PRIMARY, margin_top="4px"),
                        rx.text(
                            "Taxonomy, TF-IDF, BM25, and deterministic experience rules.",
                            font_size="0.75rem",
                            color=t.SECONDARY,
                            margin_top="8px",
                            line_height="1.4",
                        ),
                        padding="16px",
                        background_color=t.PRIMARY_LIGHT,
                        border_radius="10px",
                        width="100%",
                        margin_bottom="12px",
                    ),
                    rx.box(
                        rx.text(
                            "Privacy Boundary",
                            font_size="0.85rem",
                            font_weight="700",
                            color=t.SECONDARY,
                            text_transform="uppercase",
                        ),
                        rx.heading("In memory", size="7", color=t.DARK, margin_top="4px"),
                        rx.text(
                            "Uploaded bytes and resume text are not written to persistent storage.",
                            font_size="0.75rem",
                            color=t.SECONDARY,
                            margin_top="8px",
                            line_height="1.4",
                        ),
                        padding="16px",
                        background_color=t.SURFACE,
                        border=f"1px solid {t.BORDER}",
                        border_radius="10px",
                        width="100%",
                        margin_bottom="12px",
                    ),
                    rx.box(
                        rx.text(
                            "Knowledge Graph Taxonomy",
                            font_size="0.85rem",
                            font_weight="700",
                            color=t.SECONDARY,
                            text_transform="uppercase",
                        ),
                        rx.heading(
                            InsightsState.taxonomy_cluster_count + " Domains",
                            size="7",
                            color=t.DARK,
                            margin_top="4px",
                        ),
                        rx.text(
                            "Versioned domains available for direct skill-evidence matching.",
                            font_size="0.75rem",
                            color=t.SECONDARY,
                            margin_top="8px",
                            line_height="1.4",
                        ),
                        padding="16px",
                        background_color=t.SURFACE,
                        border=f"1px solid {t.BORDER}",
                        border_radius="10px",
                        width="100%",
                    ),
                    width="100%",
                    spacing="0",
                ),
                **t.card_style(),
                height="100%",
                display="flex",
                flex_direction="column",
            ),
            grid_template_columns=rx.breakpoints(initial="1fr", sm="1fr 1fr", lg="1.2fr 1fr 1fr"),
            spacing="4",
            width="100%",
            margin_bottom=t.SPACE_6,
        ),
        # 3. System Architecture (Full Fidelity Diagram)
        technical_architecture(),
        width="100%",
    )


def main_content() -> rx.Component:
    return rx.box(
        project_overview(),
        stats_row(),
        rx.box(height=t.SPACE_5),
        dashboard_mixed_content(),
        flex="1",
        padding=rx.breakpoints(initial=t.SPACE_4, md=t.CONTENT_PADDING),
        min_width="0",
        overflow_x="hidden",
        padding_bottom="80px",  # Room for sticky CTA on mobile
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
    )
