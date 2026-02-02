"""Series state for managing the series table."""

import logging
from datetime import datetime

from cbz_tagger.common.enums import Emoji
from cbz_tagger.reflex_gui.states.base_state import BaseState

logger = logging.getLogger()


class SeriesState(BaseState):
    """State for the series page.

    Manages:
    - Series table data
    - Column visibility toggles
    - Refresh operations
    """

    # Table data
    series_data: list[dict] = []

    # Column visibility (default hidden columns)
    show_entity_id: bool = False
    show_metadata_updated: bool = False
    show_plugin: bool = False

    # Loading state
    is_loading: bool = False

    async def refresh_table(self):
        """Refresh the series table data.

        Reloads scanner and updates table with formatted data.
        """
        logger.debug("Refreshing series table")
        self.is_loading = True

        try:

            def _load_data():
                scanner = self.get_scanner()
                scanner.reload_scanner()
                state = scanner.to_state()

                # Format data for display
                formatted_state = []
                for item in state:
                    # Truncate long entity names
                    if len(item["entity_name"]) > 50:
                        item["entity_name_display"] = item["entity_name"][:50] + "..."
                    else:
                        item["entity_name_display"] = item["entity_name"]

                    # Add formatted dates
                    if item.get("updated"):
                        item["updated_display"] = self._format_date(item["updated"])
                    if item.get("latest_chapter_date"):
                        item["chapter_date_display"] = self._format_date(item["latest_chapter_date"])

                    formatted_state.append(item)

                return formatted_state

            # Run in executor
            self.series_data = await self.run_sync_operation(_load_data)
            logger.debug("Series table refreshed with %d items", len(self.series_data))

        except Exception as e:
            logger.error("Error refreshing table: %s", e)
            self.notify(f"Error refreshing table: {e}", "error")
        finally:
            self.is_loading = False

    async def refresh_database(self):
        """Perform full database refresh (scan for new files and update metadata).

        This is a long-running operation that should show progress to user.
        """
        if self.is_database_locked():
            self.notify("Database currently in use, please wait...", "warning")
            return

        self.notify("Refreshing database... please wait", "info")
        self.is_loading = True

        try:

            def _refresh():
                scanner = self.get_scanner()
                scanner.run()
                return scanner

            await self.run_sync_operation(_refresh)
            self.notify("Database refreshed successfully", "success")

            # Refresh table after database refresh
            await self.refresh_table()

        except Exception as e:
            logger.error("Error refreshing database: %s", e)
            self.notify(f"Error refreshing database: {e}", "error")
        finally:
            self.is_loading = False

    def toggle_entity_id(self):
        """Toggle Entity ID column visibility."""
        self.show_entity_id = not self.show_entity_id

    def toggle_metadata_updated(self):
        """Toggle Metadata Updated column visibility."""
        self.show_metadata_updated = not self.show_metadata_updated

    def toggle_plugin(self):
        """Toggle Plugin column visibility."""
        self.show_plugin = not self.show_plugin

    @staticmethod
    def _format_date(date_str: str) -> dict:
        """Format date string with color coding based on age.

        Args:
            date_str: ISO format date string

        Returns:
            Dict with 'text' and 'color' keys
        """
        try:
            date = datetime.fromisoformat(date_str)
            now = datetime.now()
            days_old = (now - date).days

            # Determine color based on age
            if days_old < 45:
                color = "green"
            elif days_old < 90:
                color = "orange"
            else:
                color = "red"

            # Format date for display (YYYY-MM-DD HH:MM)
            formatted = date.strftime("%Y-%m-%d %H:%M")

            return {"text": formatted, "color": color}

        except (ValueError, TypeError):
            return {"text": "Unknown", "color": "gray"}

    @staticmethod
    def get_status_emoji(status: str) -> str:
        """Get emoji for series status.

        Args:
            status: Status string from database

        Returns:
            Emoji character
        """
        status_lower = status.lower() if status else ""
        if status_lower == "completed":
            return Emoji.CHECK_GREEN
        elif status_lower == "ongoing":
            return Emoji.CIRCLE_GREEN
        elif status_lower == "hiatus":
            return Emoji.CIRCLE_YELLOW
        elif status_lower == "cancelled":
            return Emoji.CIRCLE_RED
        else:
            return Emoji.CIRCLE_BROWN

    @staticmethod
    def get_tracked_emoji(tracked: str) -> str:
        """Get emoji for tracked status.

        Args:
            tracked: Tracked status string

        Returns:
            Emoji character
        """
        if tracked == "True":
            return Emoji.CIRCLE_GREEN
        else:
            return Emoji.CIRCLE_BROWN
