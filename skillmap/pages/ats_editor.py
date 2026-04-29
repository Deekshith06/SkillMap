"""ats_editor.py — Upload → Score → Suggestions ATS page."""
import reflex as rx
from skillmap.state.ats_state import ATSState
from skillmap.components.skill_badge import skill_pill_primary, skill_pill_muted
from skillmap.styles import theme as t


# ── Sub-score bar ─────────────────────────────────────────────────────────────

def sub_score_bar(label: str, score) -> rx.Component:
    """Horizontal progress bar for a sub-category score."""
    return rx.vstack(
        rx.hstack(
            rx.text(label, font_size="0.85rem", font_weight="600", color=t.DARK),
            rx.spacer(),
            rx.text(
                score.to_string() + "%",
                font_size="0.85rem", font_weight="700", color=t.PRIMARY,
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
            width="100%", height="6px",
            background_color=t.SECONDARY_LIGHT,
            border_radius=t.RADIUS_PILL,
            overflow="hidden",
        ),
        spacing="1", width="100%",
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
                padding="2px 8px", border_radius=t.RADIUS_PILL,
                font_size="0.7rem", font_weight="800",
            ),
            rx.text(s.title, font_weight="700", color=t.DARK, font_size="0.9rem"),
            spacing="2", align="center",
        ),
        rx.text(s.detail, font_size="0.85rem", color=t.SECONDARY, margin_top=t.SPACE_1),
        background_color=t.SURFACE_HOVER,
        border_radius=t.RADIUS_MD, padding=t.SPACE_3, margin_bottom=t.SPACE_2,
        border_left=f"3px solid {t.PRIMARY}",
    )


# ── Upload card (Match Analyze Layout) ────────────────────────────────────────

def upload_card() -> rx.Component:
    return rx.box(
        rx.heading("ATS Optimizer", size="6", font_family=t.FONT_HEADING, color=t.DARK, margin_bottom="0.5rem"),
        rx.text("Score and optimize your resume against specific job requirements.", color=t.SECONDARY, font_size="0.9rem", margin_bottom=t.SPACE_6),

        rx.text("Resume", font_size="0.85rem", font_weight="700", color=t.DARK, margin_bottom="0.5rem"),
        rx.cond(
            ATSState.ats_filename != "",
            rx.hstack(
                rx.icon("file-check-2", size=18, color=t.SUCCESS),
                rx.text(ATSState.ats_filename, font_size="0.85rem", font_weight="600", color=t.DARK),
                rx.spacer(),
                rx.button(rx.icon("x", size=14), on_click=ATSState.clear_resume_file, background="transparent", color=t.SECONDARY, cursor="pointer", padding="0"),
                padding=t.SPACE_3, background_color="rgba(107, 143, 113, 0.05)", border=f"1px solid rgba(107, 143, 113, 0.2)", border_radius=t.RADIUS_MD, width="100%", align_items="center", height="64px"
            ),
            rx.upload(
                rx.hstack(
                    rx.icon("upload", size=18, color=t.PRIMARY),
                    rx.text("Click or drop resume file here", font_weight="600", color=t.DARK, font_size="0.85rem"),
                    spacing="2", align="center", justify="center", width="100%"
                ),
                id="ats_upload",
                on_drop=ATSState.handle_ats_upload(rx.upload_files(upload_id="ats_upload")),
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
        rx.box(height=t.SPACE_6),

        rx.text("Job Description (Optional)", font_size="0.85rem", font_weight="700", color=t.DARK, margin_bottom="0.5rem"),
        # Tabs for JD
        rx.hstack(
            rx.box(
                rx.hstack(rx.icon("file-text", size=14), rx.text("Paste Text"), spacing="2", align="center"),
                padding="0.5rem 0", flex="1", cursor="pointer", font_weight="600", font_size="0.85rem", text_align="center",
                color=rx.cond(ATSState.jd_mode == "text", t.PRIMARY, t.SECONDARY),
                border_bottom=rx.cond(ATSState.jd_mode == "text", f"2px solid {t.PRIMARY}", "2px solid transparent"),
                on_click=ATSState.set_jd_mode("text"),
            ),
            rx.box(
                rx.hstack(rx.icon("upload", size=14), rx.text("Upload File"), spacing="2", align="center"),
                padding="0.5rem 0", flex="1", cursor="pointer", font_weight="600", font_size="0.85rem", text_align="center",
                color=rx.cond(ATSState.jd_mode == "file", t.PRIMARY, t.SECONDARY),
                border_bottom=rx.cond(ATSState.jd_mode == "file", f"2px solid {t.PRIMARY}", "2px solid transparent"),
                on_click=ATSState.set_jd_mode("file"),
            ),
            width="100%", border_bottom=f"1px solid {t.SURFACE_BORDER}", margin_bottom=t.SPACE_4,
        ),
        
        rx.cond(
            ATSState.jd_mode == "text",
            rx.text_area(
                placeholder="Paste job description...",
                value=ATSState.jd_text, on_change=ATSState.set_jd_text,
                height="100px", width="100%", border=f"1px solid {t.SURFACE_BORDER}",
                border_radius=t.RADIUS_MD, padding=t.SPACE_3, font_family=t.FONT_BODY,
            ),
            rx.cond(
                ATSState.jd_filename != "",
                rx.hstack(
                    rx.icon("file-text", size=18, color=t.PRIMARY),
                    rx.text(ATSState.jd_filename, font_size="0.85rem", font_weight="600", color=t.DARK),
                    rx.spacer(),
                    rx.button(rx.icon("x", size=14), on_click=ATSState.clear_jd_file, background="transparent", color=t.SECONDARY, cursor="pointer", padding="0"),
                    padding=t.SPACE_3, background_color="rgba(255, 119, 28, 0.05)", border=f"1px solid rgba(255, 119, 28, 0.2)", border_radius=t.RADIUS_MD, width="100%", align_items="center", height="64px"
                ),
                rx.upload(
                    rx.hstack(
                        rx.icon("upload", size=18, color=t.PRIMARY),
                        rx.text("Click or drop JD file here", font_weight="600", color=t.DARK, font_size="0.85rem"),
                        spacing="2", align="center", justify="center", width="100%"
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
                    flex="1", padding="0.8rem", font_size="1rem",
                    background_color=rx.cond(ATSState.ats_filename == "", "rgba(255,119,28,0.5)", t.PRIMARY),
                    _disabled={"opacity": "1", "cursor": "not-allowed"}
                ),
            ),
            rx.button(
                rx.text("Reset"),
                on_click=ATSState.reset_ats,
                **t.btn_ghost(flex="0 0 auto", padding="0.8rem 1.5rem", border=f"1px solid {t.BORDER}")
            ),
            spacing="3", margin_top=t.SPACE_6, width="100%", align_items="center",
        ),

        # Error
        rx.cond(
            ATSState.ats_error != "",
            rx.box(
                rx.text(ATSState.ats_error, color=t.ERROR, font_size="0.9rem"),
                background_color=t.ERROR_LIGHT,
                border_radius=t.RADIUS_MD,
                padding=t.SPACE_3,
                margin_top=t.SPACE_4,
            ),
            rx.box(),
        ),

        background_color=t.SURFACE,
        border_radius=t.RADIUS_LG,
        padding=t.SPACE_6,
        box_shadow=t.SHADOW_SM,
        width="100%",
    )


# ── Results panel (shown after scoring) ──────────────────────────────────────

def results_panel() -> rx.Component:
    return rx.vstack(
        # Top 3 Metrics Row
        rx.hstack(
            rx.box(
                rx.text("ATS Score", font_size="0.85rem", font_weight="600", color=t.SECONDARY),
                rx.text(ATSState.ats_total_score.to_string() + "%", font_size="1.8rem", font_family=t.FONT_HEADING, font_weight="800", color=t.PRIMARY, line_height="1.2"),
                **t.card_style(), flex="1",
            ),
            rx.box(
                rx.text("Keywords", font_size="0.85rem", font_weight="600", color=t.SECONDARY),
                rx.text(ATSState.cat_keywords_pct.to_string() + "%", font_size="1.8rem", font_family=t.FONT_HEADING, font_weight="800", color=t.DARK, line_height="1.2"),
                **t.card_style(), flex="1",
            ),
            rx.box(
                rx.text("Formatting", font_size="0.85rem", font_weight="600", color=t.SECONDARY),
                rx.text(ATSState.cat_formatting_pct.to_string() + "%", font_size="1.8rem", font_family=t.FONT_HEADING, font_weight="800", color=t.DARK, line_height="1.2"),
                **t.card_style(), flex="1",
            ),
            spacing="4", width="100%", margin_bottom="1rem",
        ),

        # Sub-scores
        rx.box(
            rx.vstack(
                rx.text("Score Breakdown", font_weight="700", font_size="0.95rem", color=t.DARK),
                sub_score_bar("Keywords", ATSState.cat_keywords),
                sub_score_bar("Formatting", ATSState.cat_formatting),
                sub_score_bar("Contact Info", ATSState.cat_contact),
                sub_score_bar("Structure", ATSState.cat_structure),
                sub_score_bar("Achievements", ATSState.cat_achievements),
                sub_score_bar("Action Verbs", ATSState.cat_action_verbs),
                sub_score_bar("Length", ATSState.cat_length),
                spacing="4", width="100%",
            ),
            **t.card_style(), margin_bottom="1rem", width="100%",
        ),

        # Keyword matches / gaps
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.text("✓ Matched Keywords", font_weight="700", font_size="0.85rem", color=t.SUCCESS),
                    rx.flex(
                        rx.foreach(ATSState.ats_matched_kw, skill_pill_primary),
                        flex_wrap="wrap", gap="6px",
                    ),
                    align_items="start", spacing="2",
                ),
                rx.vstack(
                    rx.text("✗ Missing Keywords", font_weight="700", font_size="0.85rem", color=t.ERROR),
                    rx.flex(
                        rx.foreach(ATSState.ats_missing_kw, skill_pill_muted),
                        flex_wrap="wrap", gap="6px",
                    ),
                    align_items="start", spacing="2",
                ),
                spacing="6", align_items="start", width="100%",
            ),
            **t.card_style(), margin_bottom="1rem", width="100%",
        ),

        # Suggestions
        rx.box(
            rx.vstack(
                rx.text("Suggestions", font_weight="700", font_size="0.95rem", color=t.DARK),
                rx.foreach(ATSState.ats_suggestions, suggestion_card),
                spacing="2", width="100%",
            ),
            **t.card_style(), width="100%",
        ),

        spacing="0", width="100%",
    )


# ── Page ──────────────────────────────────────────────────────────────────────

def ats_editor_page() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                upload_card(),
                width="32%",
                min_width="380px",
                flex_shrink="0",
            ),
            rx.box(
                rx.cond(
                    ATSState.has_ats_result,
                    rx.box(
                        results_panel(),
                        width="100%",
                    ),
                    rx.box(
                        # Empty state / Analysis Pending overlay
                        rx.vstack(
                            # Skeleton Top 3 Metrics
                            rx.hstack(
                                rx.box(rx.text("ATS Score", font_size="0.85rem", font_weight="600", color=t.SECONDARY), rx.text("0%", font_size="1.8rem", font_family=t.FONT_HEADING, font_weight="800", color=t.SECONDARY_LIGHT, line_height="1.2"), **t.card_style(), flex="1"),
                                rx.box(rx.text("Keywords", font_size="0.85rem", font_weight="600", color=t.SECONDARY), rx.text("0%", font_size="1.8rem", font_family=t.FONT_HEADING, font_weight="800", color=t.SECONDARY_LIGHT, line_height="1.2"), **t.card_style(), flex="1"),
                                rx.box(rx.text("Formatting", font_size="0.85rem", font_weight="600", color=t.SECONDARY), rx.text("0%", font_size="1.8rem", font_family=t.FONT_HEADING, font_weight="800", color=t.SECONDARY_LIGHT, line_height="1.2"), **t.card_style(), flex="1"),
                                spacing="4", width="100%", margin_bottom="1rem"
                            ),
                            # Skeleton Score Breakdown
                            rx.box(
                                rx.vstack(
                                    rx.text("Score Breakdown", font_weight="700", font_size="0.95rem", color=t.DARK),
                                    rx.box(height="22px", width="100%", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_PILL),
                                    rx.box(height="22px", width="100%", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_PILL),
                                    rx.box(height="22px", width="100%", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_PILL),
                                    rx.box(height="22px", width="100%", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_PILL),
                                    rx.box(height="22px", width="100%", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_PILL),
                                    rx.box(height="22px", width="100%", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_PILL),
                                    rx.box(height="22px", width="100%", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_PILL),
                                    spacing="4", width="100%"
                                ),
                                **t.card_style(), margin_bottom="1rem", width="100%"
                            ),
                            # Skeleton Keywords Matches
                            rx.box(
                                rx.hstack(
                                    rx.vstack(
                                        rx.text("✓ Matched Keywords", font_weight="700", font_size="0.85rem", color=t.DARK),
                                        rx.box(height="60px", width="100%", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_MD),
                                        align_items="start", spacing="2", width="100%"
                                    ),
                                    rx.vstack(
                                        rx.text("✗ Missing Keywords", font_weight="700", font_size="0.85rem", color=t.DARK),
                                        rx.box(height="60px", width="100%", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_MD),
                                        align_items="start", spacing="2", width="100%"
                                    ),
                                    spacing="6", align_items="start", width="100%"
                                ),
                                **t.card_style(), margin_bottom="1rem", width="100%"
                            ),
                            # Skeleton Suggestions
                            rx.box(
                                rx.vstack(
                                    rx.text("Suggestions", font_weight="700", font_size="0.95rem", color=t.DARK),
                                    rx.box(height="80px", width="100%", background_color=t.SURFACE_HOVER, border=f"1px solid {t.BORDER}", border_radius=t.RADIUS_MD),
                                    rx.box(height="80px", width="100%", background_color=t.SURFACE_HOVER, border=f"1px solid {t.BORDER}", border_radius=t.RADIUS_MD),
                                    spacing="2", width="100%"
                                ),
                                **t.card_style(), width="100%"
                            ),
                            width="100%", opacity="0.4", pointer_events="none",
                        ),
                        # Modal overlay
                        rx.box(
                            rx.vstack(
                                rx.box(rx.icon("file-search", color=t.PRIMARY, size=24), background_color=t.PRIMARY_LIGHT, padding="12px", border_radius="12px", margin_bottom="12px"),
                                rx.heading("Analysis Pending", size="5", color=t.DARK),
                                rx.text("Upload your resume and enter a JD to generate an ATS optimization report.", color=t.SECONDARY, text_align="center", max_width="250px"),
                                align_items="center",
                                background_color=t.SURFACE,
                                padding=t.SPACE_8,
                                border_radius=t.RADIUS_LG,
                                box_shadow=t.SHADOW_LG,
                            ),
                            position="absolute", top="0", left="0", right="0", bottom="0",
                            display="flex", align_items="center", justify_content="center",
                            z_index="10"
                        ),
                        position="relative", width="100%"
                    ),
                ),
                width="68%",
                padding_left=t.SPACE_6,
                flex_shrink="1",
            ),
            align_items="start",
            width="100%",
            max_width=t.CONTENT_MAX_W,
            margin="0 auto",
        )
    )
