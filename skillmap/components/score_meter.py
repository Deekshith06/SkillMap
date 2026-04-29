"""score_meter.py — ATS score ring/progress component (Var-safe)."""
import reflex as rx
from skillmap.styles import theme as t


def score_ring(score, size: int = 140, label: str = "Score") -> rx.Component:
    """Simple score display ring."""
    return rx.box(
        rx.text(score.to_string() + "%",
                font_family=t.FONT_HEADING, font_size="2rem",
                font_weight="800", color=t.PRIMARY, line_height="1"),
        rx.text(label, font_size="0.7rem", text_transform="uppercase",
                letter_spacing="0.05em", color=t.SECONDARY, margin_top="4px"),
        display="flex", flex_direction="column",
        align_items="center", justify_content="center",
        width=f"{size}px", height=f"{size}px",
        border_radius="50%",
        border=f"5px solid {t.PRIMARY}",
        background_color=t.PRIMARY_LIGHT,
    )


def sub_score_bar(label: str, score, max_score: int = 100,
                  color: str = t.PRIMARY) -> rx.Component:
    """Var-safe sub-score bar.
    
    score must be a numeric Var or plain int.
    pct = score / max_score * 100  — computed client-side via Reflex Var ops.
    """
    pct_var = (score * 100 / max_score).to(int)
    return rx.vstack(
        rx.hstack(
            rx.text(label, font_size="0.85rem", font_weight="600", color=t.SECONDARY),
            rx.text(
                score.to_string() + "/" + str(max_score),
                font_size="0.85rem", font_weight="700", color=color,
            ),
            justify="between", width="100%",
        ),
        rx.box(
            rx.box(
                height="100%",
                width=pct_var.to_string() + "%",
                background_color=color,
                border_radius=t.RADIUS_PILL,
                style={"transition": "width 0.6s ease"},
            ),
            width="100%", height="6px",
            background_color=t.SECONDARY_LIGHT,
            border_radius=t.RADIUS_PILL,
            overflow="hidden",
        ),
        spacing="1", width="100%",
    )
