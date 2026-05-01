"""cluster_card.py — Cluster summary card using new design tokens."""
import reflex as rx
from skillmap.styles import theme as t


def cluster_card(cluster) -> rx.Component:
    """Accepts a ClusterItem rx.Base object from AppState.clusters."""
    return rx.box(
        # Top accent bar in brand color
        rx.box(
            height="3px",
            background_color=t.BRAND,
            position="absolute",
            top="0", left="0", right="0",
            border_radius=f"{t.RADIUS_LG} {t.RADIUS_LG} 0 0",
        ),
        # Header row: dot + "Cluster" label
        rx.hstack(
            rx.box(width="8px", height="8px", border_radius="50%",
                   background_color=t.BRAND, flex_shrink="0"),
            rx.text("Cluster", font_size=t.TEXT_CAPTION, font_weight=t.W_BOLD,
                    color=t.TEXT_SECONDARY, font_family=t.FONT_SANS,
                    text_transform="uppercase", letter_spacing="0.06em"),
            spacing="2", align="center", margin_bottom=t.SPACE_3,
        ),
        # Cluster name
        rx.text(
            cluster.name,
            font_size=t.TEXT_H4,
            font_weight=t.W_BOLD,
            font_family=t.FONT_SANS,
            color=t.TEXT_PRIMARY,
            letter_spacing="-0.01em",
            margin_bottom=t.SPACE_1,
        ),
        # Candidate count
        rx.text(
            cluster.size.to_string() + " candidates",
            font_size=t.TEXT_SMALL,
            color=t.TEXT_SECONDARY,
            font_family=t.FONT_SANS,
            margin_bottom=t.SPACE_4,
        ),
        # Skill pills
        rx.flex(
            rx.foreach(
                cluster.top_skills,
                lambda s: rx.box(
                    s,
                    display="inline-flex",
                    padding=f"3px 10px",
                    background_color=t.BORDER,
                    color=t.BRAND,
                    font_size=t.TEXT_CAPTION,
                    font_weight=t.W_MEDIUM,
                    font_family=t.FONT_SANS,
                    border_radius=t.RADIUS_PILL,
                    border=f"1px solid {t.BORDER}",
                ),
            ),
            flex_wrap="wrap",
            gap=t.SPACE_2,
            flex="1",
            margin_bottom=t.SPACE_4,
        ),
        # Confidence bar
        rx.vstack(
            rx.hstack(
                rx.text("Confidence", font_size=t.TEXT_SMALL,
                        color=t.TEXT_SECONDARY, font_family=t.FONT_SANS),
                rx.text(
                    rx.cond(
                        cluster.avg_confidence > 1,
                        cluster.avg_confidence.to(int).to_string() + "%",
                        (cluster.avg_confidence * 100).to(int).to_string() + "%",
                    ),
                    font_size=t.TEXT_SMALL,
                    font_weight=t.W_SEMI,
                    color=t.BRAND,
                    font_family=t.FONT_MONO,
                ),
                justify="between", width="100%",
            ),
            rx.box(
                rx.box(
                    height="100%",
                    width=rx.cond(
                        cluster.avg_confidence > 1,
                        cluster.avg_confidence.to_string() + "%",
                        (cluster.avg_confidence * 100).to(int).to_string() + "%",
                    ),
                    background_color=t.BRAND,
                    border_radius=t.RADIUS_PILL,
                    transition="width 600ms cubic-bezier(0.4,0,0.2,1)",
                ),
                width="100%",
                height="6px",
                background_color=t.BORDER,
                border_radius=t.RADIUS_PILL,
                overflow="hidden",
            ),
            spacing="1", width="100%",
        ),
        # Card container
        position="relative",
        background_color=t.SURFACE,
        border=f"1px solid {t.BORDER}",
        border_radius=t.RADIUS_LG,
        padding=t.SPACE_5,
        padding_top=f"calc({t.SPACE_5} + 3px)",
        box_shadow=t.SHADOW_SM,
        display="flex",
        flex_direction="column",
        overflow="hidden",
        transition=t.TRANSITION_BASE,
        _hover={
            "box_shadow": t.SHADOW_MD,
            "border_color": t.BORDER_STRONG,
            "transform": "translateY(-2px)",
        },
    )
