"""
components/ui.py — Reusable UI component library matching the design spec.
Covers: StatusBadge, StatsCard, SectionHeader, TimelineItem, PipelineStep,
        SidebarMeta, ProgressRing, TabBar, SkeletonCard, Footer.
"""
from __future__ import annotations
import reflex as rx
from skillmap.styles import theme as t


# ─────────────────────────────────────────────────────────────────────────────
# StatusBadge
# ─────────────────────────────────────────────────────────────────────────────

_BADGE_STYLES: dict[str, dict] = {
    "active":   {"bg": f"rgba(45,19,95,0.10)",  "color": t.BRAND,     "border": f"rgba(45,19,95,0.20)"},
    "success":  {"bg": f"rgba(22,163,74,0.10)",  "color": t.SUCCESS,       "border": f"rgba(22,163,74,0.20)"},
    "error":    {"bg": f"rgba(236,41,56,0.10)",  "color": t.ERROR,  "border": f"rgba(236,41,56,0.20)"},
    "warning":  {"bg": f"rgba(234,179,8,0.10)",  "color": t.WARNING,       "border": f"rgba(234,179,8,0.20)"},
    "neutral":  {"bg": t.BORDER,         "color": t.TEXT_PRIMARY, "border": t.BORDER},
}


def status_badge(label: str, variant: str = "active") -> rx.Component:
    s = _BADGE_STYLES.get(variant, _BADGE_STYLES["neutral"])
    return rx.box(
        label,
        background_color=s["bg"],
        color=s["color"],
        border=f"1px solid {s['border']}",
        border_radius=t.RADIUS_PILL,
        padding=f"2px 10px",
        font_size=t.TEXT_CAPTION,
        font_weight=t.W_MEDIUM,
        font_family=t.FONT_SANS,
        display="inline-flex",
        align_items="center",
        white_space="nowrap",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tag chip
# ─────────────────────────────────────────────────────────────────────────────

def tag_chip(label: str) -> rx.Component:
    return rx.box(
        label,
        background_color=t.BORDER,
        color=t.BRAND,
        border=f"1px solid {t.BORDER}",
        border_radius=t.RADIUS_PILL,
        padding=f"3px 12px",
        font_size=t.TEXT_CAPTION,
        font_weight=t.W_MEDIUM,
        font_family=t.FONT_SANS,
    )


# ─────────────────────────────────────────────────────────────────────────────
# StatsCard
# ─────────────────────────────────────────────────────────────────────────────

def stats_card(
    icon: str,
    value: str | rx.Component,
    label: str,
    value_color: str = t.TEXT_PRIMARY,
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.center(
                    rx.icon(icon, size=18),
                    width="36px", height="36px", border_radius="8px",
                    background_color=t.PRIMARY_LIGHT, color=t.PRIMARY,
                    margin_bottom="8px"
                ),
                rx.spacer(),
                align="center",
                width="100%",
            ),
            rx.text(
                value,
                font_size="1.75rem",
                font_weight=t.W_BOLD,
                color=value_color,
                font_family=t.FONT_HEADING,
                letter_spacing="-0.02em",
                line_height="1",
            ),
            rx.text(
                label,
                font_size=t.TEXT_SMALL,
                font_weight=t.W_MEDIUM,
                color=t.TEXT_SECONDARY,
                font_family=t.FONT_SANS,
            ),
            spacing="2",
            align_items="start",
        ),
        **t.card_style(),
        _hover=t.card_hover_style(),
        cursor="default",
        flex="1",
        min_width="160px",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Section header
# ─────────────────────────────────────────────────────────────────────────────

def section_header(title: str, subtitle: str = "") -> rx.Component:
    children = [
        rx.heading(
            title,
            size="5",
            font_family=t.FONT_HEADING,
            font_weight=t.W_BOLD,
            color=t.TEXT_PRIMARY,
            letter_spacing="-0.01em",
        ),
    ]
    if subtitle:
        children.append(
            rx.text(
                subtitle,
                font_size=t.TEXT_BODY,
                color=t.TEXT_SECONDARY,
                font_family=t.FONT_SANS,
            )
        )
    return rx.vstack(*children, spacing="1", align_items="start", margin_bottom=t.SPACE_4)


# ─────────────────────────────────────────────────────────────────────────────
# PipelineStep
# ─────────────────────────────────────────────────────────────────────────────

def pipeline_step(label: str, progress: int, done: bool = True) -> rx.Component:
    bar_color = t.SUCCESS if done else t.BRAND
    icon = "✓" if done else "…"
    icon_color = t.SUCCESS if done else t.BRAND
    return rx.vstack(
        rx.hstack(
            rx.text(
                label,
                font_size=t.TEXT_BODY,
                font_weight=t.W_SEMI,
                color=t.TEXT_PRIMARY,
                font_family=t.FONT_SANS,
            ),
            rx.text(
                icon,
                font_size=t.TEXT_BODY,
                font_weight=t.W_BOLD,
                color=icon_color,
            ),
            rx.text(
                f"{progress}%",
                font_size=t.TEXT_SMALL,
                color=t.TEXT_SECONDARY,
                font_family=t.FONT_MONO,
                margin_left="auto",
            ),
            width="100%",
            align="center",
        ),
        rx.box(
            rx.box(
                width=f"{progress}%",
                height="6px",
                background_color=bar_color,
                border_radius=t.RADIUS_PILL,
                transition="width 600ms cubic-bezier(0.4,0,0.2,1)",
            ),
            width="100%",
            height="6px",
            background_color=t.BORDER,
            border_radius=t.RADIUS_PILL,
            overflow="hidden",
        ),
        spacing="2",
        width="100%",
    )


# ─────────────────────────────────────────────────────────────────────────────
# TimelineItem
# ─────────────────────────────────────────────────────────────────────────────

_DOT_COLORS = {
    "success": t.SUCCESS,
    "error":   t.ERROR,
    "info":    t.BRAND,
    "neutral": t.BORDER,
}


def timeline_item(
    title: str,
    description: str,
    timestamp: str,
    dot_type: str = "info",
) -> rx.Component:
    dot_color = _DOT_COLORS.get(dot_type, t.BRAND)
    return rx.hstack(
        # Left: dot + line
        rx.vstack(
            rx.box(
                width="10px",
                height="10px",
                border_radius="50%",
                background_color=dot_color,
                flex_shrink="0",
                margin_top="4px",
            ),
            width="10px",
            align_items="center",
        ),
        # Right: content
        rx.vstack(
            rx.hstack(
                rx.text(
                    title,
                    font_size=t.TEXT_BODY,
                    font_weight=t.W_SEMI,
                    color=t.TEXT_PRIMARY,
                    font_family=t.FONT_SANS,
                ),
                rx.text(
                    timestamp,
                    font_size=t.TEXT_SMALL,
                    color=t.TEXT_MUTED,
                    font_family=t.FONT_SANS,
                    margin_left="auto",
                ),
                width="100%",
                align="center",
            ),
            rx.text(
                description,
                font_size=t.TEXT_SMALL,
                color=t.TEXT_SECONDARY,
                font_family=t.FONT_SANS,
            ),
            spacing="1",
            align_items="start",
            flex="1",
        ),
        spacing="3",
        align_items="start",
        width="100%",
        padding_bottom=t.SPACE_3,
        border_bottom=f"1px solid {t.BORDER}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# SidebarMeta row
# ─────────────────────────────────────────────────────────────────────────────

def meta_row(label: str, value: str) -> rx.Component:
    return rx.hstack(
        rx.text(
            label,
            font_size=t.TEXT_SMALL,
            color=t.TEXT_SECONDARY,
            font_family=t.FONT_SANS,
            min_width="70px",
        ),
        rx.text(
            value,
            font_size=t.TEXT_SMALL,
            color=t.TEXT_PRIMARY,
            font_weight=t.W_MEDIUM,
            font_family=t.FONT_SANS,
        ),
        spacing="2",
        align="center",
        width="100%",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Skeleton loader card
# ─────────────────────────────────────────────────────────────────────────────

def skeleton_bar(width: str = "100%", height: str = "12px", margin_bottom: str = "0", margin_top: str = "0", **kwargs) -> rx.Component:
    return rx.box(
        width=width,
        height=height,
        background_color=t.SECONDARY_LIGHT,
        border_radius=t.RADIUS_PILL,
        margin_bottom=margin_bottom,
        margin_top=margin_top,
        animation="pulse 1.5s ease-in-out infinite",
        opacity="0.6",
        **kwargs
    )


def skeleton_card(height: str = "120px") -> rx.Component:
    return rx.box(
        rx.vstack(
            skeleton_bar(width="40%", height="16px", margin_bottom=t.SPACE_4),
            skeleton_bar(width="90%", height="12px", margin_bottom=t.SPACE_2),
            skeleton_bar(width="75%", height="12px", margin_bottom=t.SPACE_2),
            align_items="start",
            width="100%",
        ),
        **t.card_style(),
        height=height,
    )


def error_alert(message: str) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon("circle-alert", color=t.ERROR, size=20, flex_shrink="0"),
            rx.text(message, color=t.ERROR, font_size="0.85rem", font_weight="600"),
            spacing="3",
            align="center",
        ),
        background_color=t.ERROR_LIGHT,
        border=f"1px solid rgba(199, 81, 70, 0.2)",
        border_radius=t.RADIUS_MD,
        padding=f"{t.SPACE_3} {t.SPACE_4}",
        margin_top=t.SPACE_4,
        width="100%",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Divider
# ─────────────────────────────────────────────────────────────────────────────

def divider() -> rx.Component:
    return rx.box(
        height="1px",
        background_color=t.BORDER_STRONG,
        width="100%",
        margin=f"{t.SPACE_4} 0",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────

def footer() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.hstack(
                *[
                    rx.link(
                        lbl, href=href,
                        font_size=t.TEXT_SMALL,
                        color=t.TEXT_SECONDARY,
                        font_family=t.FONT_SANS,
                        text_decoration="none",
                        _hover={"color": t.BRAND},
                    )
                    for href, lbl in [
                        ("/", "Projects"),
                        ("/insights", "Analytics"),
                        ("/ats", "ATS"),
                    ]
                ],
                spacing="5",
            ),
            rx.text(
                "SkillMap v2.0 · HDBSCAN",
                font_size=t.TEXT_SMALL,
                color=t.TEXT_MUTED,
                font_family=t.FONT_MONO,
            ),
            justify="between",
            align="center",
            width="100%",
            max_width=t.CONTENT_MAX_W,
            margin="0 auto",
            padding=f"0 {t.CONTENT_PADDING}",
        ),
        background_color=t.BORDER,
        border_top=f"1px solid {t.BORDER}",
        height="52px",
        margin_top=t.SPACE_8,
    )
