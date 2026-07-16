"""bulk_upload.py — Batch processing + CSV export UI."""

import reflex as rx

from skillmap.components.file_upload import file_drop_zone
from skillmap.components.skill_badge import skill_pill_primary
from skillmap.components.ui import error_alert
from skillmap.state.bulk_state import BulkState
from skillmap.styles import theme as t


def file_queue_item(f: dict) -> rx.Component:
    return rx.hstack(
        rx.text(
            f["name"],
            font_weight="500",
            flex="1",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
        ),
        rx.box(
            f["status"],
            padding="2px 8px",
            border_radius=t.RADIUS_PILL,
            font_size="0.8rem",
            font_weight="600",
            background_color=t.PRIMARY_LIGHT,
            color=t.PRIMARY,
        ),
        spacing="3",
        padding=f"{t.SPACE_2} {t.SPACE_3}",
        border_bottom=f"1px solid {t.SURFACE_BORDER}",
    )


def results_row(r) -> rx.Component:
    """r is a BulkResultItem PropsBase object."""
    return rx.el.tr(
        rx.el.td(r.index.to_string(), padding=f"{t.SPACE_3} {t.SPACE_4}", font_size="0.9rem"),
        rx.el.td(
            r.filename,
            padding=f"{t.SPACE_3} {t.SPACE_4}",
            font_size="0.9rem",
            max_width="200px",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
        ),
        rx.el.td(
            rx.box(
                r.cluster_name,
                padding="4px 8px",
                background_color=t.PRIMARY_LIGHT,
                color=t.PRIMARY,
                font_weight="700",
                font_size="0.8rem",
                border_radius=t.RADIUS_SM,
            ),
            padding=f"{t.SPACE_3} {t.SPACE_4}",
        ),
        rx.el.td(
            rx.text(
                (r.confidence * 100).to(int).to_string() + "%",
                font_size="0.85rem",
                font_weight="700",
                color=t.PRIMARY,
            ),
            padding=f"{t.SPACE_3} {t.SPACE_4}",
        ),
        rx.el.td(
            rx.flex(
                rx.foreach(r.top_skills, skill_pill_primary),
                flex_wrap="wrap",
                gap="4px",
            ),
            padding=f"{t.SPACE_3} {t.SPACE_4}",
        ),
        _hover={"background_color": t.SURFACE_HOVER},
    )


def bulk_upload_page() -> rx.Component:
    return rx.box(
        # Top Section: Side-by-side Uploads
        rx.flex(
            # Left: Resume Upload
            rx.box(
                rx.heading(
                    "Upload Resumes",
                    size="5",
                    font_family=t.FONT_HEADING,
                    color=t.DARK,
                    margin_bottom="0.5rem",
                ),
                file_drop_zone(
                    BulkState.handle_bulk_upload,
                    label="Click or drop resumes here",
                    sublabel=rx.cond(
                        BulkState.bulk_files.length() > 0,
                        f"{BulkState.bulk_files.length()}/50 files queued",
                        "Max 50 files",
                    ),
                    multiple=True,
                    upload_id="bulk_upload",
                ),
                # File queue
                rx.cond(
                    BulkState.bulk_files.length() > 0,
                    rx.box(
                        rx.hstack(
                            rx.text(
                                f"{BulkState.bulk_files.length()} file(s) queued",
                                font_size="0.9rem",
                                font_weight="600",
                            ),
                            rx.button(
                                rx.icon("trash-2", size=12),
                                rx.text("Clear all"),
                                on_click=BulkState.clear_all,
                                **t.btn_ghost(
                                    padding="0.4rem 1rem", min_height="auto", font_size="0.85rem"
                                ),
                            ),
                            justify="between",
                            align="center",
                            margin_bottom=t.SPACE_3,
                        ),
                        rx.box(
                            rx.foreach(BulkState.bulk_files[:50], file_queue_item),
                            border=f"1px solid {t.SURFACE_BORDER}",
                            border_radius=t.RADIUS_MD,
                            max_height="150px",
                            overflow_y="auto",
                        ),
                        margin_top=t.SPACE_6,
                    ),
                    rx.box(),
                ),
                background_color=t.SURFACE,
                border=f"1px solid {t.SURFACE_BORDER}",
                border_radius=t.RADIUS_LG,
                padding=t.SPACE_6,
                box_shadow=t.SHADOW_SM,
                flex="1",
                width=rx.breakpoints(initial="100%", md="50%"),
            ),
            # Right: JD Upload + Action
            rx.box(
                rx.heading(
                    "Job Description (Optional)",
                    size="5",
                    font_family=t.FONT_HEADING,
                    color=t.DARK,
                    margin_bottom="0.5rem",
                ),
                rx.hstack(
                    rx.box(
                        "Paste",
                        font_size="0.85rem",
                        font_weight="700",
                        border_bottom=f"2px solid {t.DARK}",
                        padding_bottom="4px",
                        flex="1",
                        text_align="center",
                        cursor="pointer",
                    ),
                    rx.box(
                        "Upload",
                        font_size="0.85rem",
                        font_weight="600",
                        color=t.SECONDARY,
                        padding_bottom="4px",
                        flex="1",
                        text_align="center",
                        cursor="pointer",
                    ),
                    width="100%",
                    margin_bottom="1rem",
                ),
                rx.text_area(
                    placeholder="Target skills/JD here...",
                    value=BulkState.jd_text,
                    on_change=BulkState.set_jd_text,
                    height="100px",
                    width="100%",
                    border=f"1px solid {t.SURFACE_BORDER}",
                    border_radius=t.RADIUS_MD,
                    padding=t.SPACE_3,
                    font_size="0.9rem",
                    resize="vertical",
                    background_color=t.SURFACE,
                    color=t.DARK,
                    _placeholder={"color": t.TEXT_MUTED},
                    margin_bottom=t.SPACE_4,
                ),
                rx.button(
                    rx.text(
                        rx.cond(
                            BulkState.bulk_processing,
                            "Processing...",
                            f"Analyze {BulkState.bulk_files.length()} Resumes",
                        )
                    ),
                    on_click=BulkState.process_all,
                    disabled=rx.cond(
                        BulkState.bulk_files.length() == 0, True, BulkState.bulk_processing
                    ),
                    **t.btn_primary(
                        width="100%",
                        padding="0.8rem 1.5rem",
                        font_size="1rem",
                        background_color=rx.cond(
                            BulkState.bulk_files.length() == 0, "rgba(204,69,53,0.5)", t.PRIMARY
                        ),
                        _disabled={"opacity": "1", "cursor": "not-allowed"},
                    ),
                ),
                rx.cond(
                    BulkState.bulk_processing,
                    rx.vstack(
                        rx.box(
                            rx.box(
                                height="100%",
                                width=BulkState.progress_pct.to_string() + "%",
                                background_color=t.PRIMARY,
                                border_radius=t.RADIUS_PILL,
                            ),
                            height="8px",
                            background_color=t.SECONDARY_LIGHT,
                            border_radius=t.RADIUS_PILL,
                            overflow="hidden",
                            width="100%",
                        ),
                        rx.button(
                            rx.icon("x", size=14),
                            "Cancel",
                            on_click=BulkState.cancel_processing,
                            **t.btn_ghost(padding="0.4rem 0.8rem"),
                        ),
                        rx.text(
                            "The demonstration server may take longer after inactivity.",
                            color=t.SECONDARY,
                            font_size="0.8rem",
                        ),
                        margin_top=t.SPACE_4,
                    ),
                    rx.box(),
                ),
                background_color=t.SURFACE,
                border=f"1px solid {t.SURFACE_BORDER}",
                border_radius=t.RADIUS_LG,
                padding=t.SPACE_6,
                box_shadow=t.SHADOW_SM,
                flex="1",
                width=rx.breakpoints(initial="100%", md="50%"),
                display="flex",
                flex_direction="column",
            ),
            spacing="6",
            width="100%",
            margin_bottom=t.SPACE_8,
            align_items="stretch",
            flex_direction=rx.breakpoints(initial="column", md="row"),
        ),
        rx.cond(
            BulkState.bulk_error != "",
            error_alert(BulkState.bulk_error),
            rx.box(),
        ),
        # Results section
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.heading("Results", size="5", font_family=t.FONT_HEADING, color=t.DARK),
                    rx.text(
                        BulkState.filtered_results.length().to_string()
                        + " of "
                        + BulkState.success_results.length().to_string()
                        + " results",
                        color=t.SECONDARY,
                    ),
                    spacing="1",
                    align_items="start",
                ),
                rx.button(
                    rx.icon("download", size=14),
                    rx.text("Export CSV"),
                    on_click=BulkState.download_csv,
                    disabled=BulkState.filtered_results.length() == 0,
                    background_color=t.PRIMARY_LIGHT,
                    color=t.PRIMARY,
                    border_radius=t.RADIUS_PILL,
                    padding="0.6rem 1.25rem",
                    min_height="44px",
                    font_weight="600",
                    font_size="0.95rem",
                    cursor="pointer",
                    display="inline-flex",
                    align_items="center",
                    justify_content="center",
                    gap=t.SPACE_2,
                    transition=f"all {t.TRANSITION_FAST}",
                    border="none",
                    _hover={"background_color": "rgba(204, 69, 53, 0.2)"},
                    _disabled={"opacity": "0.6", "cursor": "not-allowed"},
                ),
                justify="between",
                align="center",
                margin_bottom=t.SPACE_6,
            ),
            # Table
            rx.cond(
                BulkState.page_results.length() > 0,
                rx.vstack(
                    rx.box(
                        rx.el.table(
                            rx.el.thead(
                                rx.el.tr(
                                    rx.el.th(
                                        "#",
                                        padding=f"{t.SPACE_3} {t.SPACE_4}",
                                        text_align="left",
                                        font_weight="600",
                                        color=t.SECONDARY,
                                        font_size="0.9rem",
                                    ),
                                    rx.el.th(
                                        "Filename",
                                        padding=f"{t.SPACE_3} {t.SPACE_4}",
                                        text_align="left",
                                        font_weight="600",
                                        color=t.SECONDARY,
                                        font_size="0.9rem",
                                    ),
                                    rx.el.th(
                                        "Cluster",
                                        padding=f"{t.SPACE_3} {t.SPACE_4}",
                                        text_align="left",
                                        font_weight="600",
                                        color=t.SECONDARY,
                                        font_size="0.9rem",
                                    ),
                                    rx.el.th(
                                        "Confidence",
                                        padding=f"{t.SPACE_3} {t.SPACE_4}",
                                        text_align="left",
                                        font_weight="600",
                                        color=t.SECONDARY,
                                        font_size="0.9rem",
                                    ),
                                    rx.el.th(
                                        "Top Skills",
                                        padding=f"{t.SPACE_3} {t.SPACE_4}",
                                        text_align="left",
                                        font_weight="600",
                                        color=t.SECONDARY,
                                        font_size="0.9rem",
                                    ),
                                    background_color=t.SURFACE_HOVER,
                                )
                            ),
                            rx.el.tbody(rx.foreach(BulkState.page_results, results_row)),
                            width="100%",
                            border_collapse="collapse",
                            font_size="0.9rem",
                        ),
                        overflow_x="auto",
                        border=f"1px solid {t.SURFACE_BORDER}",
                        border_radius=t.RADIUS_MD,
                        margin_bottom=t.SPACE_6,
                    ),
                    rx.hstack(
                        rx.button(
                            "←",
                            on_click=BulkState.prev_page,
                            disabled=BulkState.page <= 1,
                            background="none",
                            color=t.SECONDARY,
                            cursor="pointer",
                            font_size="1.2rem",
                            _disabled={"opacity": "0.4"},
                        ),
                        rx.text(
                            "Page "
                            + BulkState.page.to_string()
                            + " of "
                            + BulkState.total_pages.to_string(),
                            font_weight="600",
                            font_size="0.9rem",
                        ),
                        rx.button(
                            "→",
                            on_click=BulkState.next_page,
                            disabled=BulkState.page >= BulkState.total_pages,
                            background="none",
                            color=t.SECONDARY,
                            cursor="pointer",
                            font_size="1.2rem",
                            _disabled={"opacity": "0.4"},
                        ),
                        spacing="4",
                        justify="center",
                    ),
                    width="100%",
                ),
                rx.vstack(
                    rx.center(
                        rx.icon("table-properties", size=22, color=t.PRIMARY),
                        width="48px",
                        height="48px",
                        background_color=t.PRIMARY_LIGHT,
                        border_radius=t.RADIUS_MD,
                    ),
                    rx.text(
                        rx.cond(
                            BulkState.bulk_results.length() > 0,
                            "No matching results",
                            "Upload files and process them to see results here.",
                        ),
                        color=t.SECONDARY,
                        text_align="center",
                    ),
                    align="center",
                    justify="center",
                    padding=t.SPACE_12,
                ),
            ),
            background_color=t.SURFACE,
            border=f"1px solid {t.SURFACE_BORDER}",
            border_radius=t.RADIUS_LG,
            padding=t.SPACE_6,
            box_shadow=t.SHADOW_SM,
        ),
        max_width="1200px",
        margin="0 auto",
        padding=rx.breakpoints(initial=f"{t.SPACE_4} 0", md=f"{t.SPACE_6} 0"),
    )
