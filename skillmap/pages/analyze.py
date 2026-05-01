"""analyze.py — Single resume analysis page."""
import reflex as rx
from skillmap.state.analyze_state import AnalyzeState
from skillmap.components.file_upload import file_drop_zone
from skillmap.components.skill_badge import skill_badge, skill_pill_primary, skill_pill_muted
from skillmap.components.charts import radar_chart
from skillmap.components.ui import skeleton_bar, error_alert
from skillmap.styles import theme as t





def input_panel() -> rx.Component:
    return rx.box(
        rx.heading("Analyze Resume", size="6", font_family=t.FONT_HEADING, color=t.DARK, margin_bottom="0.5rem"),
        rx.text("Upload a resume and optionally add a job description for AI-powered matching.", color=t.SECONDARY, font_size="0.9rem", margin_bottom=t.SPACE_6),

        rx.text("Resume", font_size="0.85rem", font_weight="700", color=t.DARK, margin_bottom="0.5rem"),
        rx.cond(
            AnalyzeState.resume_filename != "",
            rx.hstack(
                rx.icon("file-text", size=18, color=t.PRIMARY),
                rx.text(AnalyzeState.resume_filename, font_size="0.85rem", font_weight="600", color=t.DARK),
                rx.spacer(),
                rx.button(rx.icon("x", size=14), on_click=AnalyzeState.clear_resume_file, background="transparent", color=t.SECONDARY, cursor="pointer", padding="0"),
                padding=t.SPACE_3, background_color=t.PRIMARY_LIGHT, border=f"1px solid {t.PRIMARY}", border_radius=t.RADIUS_MD, width="100%", align_items="center", height="64px"
            ),
            rx.upload(
                rx.hstack(
                    rx.icon("upload", size=18, color=t.PRIMARY),
                    rx.text("Click or drop resume file here", font_weight="600", color=t.DARK, font_size="0.85rem"),
                    spacing="2", align="center", justify="center", width="100%"
                ),
                id="analyze_upload",
                on_drop=AnalyzeState.handle_upload(rx.upload_files(upload_id="analyze_upload")),
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
                color=rx.cond(AnalyzeState.jd_mode == "text", t.PRIMARY, t.SECONDARY),
                border_bottom=rx.cond(AnalyzeState.jd_mode == "text", f"2px solid {t.PRIMARY}", "2px solid transparent"),
                on_click=AnalyzeState.set_jd_mode("text"),
            ),
            rx.box(
                rx.hstack(rx.icon("upload", size=14), rx.text("Upload File"), spacing="2", align="center"),
                padding="0.5rem 0", flex="1", cursor="pointer", font_weight="600", font_size="0.85rem", text_align="center",
                color=rx.cond(AnalyzeState.jd_mode == "file", t.PRIMARY, t.SECONDARY),
                border_bottom=rx.cond(AnalyzeState.jd_mode == "file", f"2px solid {t.PRIMARY}", "2px solid transparent"),
                on_click=AnalyzeState.set_jd_mode("file"),
            ),
            width="100%", border_bottom=f"1px solid {t.SURFACE_BORDER}", margin_bottom=t.SPACE_4,
        ),
        
        rx.cond(
            AnalyzeState.jd_mode == "text",
            rx.text_area(
                placeholder="Paste job description...",
                value=AnalyzeState.jd_text, on_change=AnalyzeState.set_jd_text,
                height="100px", width="100%", border=f"1px solid {t.SURFACE_BORDER}",
                border_radius=t.RADIUS_MD, padding=t.SPACE_3, font_family=t.FONT_BODY,
            ),
            rx.cond(
                AnalyzeState.jd_filename != "",
                rx.hstack(
                    rx.icon("file-text", size=18, color=t.PRIMARY),
                    rx.text(AnalyzeState.jd_filename, font_size="0.85rem", font_weight="600", color=t.DARK),
                    rx.spacer(),
                    rx.button(rx.icon("x", size=14), on_click=AnalyzeState.clear_jd_file, background="transparent", color=t.SECONDARY, cursor="pointer", padding="0"),
                    padding=t.SPACE_3, background_color=t.PRIMARY_LIGHT, border=f"1px solid {t.PRIMARY}", border_radius=t.RADIUS_MD, width="100%", align_items="center", height="64px"
                ),
                rx.upload(
                    rx.hstack(
                        rx.icon("upload", size=18, color=t.PRIMARY),
                        rx.text("Click or drop JD file here", font_weight="600", color=t.DARK, font_size="0.85rem"),
                        spacing="2", align="center", justify="center", width="100%"
                    ),
                    id="analyze_jd_upload",
                    on_drop=AnalyzeState.handle_jd_upload(rx.upload_files(upload_id="analyze_jd_upload")),
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

        # Error
        rx.cond(
            AnalyzeState.analyze_error != "",
            error_alert(AnalyzeState.analyze_error),
            rx.box(),
        ),

        background_color=t.SURFACE,
        border_radius=t.RADIUS_LG,
        padding=t.SPACE_6,
        box_shadow=t.SHADOW_SM,
        width="100%",
    )


def skill_progress_bar(item: dict) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(item["domain"], font_size="0.85rem", font_weight="600", color=t.DARK),
            rx.spacer(),
            rx.text(item["confidence"].to(str) + "%", font_size="0.85rem", font_weight="700", color=t.PRIMARY),
            width="100%",
        ),
        rx.box(
            rx.box(height="100%", width=item["confidence"].to(str) + "%", background_color=t.PRIMARY, border_radius=t.RADIUS_PILL),
            width="100%", height="6px", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_PILL, overflow="hidden",
        ),
        spacing="1", width="100%", margin_bottom=t.SPACE_2,
    )

def result_panel() -> rx.Component:
    def skeleton_metric_box():
        return rx.box(
            rx.vstack(
                rx.text("Metric", font_size="0.75rem", font_weight="600", color=t.ARCH_NEUTRAL_500),
                rx.heading("0%", size="7", color=t.ARCH_NEUTRAL_300),
                spacing="1", align_items="start"
            ),
            **t.card_style(), flex="1", opacity="0.6"
        )

    loading_skeleton_view = rx.vstack(
        # 1. Top Row: Metrics
        rx.hstack(
            skeleton_metric_box(),
            skeleton_metric_box(),
            skeleton_metric_box(),
            width="100%", spacing="4", margin_bottom="1rem"
        ),
        # 2. Skeleton Unified Domain Box
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.box(width="34px", height="34px", background_color=t.SECONDARY_LIGHT, border_radius="8px", animation="pulse 1.5s ease-in-out infinite"),
                        rx.vstack(
                            skeleton_bar(width="100px", height="12px"),
                            skeleton_bar(width="200px", height="24px"),
                            spacing="1", align_items="start"
                        ),
                        spacing="3", align_items="center"
                    ),
                    skeleton_bar(width="180px", height="16px", margin_top="12px"),
                    skeleton_bar(width="220px", height="14px", margin_top="8px"),
                    align_items="start", flex="1"
                ),
                rx.vstack(
                    rx.text("Primary Insight", font_size="0.85rem", font_weight="700", color=t.ARCH_NEUTRAL_300, text_align="center", width="100%"),
                    rx.box(width="56px", height="56px", background_color=t.SECONDARY_LIGHT, border_radius="12px", animation="pulse 1.5s ease-in-out infinite", margin_top="4px"),
                    spacing="1", align_items="center", min_width="120px"
                ),
                align_items="center", width="100%"
            ),
            **t.card_style(), margin_bottom="1rem", opacity="0.6"
        ),
        # 3. Skeleton Detected Skills
        rx.box(
            rx.vstack(
                rx.text("Detected Skills", font_size="0.9rem", font_weight="700", color=t.ARCH_NEUTRAL_300, margin_bottom="12px"),
                rx.flex(
                    rx.foreach(list(range(12)), lambda _: skeleton_bar(width="80px", height="28px")),
                    flex_wrap="wrap", gap="8px"
                ),
                width="100%", align_items="start"
            ),
            **t.card_style(), margin_bottom="1rem", opacity="0.6"
        ),
        # 4. Skeleton Skill Dimensions
        rx.box(
            rx.vstack(
                rx.text("Skill Dimensions", font_size="0.9rem", font_weight="700", color=t.ARCH_NEUTRAL_300, margin_bottom="12px"),
                rx.hstack(
                    rx.box(width="240px", height="240px", background_color=t.SECONDARY_LIGHT, border_radius="50%", animation="pulse 1.5s ease-in-out infinite", flex_shrink="0"),
                    rx.vstack(
                        rx.foreach(list(range(5)), lambda _: rx.vstack(
                            rx.hstack(skeleton_bar(width="100px", height="8px"), rx.spacer(), skeleton_bar(width="30px", height="8px"), width="100%"),
                            skeleton_bar(width="100%", height="6px"),
                            width="100%", spacing="2"
                        )),
                        flex="1", width="100%", spacing="4"
                    ),
                    width="100%", spacing="8", align_items="center"
                ),
                width="100%", align_items="start"
            ),
            **t.card_style(), margin_bottom="1rem", opacity="0.6"
        ),
        # 5. Similar Resumes Skeleton
        rx.box(
            rx.vstack(
                rx.text("Similar Resumes", font_size="0.9rem", font_weight="700", color=t.ARCH_NEUTRAL_300, margin_bottom="12px"),
                rx.foreach(list(range(2)), lambda _: rx.box(
                    skeleton_bar(width="140px", height="12px", margin_bottom="8px"),
                    skeleton_bar(width="100%", height="10px"),
                    skeleton_bar(width="85%", height="10px", margin_top="4px"),
                    padding="16px", border_radius="8px", border=f"1px solid {t.ARCH_NEUTRAL_300}", width="100%", margin_bottom="8px"
                )),
                spacing="2", width="100%"
            ),
            **t.card_style(), width="100%", opacity="0.6"
        ),
        width="100%", spacing="0"
    )

    initial_overlay = rx.box(
        # Background Skeleton (Blurred)
        rx.box(
            loading_skeleton_view,
            width="100%", height="100%",
            opacity="0.5", filter="blur(1px)"
        ),
        # Center Card (Absolute Overlay)
        rx.center(
            rx.vstack(
                rx.box(
                    rx.icon("scan-face", color=t.PRIMARY, size=32),
                    background_color=t.PRIMARY_LIGHT, padding="20px", border_radius="16px",
                    margin_bottom="12px"
                ),
                rx.heading("Ready for Analysis", size="6", font_weight="800", color=t.DARK),
                rx.text(
                    "Upload a resume to extract skills and find matching job domains.",
                    color=t.SECONDARY, text_align="center", max_width="320px", font_size="0.95rem",
                    line_height="1.5"
                ),
                align_items="center", background_color=t.SURFACE, padding="40px",
                border_radius=t.RADIUS_LG, box_shadow=t.SHADOW_LG,
                border=f"1px solid {t.BORDER}",
            ),
            position="absolute",
            top="0", left="0",
            width="100%", height="100%",
            z_index="10"
        ),
        position="relative",
        width="100%", height="100%", min_height="800px"
    )

    return rx.box(
        rx.cond(
                AnalyzeState.analyzing,
                loading_skeleton_view,
                rx.cond(
                    AnalyzeState.has_result,
                    rx.vstack(
                    # Top Row: Metrics
                    rx.hstack(
                        rx.box(
                            rx.vstack(
                                rx.text("Match Confidence", font_size="0.75rem", font_weight="700", color=t.SECONDARY, text_transform="uppercase"),
                                rx.heading(AnalyzeState.result_confidence_pct, size="7", color=t.PRIMARY),
                                spacing="1", align_items="start"
                            ),
                            **t.card_style(), flex="1"
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("Skills Detected", font_size="0.75rem", font_weight="700", color=t.SECONDARY, text_transform="uppercase"),
                                rx.heading(AnalyzeState.result_top_skills.length().to(str), size="7", color=t.DARK),
                                spacing="1", align_items="start"
                            ),
                            **t.card_style(), flex="1"
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("Match Quality", font_size="0.75rem", font_weight="700", color=t.SECONDARY, text_transform="uppercase"),
                                rx.heading(rx.cond(AnalyzeState.result_has_match, AnalyzeState.match_score_str + "%", "N/A"), size="7", color=rx.cond(AnalyzeState.result_has_match, t.SUCCESS, t.ARCH_NEUTRAL_300)),
                                spacing="1", align_items="start"
                            ),
                            **t.card_style(), flex="1"
                        ),
                        width="100%", spacing="4", margin_bottom="1rem"
                    ),

                    # Card 1: Unified Domain Display Box
                    rx.box(
                        rx.hstack(
                            rx.vstack(
                                rx.hstack(
                                    rx.box(rx.icon("briefcase", size=18, color=t.PRIMARY), background_color=t.PRIMARY_LIGHT, padding="8px", border_radius="8px"),
                                    rx.vstack(
                                        rx.text("Detected Domain", font_size="0.75rem", font_weight="700", color=t.SECONDARY, text_transform="uppercase", letter_spacing="0.05em"),
                                        rx.heading(AnalyzeState.result_domain, size="6", color=t.DARK, margin_top="-4px"),
                                        spacing="0", align_items="start"
                                    ),
                                    spacing="3", align_items="center"
                                ),
                                rx.text(
                                    AnalyzeState.result_cluster_name,
                                    font_size="0.9rem", color=t.SECONDARY, font_weight="500", margin_top="12px"
                                ),
                                rx.hstack(
                                    rx.icon("gauge", size=14, color=t.SUCCESS),
                                    rx.text("Confidence Score: ", font_size="0.85rem", color=t.SECONDARY),
                                    rx.text(
                                        AnalyzeState.result_confidence_pct,
                                        font_size="0.85rem", font_weight="700", color=t.PRIMARY
                                    ),
                                    spacing="2", align_items="center", margin_top="8px"
                                ),
                                align_items="start", flex="1"
                            ),
                            rx.vstack(
                                rx.text("Primary Insight", font_size="0.75rem", font_weight="700", color=t.SECONDARY, text_align="right", width="100%", text_transform="uppercase", letter_spacing="0.05em"),
                                rx.box(
                                    rx.icon("sparkles", size=24, color=t.PRIMARY),
                                    padding="10px", background_color=t.PRIMARY_LIGHT, border_radius="10px", margin_top="4px"
                                ),
                                spacing="1", align_items="end", min_width="120px"
                            ),
                            align_items="center", width="100%", justify_content="space-between"
                        ),
                        **t.card_style(), margin_bottom="1rem", width="100%",
                        background=f"linear-gradient(135deg, {t.SURFACE} 0%, {t.SURFACE_HOVER} 100%)"
                    ),

                    # Card: Detected Skills (New dedicated box)
                    rx.box(
                        rx.text("Detected Skills", font_size="0.95rem", font_weight="700", color=t.DARK, margin_bottom=t.SPACE_4),
                        rx.flex(rx.foreach(AnalyzeState.result_top_skills, skill_pill_primary), flex_wrap="wrap", gap=t.SPACE_2),
                        **t.card_style(), margin_bottom="1rem", width="100%"
                    ),

                    # Card 2: Skill Dimensions
                    rx.cond(
                        AnalyzeState.radar_data.length() > 2,
                        rx.box(
                            rx.text("Skill Dimensions", font_size="1rem", font_weight="700", color=t.DARK, margin_bottom=t.SPACE_6),
                            rx.hstack(
                                rx.box(radar_chart(AnalyzeState.radar_data, height=280), flex="1"),
                                rx.vstack(rx.foreach(AnalyzeState.radar_data, skill_progress_bar), flex="1", justify="center"),
                                width="100%", spacing="6", align_items="center",
                            ),
                            **t.card_style(), margin_bottom="1rem", width="100%", min_height="380px"
                        ),
                        rx.box(),
                    ),

                    # Card: JD Match Details
                    rx.cond(
                        AnalyzeState.result_has_match,
                        rx.box(
                            rx.text("JD Match Analysis", font_size="1rem", font_weight="700", color=t.DARK, margin_bottom=t.SPACE_6),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("✓ Matched Keywords", font_weight="700", font_size="0.85rem", color=t.DARK),
                                    rx.flex(rx.foreach(AnalyzeState.matched_keywords, skill_pill_primary), flex_wrap="wrap", gap=t.SPACE_2),
                                    align_items="start", spacing="2", width="100%"
                                ),
                                rx.vstack(
                                    rx.text("✗ Skills to Improve", font_weight="700", font_size="0.85rem", color=t.DARK),
                                    rx.flex(rx.foreach(AnalyzeState.missing_keywords, skill_pill_muted), flex_wrap="wrap", gap=t.SPACE_2),
                                    align_items="start", spacing="2", width="100%"
                                ),
                                spacing="6", align_items="start", width="100%"
                            ),
                            **t.card_style(), margin_bottom="1rem", width="100%"
                        ),
                        rx.box()
                    ),

                    # Card 3: Similar Resumes
                    rx.cond(
                        AnalyzeState.result_similar_resumes.length() > 0,
                        rx.box(
                            rx.text("Similar Resumes", font_size="1rem", font_weight="700", color=t.DARK, margin_bottom=t.SPACE_6),
                            rx.vstack(
                                rx.foreach(
                                    AnalyzeState.result_similar_resumes,
                                    lambda r: rx.box(
                                        rx.text(r["category"], font_size="0.9rem", font_weight="700", color=t.PRIMARY, margin_bottom="6px"),
                                        rx.text(r["snippet"].to(str)[:150] + "...", font_size="0.85rem", color=t.DARK, line_height="1.5"),
                                        border=f"1px solid rgba(255, 119, 28, 0.2)",
                                        border_radius=t.RADIUS_MD,
                                        padding=t.SPACE_4, margin_bottom=t.SPACE_3, width="100%",
                                        background_color=t.SURFACE,
                                    )
                                ),
                                width="100%", spacing="0",
                            ),
                            **t.card_style(), width="100%", min_height="380px"
                        ),
                        rx.box(),
                    ),
                    width="100%", align_items="stretch", spacing="0"
                ),
                initial_overlay,
            )
        ),
        width="100%",
    )


def analyze_page() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                input_panel(),
                width="32%",
                min_width="380px",
                flex_shrink="0",
            ),
            rx.box(
                result_panel(),
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
