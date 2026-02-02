"""Logs page - display server logs."""

import reflex as rx

from cbz_tagger.reflex_gui.components.navbar import navbar
from cbz_tagger.reflex_gui.states.log_state import LogState


def logs_page() -> rx.Component:
    """Create the logs page.

    Returns:
        Reflex component for the logs page
    """
    return rx.box(
        navbar(),
        rx.container(
            rx.vstack(
                rx.heading("Server Logs", size="8"),
                # Controls
                rx.hstack(
                    rx.button(
                        "Refresh Logs",
                        on_click=LogState.refresh_logs,
                        loading=LogState.is_loading,
                        # color_scheme="blue",
                    ),
                    rx.button(
                        "Clear Logs",
                        on_click=LogState.clear_logs,
                        # color_scheme="red",
                    ),
                    rx.switch(
                        "Auto-refresh",
                        checked=LogState.is_auto_refresh,
                        on_change=LogState.toggle_auto_refresh,
                    ),
                    spacing="4",
                ),
                # Log viewer
                rx.box(
                    rx.scroll_area(
                        rx.vstack(
                            rx.foreach(
                                LogState.log_lines,
                                lambda line: rx.text(
                                    line,
                                    font_family="monospace",
                                    font_size="0.875rem",
                                    white_space="pre-wrap",
                                    word_break="break-all",
                                    color="#222",
                                ),
                            ),
                            spacing="1",
                            align="start",
                        ),
                        height="70vh",
                        width="100%",
                    ),
                    border="1px solid #e0e0e0",
                    border_radius="8px",
                    padding="1rem",
                    background_color="#f5f5f5",
                    width="100%",
                ),
                # Notification
                rx.cond(
                    LogState.show_notification,
                    rx.callout(
                        LogState.notification_message,
                        icon="info",
                        color_scheme=LogState.notification_severity,
                        on_click=LogState.clear_notification,
                    ),
                ),
                spacing="4",
                padding="2rem",
            ),
            max_width="1400px",
        ),
        on_mount=LogState.refresh_logs,
    )
