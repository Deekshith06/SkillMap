"""analyze.py — Single resume analysis page."""
import reflex as rx
from skillmap.state.analyze_state import AnalyzeState
from skillmap.components.file_upload import file_drop_zone
from skillmap.components.skill_badge import skill_badge, skill_pill_primary, skill_pill_muted
from skillmap.components.charts import radar_chart
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
                padding=t.SPACE_3, background_color="rgba(255, 119, 28, 0.05)", border=f"1px solid rgba(255, 119, 28, 0.2)", border_radius=t.RADIUS_MD, width="100%", align_items="center", height="64px"
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
                    padding=t.SPACE_3, background_color="rgba(255, 119, 28, 0.05)", border=f"1px solid rgba(255, 119, 28, 0.2)", border_radius=t.RADIUS_MD, width="100%", align_items="center", height="64px"
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

        # Actions
        rx.hstack(
            rx.button(
                rx.text(rx.cond(AnalyzeState.analyzing, "Analyzing...", "Analyze Resume")),
                on_click=AnalyzeState.predict_cluster,
                disabled=rx.cond(AnalyzeState.resume_text.strip() == "", True, AnalyzeState.analyzing),
                **t.btn_primary(
                    flex="1", padding="0.8rem", font_size="1rem",
                    background_color=rx.cond(AnalyzeState.resume_text.strip() == "", "rgba(255,119,28,0.5)", t.PRIMARY),
                    _disabled={"opacity": "1", "cursor": "not-allowed"}
                ),
            ),
            rx.button(
                rx.text("Reset"),
                on_click=AnalyzeState.reset_analyze,
                **t.btn_ghost(flex="0 0 auto", padding="0.8rem 1.5rem", border=f"1px solid {t.BORDER}")
            ),
            spacing="3", margin_top=t.SPACE_6, width="100%", align_items="center",
        ),

        # Error
        rx.cond(
            AnalyzeState.analyze_error != "",
            rx.box(
                rx.text(AnalyzeState.analyze_error, color=t.ERROR, font_size="0.9rem"),
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
    analyze_skeleton = rx.vstack(
        # Skeleton Card 1
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.heading("Cluster Result", size="5", font_family=t.FONT_HEADING, color=t.DARK),
                    rx.text("AI ML Data Analyst", color=t.SECONDARY, font_size="0.9rem", opacity="0"),
                    spacing="2", align_items="start",
                ),
                rx.spacer(),
                rx.box(
                    rx.text("0%", font_family=t.FONT_HEADING, font_size="2rem", font_weight="800", color=t.SECONDARY),
                    rx.text("Match Score", font_size="0.7rem", text_transform="uppercase", color=t.SECONDARY),
                    display="flex", flex_direction="column", align_items="center", justify_content="center",
                    width="100px", height="100px", border_radius="50%", border=f"4px solid {t.SECONDARY_LIGHT}", flex_shrink="0",
                ),
                justify="between", align="start", width="100%", margin_bottom=t.SPACE_6,
            ),
            rx.box(
                rx.text("Detected Skills", font_size="0.9rem", font_weight="700", color=t.DARK, margin_bottom=t.SPACE_3),
                rx.box(height="32px", width="80%", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_MD),
                width="100%",
            ),
            **t.card_style(), margin_bottom="1rem", width="100%", min_height="280px"
        ),

        # Skeleton Card 2
        rx.box(
            rx.text("Skill Dimensions", font_size="1rem", font_weight="700", color=t.DARK, margin_bottom=t.SPACE_6),
            rx.hstack(
                rx.box(height="280px", width="280px", background_color=t.SECONDARY_LIGHT, border_radius="50%", flex="1"),
                rx.vstack(
                    rx.box(height="24px", width="100%", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_PILL),
                    rx.box(height="24px", width="80%", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_PILL),
                    rx.box(height="24px", width="90%", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_PILL),
                    rx.box(height="24px", width="70%", background_color=t.SECONDARY_LIGHT, border_radius=t.RADIUS_PILL),
                    width="100%", spacing="4", flex="1", justify="center"
                ),
                width="100%", spacing="6", align_items="center",
            ),
            **t.card_style(), margin_bottom="1rem", width="100%", min_height="380px"
        ),

        # Skeleton Card 3
        rx.box(
            rx.text("Similar Resumes", font_size="1rem", font_weight="700", color=t.DARK, margin_bottom=t.SPACE_6),
            rx.vstack(
                rx.box(height="85px", width="100%", background_color=t.SURFACE_HOVER, border=f"1px solid {t.BORDER}", border_radius=t.RADIUS_MD),
                rx.box(height="85px", width="100%", background_color=t.SURFACE_HOVER, border=f"1px solid {t.BORDER}", border_radius=t.RADIUS_MD),
                rx.box(height="85px", width="100%", background_color=t.SURFACE_HOVER, border=f"1px solid {t.BORDER}", border_radius=t.RADIUS_MD),
                width="100%", spacing="3"
            ),
            **t.card_style(), width="100%", min_height="380px"
        ),
        width="100%", opacity="0.5", pointer_events="none",
    )

    analyze_overlay = rx.box(
        analyze_skeleton,
        rx.box(
            rx.vstack(
                rx.box(rx.icon("scan-face", color=t.PRIMARY, size=24), background_color=t.PRIMARY_LIGHT, padding="12px", border_radius="12px", margin_bottom="12px"),
                rx.heading("Analysis Pending", size="5", color=t.DARK),
                rx.text("Upload your resume and enter a JD to generate an AI-powered match.", color=t.SECONDARY, text_align="center", max_width="250px"),
                align_items="center", background_color=t.SURFACE, padding=t.SPACE_8, border_radius=t.RADIUS_LG, box_shadow=t.SHADOW_LG,
            ),
            position="absolute", top="0", left="0", right="0", bottom="0", display="flex", align_items="center", justify_content="center", z_index="10"
        ),
        position="relative", width="100%"
    )

    return rx.box(
        rx.cond(
            AnalyzeState.has_result,
            rx.vstack(
                # Card 1: Header + Detected Skills
                rx.box(
                    rx.hstack(
                        rx.vstack(
                            rx.heading(AnalyzeState.result_domain, size="5", font_family=t.FONT_HEADING, color=t.DARK),
                            rx.text(AnalyzeState.result_cluster_name, color=t.SECONDARY, font_size="0.9rem"),
                            spacing="2", align_items="start",
                        ),
                        rx.spacer(),
                        rx.cond(
                            AnalyzeState.result_has_match,
                            rx.box(
                                rx.text(AnalyzeState.match_score_str, font_family=t.FONT_HEADING, font_size="2rem", font_weight="800", color=t.PRIMARY),
                                rx.text("Match Score", font_size="0.7rem", text_transform="uppercase", color=t.SECONDARY),
                                display="flex", flex_direction="column", align_items="center", justify_content="center",
                                width="100px", height="100px", border_radius="50%", border=f"4px solid {t.PRIMARY}", flex_shrink="0",
                            ),
                            rx.box(
                                rx.text(AnalyzeState.result_confidence_pct, font_family=t.FONT_HEADING, font_size="2rem", font_weight="800", color=t.PRIMARY),
                                rx.text("Confidence", font_size="0.7rem", text_transform="uppercase", color=t.SECONDARY),
                                display="flex", flex_direction="column", align_items="center", justify_content="center",
                                width="100px", height="100px", border_radius="50%", border=f"4px solid {t.PRIMARY}", flex_shrink="0",
                            )
                        ),
                        justify="between", align="start", width="100%", margin_bottom=t.SPACE_6,
                    ),
                    rx.box(
                        rx.text("Detected Skills", font_size="0.9rem", font_weight="700", color=t.DARK, margin_bottom=t.SPACE_3),
                        rx.flex(rx.foreach(AnalyzeState.result_top_skills, skill_pill_primary), flex_wrap="wrap", gap=t.SPACE_2),
                        width="100%",
                    ),
                    **t.card_style(), margin_bottom="1rem", width="100%", min_height="280px"
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

                # Card: JD Match Details (New feature)
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
                                rx.text("✗ Missing Keywords", font_weight="700", font_size="0.85rem", color=t.DARK),
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
                width="100%",
            ),
            analyze_overlay,
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
