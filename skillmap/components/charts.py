"""charts.py — Recharts → rx.recharts wrappers for SkillMap."""

import reflex as rx

from skillmap.styles import theme as t


def skill_bar_chart(data: rx.Var, height: int = 380) -> rx.Component:
    """Horizontal bar chart for top skills."""
    return rx.recharts.bar_chart(
        rx.recharts.bar(
            data_key="count",
            fill=t.BRAND,
            radius=[0, 6, 6, 0],
            max_bar_size=28,
        ),
        rx.recharts.x_axis(type_="number", stroke=t.TEXT_SECONDARY),
        rx.recharts.y_axis(
            type_="category",
            data_key="skill",
            width=130,
            stroke=t.TEXT_SECONDARY,
        ),
        rx.recharts.graphing_tooltip(),
        data=data,
        layout="vertical",
        width="100%",
        height=height,
        margin={"top": 5, "right": 30, "left": 10, "bottom": 5},
    )


def cluster_pie_chart(data: rx.Var, total: rx.Var, height: int = 300) -> rx.Component:
    """Donut pie chart for cluster distribution with center total labels."""
    return rx.box(
        # The actual chart
        rx.recharts.pie_chart(
            rx.recharts.pie(
                rx.foreach(
                    data,
                    lambda _, i: rx.recharts.cell(
                        fill=rx.Var.create(t.ORANGE_PALETTE)[i % 10], stroke="none"
                    ),
                ),
                data=data,
                data_key="resume_count",
                name_key="name",
                cx="50%",
                cy="50%",
                inner_radius=70,
                outer_radius=110,
                padding_angle=2,
                stroke="none",
            ),
            rx.recharts.graphing_tooltip(),
            width="100%",
            height=height,
        ),
        # Center Overlay (Total Text)
        rx.vstack(
            rx.text("Total", font_size="13px", font_weight="600", color=t.SECONDARY),
            rx.text(
                total.to(str), font_size="24px", font_weight="800", color=t.DARK, margin_top="-6px"
            ),
            position="absolute",
            top="50%",
            left="50%",
            transform="translate(-50%, -50%)",
            align_items="center",
            justify_content="center",
            spacing="0",
        ),
        position="relative",
        width="100%",
        display="flex",
        justify_content="center",
        align_items="center",
    )


def radar_chart(data: rx.Var, height: int = 300) -> rx.Component:
    """Radar chart for skill domains."""
    return rx.recharts.radar_chart(
        rx.recharts.polar_grid(),
        rx.recharts.polar_angle_axis(data_key="domain"),
        rx.recharts.radar(
            data_key="confidence",
            stroke=t.BRAND,
            fill=t.BRAND,
            fill_opacity=0.3,
        ),
        rx.recharts.graphing_tooltip(),
        data=data,
        width="100%",
        height=height,
    )


def scatter_chart_umap(data: rx.Var, height: int = 450) -> rx.Component:
    """2D scatter chart for UMAP cluster positions."""
    return rx.recharts.scatter_chart(
        rx.recharts.scatter(
            data=data,
            fill=t.BRAND,
        ),
        rx.recharts.x_axis(data_key="x", type_="number", domain=["auto", "auto"]),
        rx.recharts.y_axis(data_key="y", type_="number", domain=["auto", "auto"]),
        rx.recharts.z_axis(data_key="count", range=[40, 400]),
        rx.recharts.graphing_tooltip(),
        rx.recharts.cartesian_grid(stroke_dasharray="3 3", opacity=0.15),
        width="100%",
        height=height,
    )
