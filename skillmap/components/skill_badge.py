"""skill_badge.py — Skill tag/badge component."""
import reflex as rx
from skillmap.styles import theme as t

SKILL_COLORS = [t.PRIMARY, "#3a7ca5", "#6b8f71", "#8e7cc3", "#546877"]


def skill_badge(name: str, index: int = 0) -> rx.Component:
    color = SKILL_COLORS[index % len(SKILL_COLORS)]
    return rx.box(
        name,
        display="inline-flex",
        align_items="center",
        padding="0.2rem 0.6rem",
        background_color=f"{color}20",
        color=color,
        font_size="0.8rem",
        font_weight="600",
        border_radius=t.RADIUS_SM,
        white_space="nowrap",
    )


def skill_pill_primary(name: str) -> rx.Component:
    return rx.box(
        name,
        display="inline-flex",
        align_items="center",
        padding="0.25rem 0.6rem",
        background_color=t.PRIMARY_LIGHT,
        color=t.PRIMARY,
        border="none",
        font_size="0.8rem",
        font_weight="600",
        border_radius=t.RADIUS_SM,
    )


def skill_pill_muted(name: str) -> rx.Component:
    return rx.box(
        name,
        display="inline-flex",
        align_items="center",
        padding="0.25rem 0.6rem",
        background_color=t.SECONDARY_LIGHT,
        color=t.SECONDARY,
        border="none",
        font_size="0.8rem",
        font_weight="600",
        border_radius=t.RADIUS_SM,
    )
