"""Responsive primary navigation for the SkillMap workbench."""

import reflex as rx

from skillmap.styles import theme as t

NAV_ITEMS = [
    ("/", "Dashboard", "layout-dashboard"),
    ("/analyze", "Analyze", "scan"),
    ("/bulk", "Bulk Upload", "upload"),
    ("/ats", "ATS Editor", "file-text"),
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
        min_height="44px",
        padding="0.5rem 0.875rem",
        border_radius=t.RADIUS_SM,
        text_decoration="none",
        transition=t.TRANSITION_FAST,
        _hover={
            "color": t.DARK,
            "background_color": t.SURFACE_HOVER,
        },
    )


def logo() -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.box(
                rx.icon("network", size=18),
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
                letter_spacing="0",
            ),
            spacing="2",
            align="center",
        ),
        href="/",
        text_decoration="none",
    )


def mobile_nav_link(href: str, label: str, icon_name: str) -> rx.Component:
    return rx.link(
        rx.vstack(
            rx.icon(icon_name, size=19),
            rx.text(label, font_size="0.7rem", font_weight=t.W_SEMI),
            spacing="1",
            align="center",
        ),
        href=href,
        color=t.SECONDARY,
        min_width="64px",
        min_height="56px",
        display="flex",
        align_items="center",
        justify_content="center",
        border_radius=t.RADIUS_SM,
        _hover={"color": t.PRIMARY, "background_color": t.PRIMARY_LIGHT},
    )


def navbar() -> rx.Component:
    return rx.fragment(
        rx.box(
            rx.hstack(
                logo(),
                rx.hstack(
                    *[nav_link(href, label, icon) for href, label, icon in NAV_ITEMS],
                    spacing="1",
                    display=rx.breakpoints(initial="none", md="flex"),
                ),
                rx.box(
                    "LITE",
                    display=rx.breakpoints(initial="inline-flex", md="none"),
                    color=t.SUCCESS,
                    background_color="rgba(46, 125, 104, 0.10)",
                    border="1px solid rgba(46, 125, 104, 0.22)",
                    border_radius=t.RADIUS_PILL,
                    padding="3px 9px",
                    font_family=t.FONT_MONO,
                    font_size="0.68rem",
                    font_weight=t.W_BOLD,
                ),
                rx.box(
                    rx.button(
                        rx.icon("scan", size=16),
                        rx.text("Analyze resume"),
                        on_click=rx.redirect("/analyze"),
                        **t.btn_primary(),
                    ),
                    display=rx.breakpoints(initial="none", md="block"),
                ),
                justify="between",
                align="center",
                width="100%",
                max_width=t.CONTENT_MAX_W,
                margin="0 auto",
                padding=rx.breakpoints(initial="0 1rem", md=f"0 {t.CONTENT_PADDING}"),
                height=t.HEADER_HEIGHT,
            ),
            position="sticky",
            top="0",
            z_index="100",
            background="rgba(255, 255, 255, 0.94)",
            backdrop_filter="blur(16px)",
            border_bottom=f"1px solid {t.BORDER}",
        ),
        rx.box(
            rx.hstack(
                *[mobile_nav_link(href, label, icon) for href, label, icon in NAV_ITEMS],
                justify="between",
                align="center",
                width="100%",
            ),
            display=rx.breakpoints(initial="block", md="none"),
            position="fixed",
            left="0",
            right="0",
            bottom="0",
            z_index="200",
            background_color="rgba(255, 255, 255, 0.97)",
            backdrop_filter="blur(16px)",
            border_top=f"1px solid {t.BORDER_STRONG}",
            padding="4px 12px max(4px, env(safe-area-inset-bottom))",
        ),
    )
