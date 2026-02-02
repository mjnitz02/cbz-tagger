"""Reflex configuration file."""

import reflex as rx

config = rx.Config(
    app_name="cbz_tagger",
    api_url="http://0.0.0.0:8080",
    frontend_port=3000,
    backend_port=8080,
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"],
)
