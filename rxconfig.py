"""Reflex configuration for local and split Vercel/Render deployment."""

import reflex as rx

from skillmap.config.settings import get_settings

settings = get_settings()

config = rx.Config(
    app_name="skillmap",
    api_url=settings.api_url,
    deploy_url=settings.deploy_url,
    backend_host="0.0.0.0",
    cors_allowed_origins=list(settings.cors_allowed_origins),
    telemetry_enabled=False,
    state_manager_mode="memory",
    stylesheets=[
        "styles.css",
        "https://fonts.googleapis.com/css2?family=Lexend:wght@500;600;700&family=Source+Sans+3:wght@400;500;600;700&display=swap",
    ],
    plugins=[rx.plugins.SitemapPlugin()],
)
