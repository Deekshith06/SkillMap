"""
styles/theme.py — Design system tokens matching the UI specification.
Color palette: Dr. White · Festive Ferret · Kiri Mist · Voldemort · Black Sabbath · Imperial Red
"""

# ── Brand Palette (Cocoa & Amber Theme) ────────────────────────────────────
PRIMARY = "#ff771c"
PRIMARY_HOVER = "#e66815"
PRIMARY_LIGHT = "rgba(255, 119, 28, 0.12)"
SECONDARY = "#546877"
SECONDARY_LIGHT = "rgba(84, 104, 119, 0.15)"
DARK = "#161311"
BG = "#f5ede0"
SURFACE = "#ffffff"
SURFACE_ALT = "#fafafa"
SURFACE_HOVER = "#fafafa"
SURFACE_BORDER = "rgba(22, 19, 17, 0.08)"
BORDER = "rgba(22, 19, 17, 0.08)"
BORDER_STRONG = "rgba(22, 19, 17, 0.15)"
ERROR = "#c75146"
SUCCESS = "#6b8f71"
WARNING = "#e8913a"
TEXT_PRIMARY = DARK
TEXT_SECONDARY = SECONDARY
TEXT_MUTED = "rgba(22, 19, 17, 0.6)"

BRAND = PRIMARY
BRAND_DARK = DARK
ACCENT = PRIMARY

# ── Gradients ─────────────────────────────────────────────────────────────────
GRAD_HEADER = f"{BG}"
GRAD_CARD = f"linear-gradient(180deg, #FFFFFF 0%, {BG} 100%)"
GRAD_SIDEBAR_HOVER = f"linear-gradient(90deg, rgba(255,119,28,0.1) 0%, transparent 100%)"

# ── Typography ────────────────────────────────────────────────────────────────
FONT_SANS  = "'DM Sans', sans-serif"
FONT_HEADING = "'Syne', sans-serif"
FONT_MONO  = "'JetBrains Mono', 'Fira Code', monospace"

# Sizes
TEXT_H1      = "1.75rem"   # 28px
TEXT_H2      = "1.375rem"  # 22px
TEXT_H3      = "1.125rem"  # 18px
TEXT_H4      = "0.9375rem" # 15px
TEXT_BODY    = "0.875rem"  # 14px
TEXT_SMALL   = "0.75rem"   # 12px
TEXT_CAPTION = "0.6875rem" # 11px
TEXT_MONO    = "0.8125rem" # 13px

# Weights
W_REGULAR = "400"
W_MEDIUM  = "500"
W_SEMI    = "600"
W_BOLD    = "700"

# ── Spacing (4px base grid) ───────────────────────────────────────────────────
SPACE_1  = "0.25rem"   # 4px
SPACE_2  = "0.5rem"    # 8px
SPACE_3  = "0.75rem"   # 12px
SPACE_4  = "1rem"      # 16px
SPACE_5  = "1.5rem"    # 24px
SPACE_6  = "2rem"      # 32px
SPACE_7  = "3rem"      # 48px
SPACE_8  = "4rem"      # 64px
SPACE_12 = "6rem"      # 96px  (legacy alias)

# ── Border Radius ─────────────────────────────────────────────────────────────
RADIUS_SM   = "6px"
RADIUS_MD   = "8px"
RADIUS_LG   = "12px"
RADIUS_XL   = "16px"
RADIUS_PILL = "9999px"

# ── Shadows ───────────────────────────────────────────────────────────────────
SHADOW_SM    = "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)"
SHADOW_MD    = "0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)"
SHADOW_LG    = "0 8px 24px rgba(0,0,0,0.10), 0 4px 8px rgba(0,0,0,0.06)"
SHADOW_BRAND = "0 4px 12px rgba(45,19,95,0.20)"

# ── Transitions ───────────────────────────────────────────────────────────────
TRANSITION_FAST = "all 150ms cubic-bezier(0.4,0,0.2,1)"
TRANSITION_BASE = "all 200ms cubic-bezier(0.4,0,0.2,1)"
TRANSITION_SLOW = "all 300ms cubic-bezier(0.4,0,0.2,1)"

# ── Chart Colors (brand-aligned) ──────────────────────────────────────────────
CHART_COLORS = [
    "#F4B34F", "#C06F30", "#861C1C", "#2B1D1C",
    "#3a7ca5", "#546877", "#6b8f71", "#8e7cc3",
    "#5b9bd5", "#70ad47",
]

ORANGE_PALETTE = [
    "#803a00", # Darkest
    "#a64d00",
    "#cc5e00",
    "#f27000",
    "#ff771c", # Main
    "#ff8b3d",
    "#ffa05e",
    "#ffb480",
    "#ffc9a1",
    "#ffdec2"  # Lightest
]

# ── Layout constants ──────────────────────────────────────────────────────────
SIDEBAR_WIDTH   = "280px"
HEADER_HEIGHT   = "64px"
CONTENT_MAX_W   = "1280px"
CONTENT_PADDING = SPACE_6


# ── Component style helpers ───────────────────────────────────────────────────

def card_style(**extra) -> dict:
    return {
        "background_color": SURFACE,
        "border": f"1px solid {BORDER}",
        "border_radius": RADIUS_XL,
        "padding": "24px",
        "box_shadow": SHADOW_SM,
        "transition": TRANSITION_BASE,
        **extra,
    }


def card_hover_style(**extra) -> dict:
    return {
        "box_shadow": "0 10px 15px -3px rgba(43, 29, 28, 0.1)",
        "transform": "translateY(-2px)",
        **extra,
    }


def btn_primary(**extra) -> dict:
    return {
        "background_color": PRIMARY,
        "color": "white",
        "min_height": "44px",
        "padding": "0.6rem 1.25rem",
        "border_radius": RADIUS_PILL,
        "font_size": "0.95rem",
        "font_weight": "600",
        "font_family": FONT_SANS,
        "cursor": "pointer",
        "border": "none",
        "transition": f"all {TRANSITION_FAST}",
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "gap": SPACE_2,
        "_hover": {
            "background_color": PRIMARY_HOVER,
            "transform": "translateY(-1px)",
            "box_shadow": SHADOW_SM,
        },
        "_disabled": {
            "opacity": "0.6",
            "cursor": "not-allowed",
        },
        **extra,
    }


def btn_secondary(**extra) -> dict:
    return {
        "background_color": DARK,
        "color": BG,
        "min_height": "44px",
        "padding": "0.6rem 1.25rem",
        "border_radius": RADIUS_PILL,
        "font_size": "0.95rem",
        "font_weight": "600",
        "font_family": FONT_SANS,
        "cursor": "pointer",
        "border": "none",
        "transition": f"all {TRANSITION_FAST}",
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "gap": SPACE_2,
        "_hover": {
            "background_color": "#2c2622",
            "transform": "translateY(-1px)",
            "box_shadow": SHADOW_SM,
        },
        "_disabled": {
            "opacity": "0.6",
            "cursor": "not-allowed",
        },
        **extra,
    }


def btn_ghost(**extra) -> dict:
    return {
        "background_color": "transparent",
        "color": SECONDARY,
        "min_height": "44px",
        "padding": "0.6rem 1.25rem",
        "border_radius": RADIUS_PILL,
        "font_size": "0.95rem",
        "font_weight": "600",
        "font_family": FONT_SANS,
        "cursor": "pointer",
        "border": "none",
        "transition": f"all {TRANSITION_FAST}",
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "gap": SPACE_2,
        "_hover": {
            "background_color": SECONDARY_LIGHT,
            "color": DARK,
        },
        "_disabled": {
            "opacity": "0.6",
            "cursor": "not-allowed",
        },
        **extra,
    }


# Legacy aliases kept for backward compatibility with existing pages
SURFACE_BORDER  = BORDER
SURFACE_HOVER   = BG
DARK_HOVER      = "#1A1211"
DARK_LIGHT      = "rgba(43, 29, 28, 0.6)"
SECONDARY_LIGHT = "rgba(107, 114, 128, 0.12)"
ERROR_LIGHT     = "rgba(239, 68, 68, 0.10)"

DARK_BG             = DARK
DARK_SURFACE        = "#3d2a29"
DARK_SURFACE_HOVER  = DARK
DARK_SURFACE_BORDER = "rgba(255, 255, 255, 0.10)"
DARK_TEXT           = "#FFFFFF"
DARK_SECONDARY      = "#9ca3af"

FONT_HEADING = FONT_SANS
FONT_BODY    = FONT_SANS

SHADOW_XL = SHADOW_LG
