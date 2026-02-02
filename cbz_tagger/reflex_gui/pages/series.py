"""Series page - displays table of tracked manga series."""

import reflex as rx

from cbz_tagger.reflex_gui.components.navbar import navbar
from cbz_tagger.reflex_gui.components.series_table import legend
from cbz_tagger.reflex_gui.components.series_table import series_table
from cbz_tagger.reflex_gui.states.series_state import SeriesState


def series_page() -> rx.Component:
    """Create the series page.

    Returns:
        Reflex component for the series page
    """
    return rx.box(
        navbar(),
        rx.container(
            rx.vstack(
                # Sidebar controls
                rx.hstack(
                    rx.button(
                        "Refresh Table",
                        on_click=SeriesState.refresh_table,
                        loading=SeriesState.is_loading,
                        color_scheme="blue",
                    ),
                    rx.button(
                        "Refresh Database",
                        on_click=SeriesState.refresh_database,
                        loading=SeriesState.is_loading,
                        color_scheme="green",
                    ),
                    spacing="4",
                ),
                # Column visibility toggles
                rx.hstack(
                    rx.switch(
                        "Entity ID",
                        checked=SeriesState.show_entity_id,
                        on_change=SeriesState.toggle_entity_id,
                    ),
                    rx.switch(
                        "Metadata Updated",
                        checked=SeriesState.show_metadata_updated,
                        on_change=SeriesState.toggle_metadata_updated,
                    ),
                    rx.switch(
                        "Plugin",
                        checked=SeriesState.show_plugin,
                        on_change=SeriesState.toggle_plugin,
                    ),
                    spacing="4",
                    wrap="wrap",
                ),
                # Series table
                series_table(),
                # Legend
                legend(),
                # Notification
                rx.cond(
                    SeriesState.show_notification,
                    rx.callout(
                        SeriesState.notification_message,
                        icon="info",
                        color_scheme=SeriesState.notification_severity,
                        on_click=SeriesState.clear_notification,
                    ),
                ),
                spacing="4",
                padding="2rem",
            ),
            max_width="1400px",
        ),
        on_mount=SeriesState.refresh_table,
    )
