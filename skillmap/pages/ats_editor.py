"""ats_editor.py — Upload → Score → Suggestions ATS page."""

import reflex as rx

from skillmap.components.file_upload import file_drop_zone
from skillmap.components.skill_badge import skill_pill_muted, skill_pill_primary
from skillmap.components.ui import error_alert, skeleton_bar
from skillmap.state.ats_state import ATSState
from skillmap.styles import theme as t

# ── Sub-score bar ─────────────────────────────────────────────────────────────


def sub_score_bar(label: str, score) -> rx.Component:
    """Horizontal progress bar for a sub-category score."""
    return rx.vstack(
        rx.grid(
            rx.text(label, font_size="0.85rem", font_weight="600", color=t.DARK),
            rx.spacer(),
            rx.text(
                score.to_string() + "%",
                font_size="0.85rem",
                font_weight="700",
                color=t.PRIMARY,
            ),
            width="100%",
        ),
        rx.box(
            rx.box(
                height="100%",
                width=score.to_string() + "%",
                background_color=t.PRIMARY,
                border_radius=t.RADIUS_PILL,
                transition=f"width {t.TRANSITION_BASE}",
            ),
            width="100%",
            height="6px",
            background_color=t.SECONDARY_LIGHT,
            border_radius=t.RADIUS_PILL,
            overflow="hidden",
        ),
        spacing="1",
        width="100%",
    )


# ── Suggestion card ───────────────────────────────────────────────────────────


def suggestion_card(s) -> rx.Component:
    """s is an ATSSuggestion PropsBase object."""
    return rx.box(
        rx.hstack(
            rx.box(
                s.priority.upper(),
                background_color=t.PRIMARY_LIGHT,
                color=t.PRIMARY,
                padding="2px 8px",
                border_radius=t.RADIUS_PILL,
                font_size="0.7rem",
                font_weight="800",
            ),
            rx.text(s.title, font_weight="700", color=t.DARK, font_size="0.9rem"),
            spacing="2",
            align="center",
        ),
        rx.text(s.detail, font_size="0.85rem", color=t.SECONDARY, margin_top=t.SPACE_1),
        background_color=t.SURFACE_HOVER,
        border_radius=t.RADIUS_MD,
        padding=t.SPACE_3,
        margin_bottom=t.SPACE_2,
        border_left=f"3px solid {t.PRIMARY}",
    )


# ── Upload card (Match Analyze Layout) ────────────────────────────────────────


def upload_card() -> rx.Component:
    return rx.box(
        rx.heading(
            "ATS Optimizer",
            size="6",
            font_family=t.FONT_HEADING,
            color=t.DARK,
            margin_bottom="0.5rem",
        ),
        rx.text(
            "Score and optimize your resume against specific job requirements.",
            color=t.SECONDARY,
            font_size="0.9rem",
            margin_bottom=t.SPACE_6,
        ),
        rx.text(
            "Resume", font_size="0.85rem", font_weight="700", color=t.DARK, margin_bottom="0.5rem"
        ),
        rx.cond(
            ATSState.ats_filename != "",
            rx.hstack(
                rx.icon("file-check-2", size=18, color=t.SUCCESS),
                rx.text(
                    ATSState.ats_filename, font_size="0.85rem", font_weight="600", color=t.DARK
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=14),
                    on_click=ATSState.clear_resume_file,
                    background="transparent",
                    color=t.SECONDARY,
                    cursor="pointer",
                    padding="0",
                ),
                padding=t.SPACE_3,
                background_color="rgba(107, 143, 113, 0.05)",
                border="1px solid rgba(107, 143, 113, 0.2)",
                border_radius=t.RADIUS_MD,
                width="100%",
                align_items="center",
                height="64px",
            ),
            file_drop_zone(
                ATSState.handle_ats_upload,
                label="Drop resume or browse files",
                sublabel="PDF, DOCX or TXT · 2 MB max",
                upload_id="ats_upload",
            ),
        ),
        rx.box(height=t.SPACE_6),
        rx.text(
            "Job Description (Optional)",
            font_size="0.85rem",
            font_weight="700",
            color=t.DARK,
            margin_bottom="0.5rem",
        ),
        # Tabs for JD
        rx.hstack(
            rx.box(
                rx.hstack(
                    rx.icon("file-text", size=14),
                    rx.text("Paste Text"),
                    spacing="2",
                    align="center",
                ),
                padding="0.5rem 0",
                flex="1",
                cursor="pointer",
                font_weight="600",
                font_size="0.85rem",
                text_align="center",
                color=rx.cond(ATSState.jd_mode == "text", t.PRIMARY, t.SECONDARY),
                border_bottom=rx.cond(
                    ATSState.jd_mode == "text", f"2px solid {t.PRIMARY}", "2px solid transparent"
                ),
                on_click=ATSState.set_jd_mode("text"),
            ),
            rx.box(
                rx.hstack(
                    rx.icon("upload", size=14), rx.text("Upload File"), spacing="2", align="center"
                ),
                padding="0.5rem 0",
                flex="1",
                cursor="pointer",
                font_weight="600",
                font_size="0.85rem",
                text_align="center",
                color=rx.cond(ATSState.jd_mode == "file", t.PRIMARY, t.SECONDARY),
                border_bottom=rx.cond(
                    ATSState.jd_mode == "file", f"2px solid {t.PRIMARY}", "2px solid transparent"
                ),
                on_click=ATSState.set_jd_mode("file"),
            ),
            width="100%",
            border_bottom=f"1px solid {t.SURFACE_BORDER}",
            margin_bottom=t.SPACE_4,
        ),
        rx.cond(
            ATSState.jd_mode == "text",
            rx.text_area(
                placeholder="Paste job description...",
                value=ATSState.jd_text,
                on_change=ATSState.set_jd_text,
                height="100px",
                width="100%",
                border=f"1px solid {t.SURFACE_BORDER}",
                border_radius=t.RADIUS_MD,
                padding=t.SPACE_3,
                font_family=t.FONT_BODY,
                background_color=t.SURFACE,
                color=t.DARK,
                _placeholder={"color": t.TEXT_MUTED},
            ),
            rx.cond(
                ATSState.jd_filename != "",
                rx.hstack(
                    rx.icon("file-text", size=18, color=t.PRIMARY),
                    rx.text(
                        ATSState.jd_filename, font_size="0.85rem", font_weight="600", color=t.DARK
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("x", size=14),
                        on_click=ATSState.clear_jd_file,
                        background="transparent",
                        color=t.SECONDARY,
                        cursor="pointer",
                        padding="0",
                    ),
                    padding=t.SPACE_3,
                    background_color="rgba(204, 69, 53, 0.05)",
                    border="1px solid rgba(204, 69, 53, 0.2)",
                    border_radius=t.RADIUS_MD,
                    width="100%",
                    align_items="center",
                    height="64px",
                ),
                rx.upload(
                    rx.hstack(
                        rx.icon("upload", size=18, color=t.PRIMARY),
                        rx.text(
                            "Click or drop JD file here",
                            font_weight="600",
                            color=t.DARK,
                            font_size="0.85rem",
                        ),
                        spacing="2",
                        align="center",
                        justify="center",
                        width="100%",
                    ),
                    id="ats_jd_upload",
                    on_drop=ATSState.handle_jd_upload(rx.upload_files(upload_id="ats_jd_upload")),
                    multiple=False,
                    border=f"1px dashed {t.PRIMARY}",
                    border_radius=t.RADIUS_MD,
                    background_color=t.PRIMARY_LIGHT,
                    padding=t.SPACE_3,
                    width="100%",
                    cursor="pointer",
                    height="64px",
                    display="flex",
                    flex_direction="column",
                    justify_content="center",
                ),
            ),
        ),
        # Actions
        rx.hstack(
            rx.button(
                rx.text(rx.cond(ATSState.ats_loading, "Scoring...", "Get ATS Score")),
                on_click=ATSState.score_resume,
                disabled=rx.cond(ATSState.ats_filename == "", True, ATSState.ats_loading),
                **t.btn_primary(
                    flex="1",
                    padding="0.8rem",
                    font_size="1rem",
                    background_color=rx.cond(
                        ATSState.ats_filename == "", "rgba(204,69,53,0.5)", t.PRIMARY
                    ),
                    _disabled={"opacity": "1", "cursor": "not-allowed"},
                ),
            ),
            rx.button(
                rx.text("Reset"),
                on_click=ATSState.reset_ats,
                **t.btn_ghost(
                    flex="0 0 auto", padding="0.8rem 1.5rem", border=f"1px solid {t.BORDER}"
                ),
            ),
            spacing="3",
            margin_top=t.SPACE_6,
            width="100%",
            align_items="center",
        ),
        rx.cond(
            ATSState.ats_loading,
            rx.box(
                rx.text(
                    "Connecting to the SkillMap analysis engine...", font_weight="700", color=t.DARK
                ),
                rx.text(
                    "The demonstration server may be waking up after inactivity.",
                    font_size="0.82rem",
                    color=t.SECONDARY,
                ),
                padding=t.SPACE_3,
                margin_top=t.SPACE_4,
                background_color=t.PRIMARY_LIGHT,
                border_radius=t.RADIUS_MD,
            ),
            rx.box(),
        ),
        # Error
        rx.cond(
            ATSState.ats_error != "",
            error_alert(ATSState.ats_error),
            rx.box(),
        ),
        background_color=t.SURFACE,
        border_radius=t.RADIUS_LG,
        padding=t.SPACE_6,
        box_shadow=t.SHADOW_SM,
        width="100%",
    )


# ── Results panel (shown after scoring) ──────────────────────────────────────

# ── Results panel (shown after scoring) ──────────────────────────────────────


def score_color(score) -> str:
    return rx.cond(
        score >= 90,
        t.SUCCESS,
        rx.cond(
            score >= 75,
            t.PRIMARY,
            rx.cond(
                score >= 50,
                "#E67E22",  # Orange
                t.ERROR,
            ),
        ),
    )


def results_panel() -> rx.Component:
    return rx.vstack(
        # Top Row: Metrics
        rx.hstack(
            rx.box(
                rx.vstack(
                    rx.text(
                        "ATS Score",
                        font_size="0.75rem",
                        font_weight="700",
                        color=t.SECONDARY,
                        text_transform="uppercase",
                    ),
                    rx.heading(
                        ATSState.ats_total_score.to_string() + "%",
                        size="7",
                        color=score_color(ATSState.ats_total_score),
                    ),
                    spacing="1",
                    align_items="start",
                ),
                **t.card_style(),
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    rx.text(
                        "Keywords Matched",
                        font_size="0.75rem",
                        font_weight="700",
                        color=t.SECONDARY,
                        text_transform="uppercase",
                    ),
                    rx.heading(ATSState.ats_matched_kw.length().to(str), size="7", color=t.DARK),
                    spacing="1",
                    align_items="start",
                ),
                **t.card_style(),
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    rx.text(
                        "Primary Domain",
                        font_size="0.75rem",
                        font_weight="700",
                        color=t.SECONDARY,
                        text_transform="uppercase",
                    ),
                    rx.heading(
                        ATSState.detected_domain,
                        size="7",
                        color=t.PRIMARY,
                        font_size="1.2rem",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space="nowrap",
                    ),
                    spacing="1",
                    align_items="start",
                ),
                **t.card_style(),
                flex="1",
            ),
            grid_template_columns=rx.breakpoints(initial="1fr", sm="repeat(3, minmax(0, 1fr))"),
            gap=t.SPACE_3,
            width="100%",
            margin_bottom="1rem",
        ),
        rx.flex(
            rx.badge(ATSState.ats_scoring_mode, variant="soft"),
            rx.text(ATSState.ats_model_version, font_size="0.78rem", color=t.SECONDARY),
            width="100%",
            spacing="2",
            align_items="center",
            margin_bottom="1rem",
        ),
        # Unified Domain Display Box
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.box(
                            rx.icon("briefcase", size=18, color=t.PRIMARY),
                            background_color=t.PRIMARY_LIGHT,
                            padding="8px",
                            border_radius="8px",
                        ),
                        rx.vstack(
                            rx.text(
                                "Primary Domain",
                                font_size="0.75rem",
                                font_weight="700",
                                color=t.SECONDARY,
                                text_transform="uppercase",
                                letter_spacing="0.05em",
                            ),
                            rx.heading(
                                ATSState.detected_domain, size="6", color=t.DARK, margin_top="-4px"
                            ),
                            spacing="0",
                            align_items="start",
                        ),
                        spacing="3",
                        align_items="center",
                    ),
                    rx.text(
                        rx.cond(
                            ATSState.detected_sub_domain != "",
                            ATSState.detected_sub_domain,
                            "General Professional",
                        ),
                        font_size="0.9rem",
                        color=t.SECONDARY,
                        font_weight="500",
                        margin_top="12px",
                    ),
                    rx.hstack(
                        rx.icon("gauge", size=14, color=t.SUCCESS),
                        rx.text("ATS Compatibility: ", font_size="0.85rem", color=t.SECONDARY),
                        rx.text(
                            rx.cond(
                                ATSState.ats_total_score >= 85,
                                "Excellent",
                                rx.cond(
                                    ATSState.ats_total_score >= 70, "Good", "Needs Improvement"
                                ),
                            ),
                            font_size="0.85rem",
                            font_weight="700",
                            color=score_color(ATSState.ats_total_score),
                        ),
                        spacing="2",
                        align_items="center",
                        margin_top="8px",
                    ),
                    align_items="start",
                    flex="1",
                ),
                rx.vstack(
                    rx.text(
                        "Primary Insight",
                        font_size="0.75rem",
                        font_weight="700",
                        color=t.SECONDARY,
                        text_align="right",
                        width="100%",
                        text_transform="uppercase",
                        letter_spacing="0.05em",
                    ),
                    rx.box(
                        rx.icon("sparkles", size=24, color=t.PRIMARY),
                        padding="10px",
                        background_color=t.PRIMARY_LIGHT,
                        border_radius="10px",
                        margin_top="4px",
                    ),
                    spacing="1",
                    align_items="end",
                    min_width="120px",
                ),
                align_items="center",
                width="100%",
                justify_content="space-between",
            ),
            **t.card_style(),
            margin_bottom="1rem",
            width="100%",
            background=f"linear-gradient(135deg, {t.SURFACE} 0%, {t.SURFACE_HOVER} 100%)",
        ),
        # Two Columns for Sub-scores and Matched/Missing
        rx.hstack(
            # Left: Sub-scores
            rx.box(
                rx.vstack(
                    rx.text(
                        "Score Breakdown",
                        font_weight="700",
                        font_size="0.95rem",
                        color=t.DARK,
                        margin_bottom="0.5rem",
                    ),
                    sub_score_bar("Keywords", ATSState.cat_keywords),
                    sub_score_bar("Formatting", ATSState.cat_formatting),
                    sub_score_bar("Contact Info", ATSState.cat_contact),
                    sub_score_bar("Structure", ATSState.cat_structure),
                    sub_score_bar("Achievements", ATSState.cat_achievements),
                    sub_score_bar("Action Verbs", ATSState.cat_action_verbs),
                    sub_score_bar("Length", ATSState.cat_length),
                    spacing="4",
                    width="100%",
                ),
                **t.card_style(),
                width=rx.breakpoints(initial="100%", md="45%"),
            ),
            # Right: Keyword matches / gaps
            rx.box(
                rx.vstack(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("circle-check", size=16, color=t.SUCCESS),
                            rx.text(
                                "Matched Keywords",
                                font_weight="700",
                                font_size="0.9rem",
                                color=t.SUCCESS,
                            ),
                            spacing="2",
                        ),
                        rx.flex(
                            rx.foreach(ATSState.ats_matched_kw, skill_pill_primary),
                            flex_wrap="wrap",
                            gap="6px",
                        ),
                        align_items="start",
                        spacing="3",
                        width="100%",
                    ),
                    rx.box(height="1rem"),
                    rx.vstack(
                        rx.hstack(
                            rx.icon("trending-up", size=16, color=t.PRIMARY),
                            rx.text(
                                "Skills to Improve",
                                font_weight="700",
                                font_size="0.9rem",
                                color=t.PRIMARY,
                            ),
                            spacing="2",
                        ),
                        rx.flex(
                            rx.foreach(ATSState.ats_missing_kw, skill_pill_muted),
                            flex_wrap="wrap",
                            gap="6px",
                        ),
                        align_items="start",
                        spacing="3",
                        width="100%",
                    ),
                    align_items="start",
                    spacing="2",
                    width="100%",
                ),
                **t.card_style(),
                flex="1",
            ),
            gap=t.SPACE_3,
            width="100%",
            margin_bottom="1rem",
            align_items="stretch",
            flex_direction=rx.breakpoints(initial="column", md="row"),
        ),
        # Suggestions
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("sparkles", size=18, color=t.PRIMARY),
                    rx.text(
                        "AI-Powered Suggestions", font_weight="700", font_size="1rem", color=t.DARK
                    ),
                    spacing="2",
                    align_items="center",
                    margin_bottom="0.5rem",
                ),
                rx.foreach(ATSState.ats_suggestions, suggestion_card),
                spacing="2",
                width="100%",
            ),
            **t.card_style(),
            width="100%",
        ),
        spacing="0",
        width="100%",
    )


# ── Page ──────────────────────────────────────────────────────────────────────


def ats_editor_page() -> rx.Component:
    def skeleton_metric_box():
        return rx.box(
            rx.vstack(
                skeleton_bar(width="54%", height="10px"),
                skeleton_bar(width="36%", height="28px", margin_top="6px"),
                spacing="2",
                align_items="start",
            ),
            **t.card_style(),
            flex="1",
            opacity="0.6",
        )

    ats_loading_skeleton_view = rx.vstack(
        # 1. Top Row: Metrics
        rx.grid(
            skeleton_metric_box(),
            skeleton_metric_box(),
            skeleton_metric_box(),
            grid_template_columns=rx.breakpoints(initial="1fr", sm="repeat(3, minmax(0, 1fr))"),
            gap=t.SPACE_3,
            width="100%",
            margin_bottom="1rem",
        ),
        # 2. Unified Domain Box (Full width)
        rx.box(
            rx.flex(
                rx.vstack(
                    rx.hstack(
                        rx.box(
                            width="34px",
                            height="34px",
                            background_color=t.SECONDARY_LIGHT,
                            border_radius="8px",
                            animation="pulse 1.5s ease-in-out infinite",
                        ),
                        rx.vstack(
                            skeleton_bar(width="100px", height="12px"),
                            skeleton_bar(width="200px", height="24px"),
                            spacing="1",
                            align_items="start",
                        ),
                        spacing="3",
                        align_items="center",
                    ),
                    skeleton_bar(width="180px", height="16px", margin_top="12px"),
                    skeleton_bar(width="220px", height="14px", margin_top="8px"),
                    align_items="start",
                    flex="1",
                ),
                rx.vstack(
                    skeleton_bar(width="80px", height="12px"),
                    rx.box(
                        width="80px",
                        height="80px",
                        background_color=t.SECONDARY_LIGHT,
                        border_radius="50%",
                        animation="pulse 1.5s ease-in-out infinite",
                    ),
                    spacing="2",
                    align_items="center",
                    min_width="120px",
                ),
                align_items="center",
                flex_direction=rx.breakpoints(initial="column", sm="row"),
                gap=t.SPACE_4,
                width="100%",
            ),
            **t.card_style(),
            margin_bottom="1rem",
            opacity="0.6",
        ),
        # 3. Two Columns (Breakdown & Keywords)
        rx.flex(
            # Left: Score Breakdown
            rx.box(
                rx.vstack(
                    rx.text(
                        "Score Breakdown",
                        font_size="0.9rem",
                        font_weight="700",
                        color=t.ARCH_NEUTRAL_300,
                        margin_bottom="12px",
                    ),
                    rx.foreach(
                        list(range(7)),
                        lambda _: rx.vstack(
                            rx.hstack(
                                skeleton_bar(width="80px", height="8px"),
                                rx.spacer(),
                                skeleton_bar(width="30px", height="8px"),
                                width="100%",
                            ),
                            skeleton_bar(width="100%", height="6px"),
                            spacing="2",
                            width="100%",
                        ),
                    ),
                    spacing="4",
                    width="100%",
                ),
                **t.card_style(),
                width=rx.breakpoints(initial="100%", md="45%"),
                opacity="0.6",
            ),
            # Right: Matched Skills
            rx.box(
                rx.vstack(
                    rx.text(
                        "Matched Skills",
                        font_size="0.9rem",
                        font_weight="700",
                        color=t.ARCH_NEUTRAL_300,
                        margin_bottom="12px",
                    ),
                    rx.flex(
                        rx.foreach(
                            list(range(12)), lambda _: skeleton_bar(width="80px", height="24px")
                        ),
                        flex_wrap="wrap",
                        gap="8px",
                    ),
                    width="100%",
                    align_items="start",
                ),
                **t.card_style(),
                flex="1",
                opacity="0.6",
            ),
            width="100%",
            gap=t.SPACE_3,
            margin_bottom="1rem",
            align_items="stretch",
            flex_direction=rx.breakpoints(initial="column", md="row"),
        ),
        # 4. Suggestions Card
        rx.box(
            rx.vstack(
                rx.text(
                    "Improvement Suggestions",
                    font_size="0.9rem",
                    font_weight="700",
                    color=t.ARCH_NEUTRAL_300,
                    margin_bottom="12px",
                ),
                rx.foreach(
                    list(range(3)),
                    lambda _: rx.box(
                        skeleton_bar(width="100%", height="14px"),
                        padding="16px",
                        border_radius="8px",
                        background_color=t.ARCH_NEUTRAL_50,
                        width="100%",
                        margin_bottom="8px",
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            **t.card_style(),
            width="100%",
            opacity="0.6",
        ),
        width="100%",
        spacing="0",
    )

    ats_initial_view = rx.center(
        rx.vstack(
            rx.center(
                rx.icon("file-search", color=t.PRIMARY, size=24),
                background_color=t.PRIMARY_LIGHT,
                width="56px",
                height="56px",
                border_radius=t.RADIUS_MD,
                margin_bottom=t.SPACE_2,
            ),
            rx.heading(
                "ATS results will appear here", size="6", font_weight=t.W_BOLD, color=t.DARK
            ),
            rx.text(
                "Add a resume and job description on the left to begin.",
                color=t.SECONDARY,
                text_align="center",
                max_width="340px",
                font_size="0.95rem",
            ),
            align_items="center",
            spacing="2",
        ),
        width="100%",
        min_height=rx.breakpoints(initial="360px", lg="560px"),
        background_color=t.SURFACE,
        border=f"1px dashed {t.BORDER_STRONG}",
        border_radius=t.RADIUS_LG,
        padding=t.SPACE_5,
    )

    return rx.box(
        rx.flex(
            rx.box(
                upload_card(),
                width=rx.breakpoints(initial="100%", lg="32%"),
                min_width=rx.breakpoints(initial="0", lg="360px"),
                flex_shrink="0",
                position=rx.breakpoints(initial="static", lg="sticky"),
                top=rx.breakpoints(initial="auto", lg="88px"),
            ),
            rx.box(
                rx.cond(
                    ATSState.ats_loading,
                    ats_loading_skeleton_view,
                    rx.cond(
                        ATSState.has_ats_result,
                        results_panel(),
                        ats_initial_view,
                    ),
                ),
                width=rx.breakpoints(initial="100%", lg="68%"),
                min_width="0",
                padding_left=rx.breakpoints(initial="0", lg=t.SPACE_6),
                padding_top=rx.breakpoints(initial=t.SPACE_4, lg="0"),
                flex_shrink="1",
            ),
            align_items="start",
            flex_direction=rx.breakpoints(initial="column", lg="row"),
            width="100%",
            min_width="0",
            max_width=t.CONTENT_MAX_W,
            margin="0 auto",
        )
    )
