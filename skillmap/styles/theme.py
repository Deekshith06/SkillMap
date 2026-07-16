"""Shared visual tokens for the SkillMap workbench."""

# ── Brand palette ────────────────────────────────────────────────────────────
PRIMARY = "#CC4535"
PRIMARY_HOVER = "#A93428"
PRIMARY_LIGHT = "rgba(204, 69, 53, 0.10)"
SECONDARY = "#50676F"
SECONDARY_LIGHT = "rgba(80, 103, 111, 0.10)"
DARK = "#172426"
BG = "#F4F7F6"
SURFACE = "#ffffff"
SURFACE_ALT = "#F9FBFA"
SURFACE_HOVER = "#EEF3F1"
SURFACE_BORDER = "rgba(23, 36, 38, 0.10)"
BORDER = "rgba(23, 36, 38, 0.10)"
BORDER_STRONG = "rgba(23, 36, 38, 0.18)"
ERROR = "#B83A3A"
SUCCESS = "#2E7D68"
WARNING = "#A76516"
TEXT_PRIMARY = DARK
TEXT_SECONDARY = SECONDARY
TEXT_MUTED = "rgba(23, 36, 38, 0.58)"

BRAND = PRIMARY
BRAND_DARK = DARK
ACCENT = PRIMARY

# ── Architecture Palette (Figma Spec) ────────────────────────────────────────
ARCH_ORANGE_600 = "#E07340"
ARCH_ORANGE_50 = "#FAF0E8"
ARCH_ORANGE_100 = "#EDD4C0"
ARCH_NEUTRAL_900 = "#1C1917"
ARCH_NEUTRAL_500 = "#6B6460"
ARCH_NEUTRAL_300 = "#E4DDD8"
ARCH_NEUTRAL_200 = "#C8BDB6"
ARCH_NEUTRAL_50 = "#F8F5F2"

# ── Gradients ─────────────────────────────────────────────────────────────────
GRAD_HEADER = f"{BG}"
GRAD_CARD = f"linear-gradient(180deg, #FFFFFF 0%, {BG} 100%)"
GRAD_SIDEBAR_HOVER = "linear-gradient(90deg, rgba(204,69,53,0.1) 0%, transparent 100%)"

# ── Typography ────────────────────────────────────────────────────────────────
FONT_SANS = "'Source Sans 3', sans-serif"
FONT_HEADING = "'Lexend', sans-serif"
FONT_MONO = "ui-monospace, 'SFMono-Regular', Consolas, monospace"

# Sizes
TEXT_H1 = "1.75rem"  # 28px
TEXT_H2 = "1.375rem"  # 22px
TEXT_H3 = "1.125rem"  # 18px
TEXT_H4 = "0.9375rem"  # 15px
TEXT_BODY = "0.875rem"  # 14px
TEXT_SMALL = "0.75rem"  # 12px
TEXT_CAPTION = "0.6875rem"  # 11px
TEXT_MONO = "0.8125rem"  # 13px

# Weights
W_REGULAR = "400"
W_MEDIUM = "500"
W_SEMI = "600"
W_BOLD = "700"

# ── Spacing (4px base grid) ───────────────────────────────────────────────────
SPACE_1 = "0.25rem"  # 4px
SPACE_2 = "0.5rem"  # 8px
SPACE_3 = "0.75rem"  # 12px
SPACE_4 = "1rem"  # 16px
SPACE_5 = "1.5rem"  # 24px
SPACE_6 = "2rem"  # 32px
SPACE_7 = "3rem"  # 48px
SPACE_8 = "4rem"  # 64px
SPACE_12 = "6rem"  # 96px  (legacy alias)

# ── Border Radius ─────────────────────────────────────────────────────────────
RADIUS_SM = "6px"
RADIUS_MD = "8px"
RADIUS_LG = "8px"
RADIUS_XL = "8px"
RADIUS_PILL = "9999px"

# ── Shadows ───────────────────────────────────────────────────────────────────
SHADOW_SM = "0 1px 2px rgba(23, 36, 38, 0.05)"
SHADOW_MD = "0 8px 24px rgba(23, 36, 38, 0.08)"
SHADOW_LG = "0 16px 40px rgba(23, 36, 38, 0.12)"
SHADOW_BRAND = "0 6px 18px rgba(204, 69, 53, 0.20)"

# ── Transitions ───────────────────────────────────────────────────────────────
TRANSITION_FAST = "all 150ms cubic-bezier(0.4,0,0.2,1)"
TRANSITION_BASE = "all 200ms cubic-bezier(0.4,0,0.2,1)"
TRANSITION_SLOW = "all 300ms cubic-bezier(0.4,0,0.2,1)"

# ── Chart Colors (brand-aligned) ──────────────────────────────────────────────
CHART_COLORS = [
    "#F4B34F",
    "#C06F30",
    "#861C1C",
    "#2B1D1C",
    "#3a7ca5",
    "#546877",
    "#6b8f71",
    "#8e7cc3",
    "#5b9bd5",
    "#70ad47",
]

ORANGE_PALETTE = [
    "#803a00",  # Darkest
    "#a64d00",
    "#cc5e00",
    "#f27000",
    "#ff771c",  # Main
    "#ff8b3d",
    "#ffa05e",
    "#ffb480",
    "#ffc9a1",
    "#ffdec2",  # Lightest
]

# ── Layout constants ──────────────────────────────────────────────────────────
SIDEBAR_WIDTH = "280px"
HEADER_HEIGHT = "64px"
CONTENT_MAX_W = "1280px"
CONTENT_PADDING = SPACE_6


# ── Component style helpers ───────────────────────────────────────────────────


def card_style(**extra) -> dict:
    return {
        "background_color": SURFACE,
        "border": f"1px solid {BORDER_STRONG}",
        "border_radius": RADIUS_LG,
        "padding": "24px",
        "box_shadow": SHADOW_SM,
        "transition": TRANSITION_BASE,
        **extra,
    }


def card_hover_style(**extra) -> dict:
    return {
        "border_color": BORDER_STRONG,
        "box_shadow": SHADOW_MD,
        **extra,
    }


def btn_primary(**extra) -> dict:
    return {
        "background_color": PRIMARY,
        "color": "white",
        "min_height": "44px",
        "padding": "0.6rem 1.25rem",
        "border_radius": RADIUS_MD,
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
            "box_shadow": SHADOW_BRAND,
        },
        "_disabled": {
            "opacity": "0.6",
            "cursor": "not-allowed",
        },
        **extra,
    }


def btn_secondary(**extra) -> dict:
    return {
        "background_color": SURFACE,
        "color": DARK,
        "min_height": "44px",
        "padding": "0.6rem 1.25rem",
        "border_radius": RADIUS_MD,
        "font_size": "0.95rem",
        "font_weight": "600",
        "font_family": FONT_SANS,
        "cursor": "pointer",
        "border": f"1px solid {BORDER_STRONG}",
        "transition": f"all {TRANSITION_FAST}",
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "gap": SPACE_2,
        "_hover": {
            "background_color": SURFACE_HOVER,
            "border_color": SECONDARY,
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
        "border_radius": RADIUS_MD,
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
SURFACE_BORDER = BORDER
SURFACE_HOVER = "#EEF3F1"
DARK_HOVER = "#1A1211"
DARK_LIGHT = "rgba(43, 29, 28, 0.6)"
SECONDARY_LIGHT = "rgba(80, 103, 111, 0.10)"
ERROR_LIGHT = "rgba(239, 68, 68, 0.10)"

DARK_BG = DARK
DARK_SURFACE = "#3d2a29"
DARK_SURFACE_HOVER = DARK
DARK_SURFACE_BORDER = "rgba(255, 255, 255, 0.10)"
DARK_TEXT = "#FFFFFF"
DARK_SECONDARY = "#9ca3af"

FONT_BODY = FONT_SANS

SHADOW_XL = SHADOW_LG
