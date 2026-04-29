import reflex as rx
from .navbar import navbar

def page_layout(*children, **kwargs) -> rx.Component:
    """A layout component that wraps the page with the navbar."""
    return rx.box(
        navbar(),
        rx.box(
            *children,
            padding="40px 32px",
            max_width="1200px",
            margin="0 auto",
            **kwargs,
        ),
        bg="var(--bg-page)",
        min_height="100vh",
        font_family="var(--font)",
    )
