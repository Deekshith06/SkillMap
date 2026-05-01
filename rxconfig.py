import reflex as rx

config = rx.Config(
    app_name="skillmap",
    stylesheets=[
        "styles.css",
        "https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600&display=swap"
    ],
    plugins=[
        rx.plugins.SitemapPlugin(),
    ]
)