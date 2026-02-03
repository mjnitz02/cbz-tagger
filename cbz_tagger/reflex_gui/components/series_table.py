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
        Reflex table component with series data
    """

    return rx.box(
        rx.vstack(
            # Header row
            rx.hstack(
                rx.text("Entity Name", weight="bold", width="500px"),
                rx.cond(
                    SeriesState.show_entity_id,
                    rx.text("Entity ID", weight="bold", width="500px"),
                    rx.fragment(),
                ),
                rx.text("Status", weight="bold", width="100px"),
                rx.text("Tracked", weight="bold", width="100px"),
                rx.text("Chapter", weight="bold", width="100px"),
                rx.text("Chapter Updated", weight="bold", width="200px"),
                rx.text("Metadata Updated", weight="bold", width="200px"),
                rx.cond(
                    SeriesState.show_metadata_updated,
                    rx.text("Metadata Updated", weight="bold", width="200px"),
                    rx.fragment(),
                ),
                rx.cond(
                    SeriesState.show_plugin,
                    rx.text("Plugin", weight="bold", width="100px"),
                    rx.fragment(),
                ),
                width="100%",
                padding="0.5rem",
                border_bottom="2px solid #e0e0e0",
                align="start",
            ),
            # Data rows
            rx.foreach(
                SeriesState.series_data,
                lambda item: rx.hstack(
                    rx.link(
                        item["entity_name"]["name"],
                        href=item["entity_name"]["link"],
                        width="500px",
                    ),
                    rx.cond(
                        SeriesState.show_entity_id,
                        rx.text(item["entity_id"], width="500px"),
                        rx.fragment(),
                    ),
                    rx.text(item["status"], width="100px"),
                    rx.text(item["tracked"], width="100px"),
                    rx.text(item["latest_chapter"], width="100px"),
                    rx.text(
                        item["chapter_date_display"]["text"],
                        width="200px",
                        color=item["chapter_date_display"]["color"],
                    ),
                    rx.cond(
                        SeriesState.show_metadata_updated,
                        rx.text(
                            item["updated_display"]["text"],
                            width="200px",
                            color=item["updated_display"]["color"],
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        SeriesState.show_plugin,
                        rx.link(
                            item["plugin"]["name"],
                            href=item["plugin"]["link"],
                            width="100px",
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                    padding="0.5rem",
                    border_bottom="1px solid #f0f0f0",
                    align="start",
                ),
            ),
            width="100%",
            border="1px solid #e0e0e0",
            border_radius="8px",
            overflow="auto",
            max_height="70vh",
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
