"""file_upload.py — Drag-and-drop upload component wrapper."""

import reflex as rx

from skillmap.styles import theme as t


def file_drop_zone(
    on_drop,
    label: str = "Drop files here",
    sublabel: str = "PDF, DOCX, TXT",
    multiple: bool = False,
    accept: dict | None = None,
    upload_id: str = "upload_zone",
) -> rx.Component:
    if accept is None:
        accept = {
            "application/pdf": [".pdf"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
            "text/plain": [".txt"],
        }
    return rx.upload(
        rx.vstack(
            rx.center(
                rx.icon("upload", size=20, color=t.PRIMARY),
                width="40px",
                height="40px",
                border_radius=t.RADIUS_MD,
                background_color="white",
                border=f"1px solid {t.BORDER}",
            ),
            rx.text(label, font_weight="700", font_size="1rem", color=t.DARK),
            rx.text(sublabel, font_size="0.85rem", color=t.SECONDARY),
            spacing="2",
            align="center",
        ),
        id=upload_id,
        multiple=multiple,
        accept=accept,
        on_drop=on_drop(rx.upload_files(upload_id=upload_id)),
        border=f"1px dashed {t.BORDER_STRONG}",
        border_radius=t.RADIUS_LG,
        background_color=t.PRIMARY_LIGHT,
        min_height="136px",
        padding=rx.breakpoints(initial=t.SPACE_5, md=t.SPACE_6),
        text_align="center",
        cursor="pointer",
        width="100%",
        transition=t.TRANSITION_FAST,
        _hover={
            "border_color": t.PRIMARY,
            "background_color": "rgba(204, 69, 53, 0.14)",
        },
    )
