"""
skillmap.py — Main Reflex app entry point + routing.

Routes:
  /          → Dashboard (Project Details)
  /analyze   → Analyze (single resume)
  /bulk      → Bulk Upload
  /ats       → ATS Editor
"""

import logging

import reflex as rx

from skillmap.api import backend_api
from skillmap.config.logging import configure_logging
from skillmap.pages.analyze import analyze_page
from skillmap.pages.ats_editor import ats_editor_page
from skillmap.pages.bulk_upload import bulk_upload_page
from skillmap.pages.dashboard import dashboard_page
from skillmap.state.app_state import AppState
from skillmap.styles import theme as t

configure_logging()
logger = logging.getLogger("skillmap.app")


def backend_exception_handler(exception: Exception) -> None:
    logger.error(
        "unhandled_backend_exception",
        extra={"event": {"error_category": type(exception).__name__}},
    )


# Dashboard manages its own navbar — wrap others with shared shell
def _page_shell(content_fn) -> rx.Component:
    from skillmap.components.navbar import navbar
    from skillmap.components.ui import footer
    from skillmap.styles import theme as t

    return rx.box(
        navbar(),
        rx.box(
            content_fn(),
            max_width=t.CONTENT_MAX_W,
            width="100%",
            min_width="0",
            margin="0 auto",
            padding=rx.breakpoints(
                initial=f"{t.SPACE_4} {t.SPACE_4} 6rem",
                md=f"{t.SPACE_6} {t.CONTENT_PADDING}",
            ),
            flex="1",
        ),
        footer(),
        min_height="100vh",
        display="flex",
        flex_direction="column",
        background_color=t.BG,
        font_family=t.FONT_SANS,
        color=t.TEXT_PRIMARY,
    )


def index() -> rx.Component:
    return dashboard_page()


def analyze() -> rx.Component:
    return _page_shell(analyze_page)


def bulk() -> rx.Component:
    return _page_shell(bulk_upload_page)


def ats() -> rx.Component:
    return _page_shell(ats_editor_page)


# ── App ──────────────────────────────────────────────────────────

app = rx.App(
    api_transformer=backend_api,
    backend_exception_handler=backend_exception_handler,
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Lexend:wght@500;600;700&family=Source+Sans+3:wght@400;500;600;700&display=swap",
    ],
    style={
        "*": {
            "box_sizing": "border-box",
            "margin": "0",
            "padding": "0",
        },
        "body": {
            "overflow_x": "hidden",
            "-webkit-font-smoothing": "antialiased",
            "-moz-osx-font-smoothing": "grayscale",
            "font_family": "'Source Sans 3', sans-serif",
            "font_size": "16px",
            "line_height": "1.6",
            "background_color": t.BG,
            "color": t.DARK,
        },
        "h1, h2, h3, h4, h5, h6": {
            "font_family": "'Lexend', sans-serif",
            "font_weight": "700",
            "line_height": "1.25",
            "letter_spacing": "0",
        },
        # Focus-visible ring
        "*:focus-visible": {
            "outline": f"3px solid {t.PRIMARY_LIGHT}",
            "outline_offset": "2px",
        },
        # Scrollbar styling
        "::-webkit-scrollbar": {"width": "6px", "height": "6px"},
        "::-webkit-scrollbar-track": {"background": t.SECONDARY_LIGHT},
        "::-webkit-scrollbar-thumb": {
            "background": t.SECONDARY,
            "border_radius": "9999px",
        },
        "::-webkit-scrollbar-thumb:hover": {"background": t.DARK},
        # Skeleton pulse animation
        "@keyframes pulse": {
            "0%, 100%": {"opacity": "1"},
            "50%": {"opacity": "0.5"},
        },
        ".animate-pulse": {"animation": "pulse 1.5s ease-in-out infinite"},
        # Smooth link behaviour
        "a": {"text_decoration": "none"},
    },
)

app.add_page(index, route="/", on_load=AppState.load_data)
app.add_page(analyze, route="/analyze")
app.add_page(bulk, route="/bulk")
app.add_page(ats, route="/ats")
