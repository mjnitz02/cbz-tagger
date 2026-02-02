"""Config page - display server configuration."""

import reflex as rx

from cbz_tagger.reflex_gui.components.navbar import navbar
from cbz_tagger.reflex_gui.states.config_state import ConfigState


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
                rx.data_table(
                    data=ConfigState.config_data,
                    columns=[
                        {"title": "Property", "accessorKey": "property", "id": "property"},
                        {"title": "Value", "accessorKey": "value", "id": "value"},
                    ],
                    search=False,
                    sort=False,
                    pagination=False,
                ),
                spacing="4",
                padding="2rem",
            ),
            max_width="1400px",
        ),
        on_mount=ConfigState.load_config,
    )
