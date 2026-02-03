"""Config page - display server configuration."""

import logging

import reflex as rx

from cbz_tagger.reflex_gui.components.navbar import navbar
from cbz_tagger.reflex_gui.states.config_state import ConfigState

logger = logging.getLogger()


def config_page() -> rx.Component:
    """Create the config page.

    Returns:
        Reflex component for the config page
    """
    return rx.box(
        navbar(),
        rx.container(
            rx.vstack(
                rx.heading("Server Configuration", size="8"),
                rx.cond(
                    ConfigState.is_loaded,
                    rx.vstack(
                        rx.hstack(
                            rx.text("Property", weight="bold", width="300px"),
                            rx.text("Value", weight="bold", width="600px"),
                            width="100%",
                            padding="0.5rem",
                            border_bottom="2px solid #e0e0e0",
                        ),
                        rx.foreach(
                            ConfigState.config_data,
                            lambda item: rx.hstack(
                                rx.text(item["property"], width="300px"),
                                rx.text(item["value"], width="600px"),
                                width="100%",
                                padding="0.5rem",
                                border_bottom="1px solid #f0f0f0",
                            ),
                        ),
                        width="100%",
                        border="1px solid #e0e0e0",
                        border_radius="8px",
                        overflow="hidden",
                    ),
                    rx.spinner(),
                ),
                spacing="4",
                padding="2rem",
            ),
            max_width="1400px",
        ),
        on_mount=ConfigState.load_config,
    )
