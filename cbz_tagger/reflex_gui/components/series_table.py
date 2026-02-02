"""Series table component."""

import reflex as rx

from cbz_tagger.common.enums import Emoji
from cbz_tagger.reflex_gui.states.series_state import SeriesState


def date_badge(date_data: dict) -> rx.Component:
    """Create a colored badge for date display.

    Args:
        date_data: Dict with 'text' and 'color' keys

    Returns:
        Reflex badge component
    """
    return rx.badge(
        date_data.get("text", "Unknown"),
        color_scheme=date_data.get("color", "gray"),
    )


def series_table() -> rx.Component:
    """Create the series data table.

    Returns:
        Reflex data table component with series data
    """
    return rx.box(
        rx.data_table(
            data=SeriesState.series_data,
            columns=[
                {
                    "title": "Entity Name",
                    "accessorKey": "entity_name_display",
                    "id": "entity_name_display",
                },
                {
                    "title": "Entity ID",
                    "accessorKey": "entity_id",
                    "id": "entity_id",
                    "show": SeriesState.show_entity_id,
                },
                {
                    "title": "Status",
                    "accessorKey": "status",
                    "id": "status",
                },
                {
                    "title": "Tracked",
                    "accessorKey": "tracked",
                    "id": "tracked",
                },
                {
                    "title": "Chapter",
                    "accessorKey": "latest_chapter",
                    "id": "latest_chapter",
                },
                {
                    "title": "Chapter Updated",
                    "accessorKey": "latest_chapter_date",
                    "id": "latest_chapter_date",
                },
                {
                    "title": "Metadata Updated",
                    "accessorKey": "updated",
                    "id": "updated",
                    "show": SeriesState.show_metadata_updated,
                },
                {
                    "title": "Plugin",
                    "accessorKey": "plugin",
                    "id": "plugin",
                    "show": SeriesState.show_plugin,
                },
            ],
            search=True,
            sort=True,
            pagination=True,
        ),
        width="100%",
    )


def legend() -> rx.Component:
    """Create the legend for status and date indicators.

    Returns:
        Reflex component with legend items
    """
    return rx.vstack(
        rx.hstack(
            rx.text(f"{Emoji.CHECK_GREEN} Completed"),
            rx.text(f"{Emoji.CIRCLE_GREEN} Ongoing/Tracked"),
            rx.text(f"{Emoji.CIRCLE_BROWN} Not Tracked"),
            rx.text(f"{Emoji.CIRCLE_YELLOW} Hiatus"),
            rx.text(f"{Emoji.CIRCLE_RED} Cancelled"),
            spacing="4",
            wrap="wrap",
        ),
        rx.hstack(
            rx.text(f"{Emoji.SQUARE_GREEN} Updated < 45d"),
            rx.text(f"{Emoji.SQUARE_ORANGE} Updated 45 - 90d"),
            rx.text(f"{Emoji.SQUARE_RED} Updated > 90d"),
            rx.text(f"{Emoji.QUESTION_MARK} Unknown"),
            spacing="4",
            wrap="wrap",
        ),
        spacing="2",
        align="start",
    )
