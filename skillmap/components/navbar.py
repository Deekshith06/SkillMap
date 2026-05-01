"""navbar.py — Redesigned navigation bar using new design spec.
Header: 64px, gradient #2D135F→#220022, white text/icons.
"""
import reflex as rx
from skillmap.styles import theme as t

NAV_ITEMS = [
    ("/",         "Dashboard", "layout-dashboard"),
    ("/analyze",  "Analyze", "scan"),
    ("/bulk",     "Bulk Upload", "upload"),
    ("/ats",      "ATS Editor", "file-text"),
]


def nav_link(href: str, label: str, icon_name: str) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.icon(icon_name, size=16),
            rx.text(label),
            spacing="2",
            align="center",
        ),
        href=href,
        font_weight="500",
        font_size="14px",
        font_family=t.FONT_SANS,
        color=t.SECONDARY,
        padding=f"0.5rem 1rem",
        border_radius=t.RADIUS_PILL,
        text_decoration="none",
        transition=t.TRANSITION_FAST,
        _hover={
            "color": t.DARK,
            "background_color": "transparent",
        },
    )


def logo() -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.box(
                rx.icon("database", size=18),
                background_color=t.PRIMARY,
                color="white",
                width="32px",
                height="32px",
                border_radius=t.RADIUS_MD,
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.text(
                "SkillMap",
                font_weight=t.W_BOLD,
                font_size="1.25rem",
                font_family=t.FONT_HEADING,
                color=t.DARK,
                letter_spacing="-0.02em",
            ),
            spacing="2",
            align="center",
        ),
        href="/",
        text_decoration="none",
    )


def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            logo(),
            # Desktop nav
            rx.hstack(
                *[nav_link(href, label, icon) for href, label, icon in NAV_ITEMS],
                spacing="1",
                display="flex",
            ),
            rx.button(
                "Get Started →",
                on_click=rx.redirect("/analyze"),
                **t.btn_primary(),
            ),
            justify="between",
            align="center",
            width="100%",
            max_width=t.CONTENT_MAX_W,
            margin="0 auto",
            padding=f"0 {t.CONTENT_PADDING}",
            height=t.HEADER_HEIGHT,
        ),
        position="sticky",
        top="0",
        z_index="100",
        background="rgba(255, 251, 247, 0.85)",
        backdrop_filter="blur(16px)",
        border_bottom=f"1px solid {t.BORDER_STRONG}",
    )
