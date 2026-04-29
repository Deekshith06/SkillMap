"""
skillmap.py — Main Reflex app entry point + routing.

Routes:
  /          → Dashboard (Project Details)
  /analyze   → Analyze (single resume)
  /bulk      → Bulk Upload
  /ats       → ATS Editor
"""
import reflex as rx

from skillmap.pages.dashboard import dashboard_page
from skillmap.pages.analyze import analyze_page
from skillmap.pages.bulk_upload import bulk_upload_page
from skillmap.pages.ats_editor import ats_editor_page


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
            margin="0 auto",
            padding=f"{t.SPACE_6} {t.CONTENT_PADDING}",
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
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Syne:wght@700;800&display=swap",
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
            "font_family": "'DM Sans', sans-serif",
            "font_size": "15px",
            "line_height": "1.6",
            "background_color": "#f5ede0",
            "color": "#161311",
        },
        "h1, h2, h3, h4, h5, h6": {
            "font_family": "'Syne', sans-serif",
            "font_weight": "700",
            "color": "#161311",
            "line_height": "1.2",
        },
        # Focus-visible ring
        "*:focus-visible": {
            "outline": "3px solid rgba(255, 119, 28, 0.12)",
            "outline_offset": "2px",
        },
        # Scrollbar styling
        "::-webkit-scrollbar": {"width": "6px", "height": "6px"},
        "::-webkit-scrollbar-track": {"background": "rgba(84, 104, 119, 0.15)"},
        "::-webkit-scrollbar-thumb": {
            "background": "#546877",
            "border_radius": "9999px",
        },
        "::-webkit-scrollbar-thumb:hover": {"background": "#161311"},
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

app.add_page(index,    route="/")
app.add_page(analyze,  route="/analyze")
app.add_page(bulk,     route="/bulk")
app.add_page(ats,      route="/ats")
