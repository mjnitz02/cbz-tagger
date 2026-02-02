"""Manage page - add, delete, and manage series."""

import reflex as rx

from cbz_tagger.common.enums import Plugins
from cbz_tagger.reflex_gui.components.navbar import navbar
from cbz_tagger.reflex_gui.states.manage_state import ManageState


def add_series_section() -> rx.Component:
    """Create the add series section.

    Returns:
        Reflex component for adding new series
    """
    return rx.vstack(
        rx.divider(),
        rx.heading("Add Series", size="6"),
        rx.divider(),
        # Search input
        rx.input(
            placeholder="Series Name",
            value=ManageState.add_search_term,
            on_change=ManageState.set_add_search_term,
            width="66%",
        ),
        rx.button(
            "Search for New Series",
            on_click=ManageState.search_series,
            loading=ManageState.is_searching,
            # color_scheme="blue",
        ),
        # Series selector
        rx.select(
            ManageState.add_series_options,
            placeholder="Select a series (type to filter)",
            value=ManageState.add_series_value,
            on_change=ManageState.handle_add_series_select,
            width="66%",
        ),
        # Name selector
        rx.select(
            ManageState.add_name_options,
            placeholder="Select the name of the series (type to filter)",
            value=ManageState.add_name_value,
            on_change=ManageState.set_add_name_value,
            width="66%",
        ),
        # Backend selector
        rx.select(
            [Plugins.MDX, Plugins.WBC, Plugins.KAL],
            placeholder="Select a series backend (Default: MDX)",
            value=ManageState.add_backend_value,
            on_change=ManageState.set_add_backend_value,
            width="66%",
        ),
        # Backend ID input
        rx.input(
            placeholder="Backend id for the series (Only for non-MDX backends)",
            value=ManageState.add_backend_id,
            on_change=ManageState.set_add_backend_id,
            width="66%",
        ),
        # Mark tracked radio
        rx.vstack(
            rx.text("Mark all chapters as tracked?"),
            rx.radio_group(
                ["Yes", "No", "Disable Tracking"],
                value=ManageState.add_mark_tracked,
                on_change=ManageState.set_add_mark_tracked,
                direction="row",
            ),
            align="start",
            width="66%",
        ),
        # Add button
        rx.hstack(
            rx.button(
                "Add New Series",
                on_click=ManageState.add_series,
                loading=ManageState.is_adding,
                disabled=ManageState.add_button_enabled == False,  # noqa: E712
                # color_scheme="green",
            ),
            rx.cond(
                ManageState.is_adding,
                rx.text("Adding new series...", color="blue"),
            ),
        ),
        spacing="4",
        align="start",
        width="100%",
    )


def manage_series_section() -> rx.Component:
    """Create the manage series section.

    Returns:
        Reflex component for managing existing series
    """
    return rx.vstack(
        rx.divider(),
        rx.heading("Manage Series", size="6"),
        rx.divider(),
        # Series selector
        rx.select(
            ManageState.manage_series_options,
            placeholder="Select a series (type to filter)",
            value=ManageState.manage_series_value,
            on_change=ManageState.handle_manage_series_select,
            width="66%",
        ),
        # Chapter selector
        rx.select(
            ManageState.manage_chapter_options,
            placeholder="Select a chapter (type to filter)",
            value=ManageState.manage_chapter_value,
            on_change=ManageState.set_manage_chapter_value,
            width="66%",
        ),
        # Action buttons
        rx.hstack(
            rx.button(
                "Refresh Series List",
                on_click=ManageState.load_series_list,
                loading=ManageState.is_loading_series,
                # color_scheme="blue",
            ),
            rx.button(
                "Delete Selected Series",
                on_click=ManageState.delete_series,
                loading=ManageState.is_deleting,
                disabled=ManageState.delete_button_enabled == False,  # noqa: E712
                # color_scheme="red",
            ),
            rx.button(
                "Reset Tracked Chapter",
                on_click=ManageState.reset_chapter_tracking,
                loading=ManageState.is_resetting,
                disabled=ManageState.reset_button_enabled == False,  # noqa: E712
                # color_scheme="orange",
            ),
            spacing="4",
            wrap="wrap",
        ),
        # Clean orphaned files button
        rx.button(
            "Clean Orphaned Files",
            on_click=ManageState.clean_orphaned_files,
            loading=ManageState.is_cleaning,
            # color_scheme="purple",
        ),
        spacing="4",
        align="start",
        width="100%",
    )


def manage_page() -> rx.Component:
    """Create the manage page.

    Returns:
        Reflex component for the manage page
    """
    return rx.box(
        navbar(),
        rx.container(
            rx.vstack(
                add_series_section(),
                manage_series_section(),
                # Notification
                rx.cond(
                    ManageState.show_notification,
                    rx.callout(
                        ManageState.notification_message,
                        icon="info",
                        color_scheme=ManageState.notification_severity,
                        on_click=ManageState.clear_notification,
                    ),
                ),
                spacing="6",
                padding="2rem",
            ),
            max_width="1400px",
        ),
    )
