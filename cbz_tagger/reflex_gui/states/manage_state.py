"""Manage state for adding, deleting, and managing series."""

import asyncio
import logging

from cbz_tagger.common.enums import Plugins
from cbz_tagger.entities.metadata_entity import MetadataEntity
from cbz_tagger.reflex_gui.states.base_state import BaseState

logger = logging.getLogger()


class ManageState(BaseState):
    """State for the manage page.

    Manages:
    - Add new series form and search
    - Delete series
    - Reset chapter tracking
    - Clean orphaned files
    """

    # Add Series form state
    add_search_term: str = ""
    add_series_options: list[str] = []
    add_series_value: str = ""
    add_name_options: list[str] = []
    add_name_value: str = ""
    add_backend_value: str = Plugins.MDX
    add_backend_id: str = ""
    add_mark_tracked: str = "No"  # "Yes", "No", "Disable Tracking"

    # Internal state for add series
    _meta_entries: list[MetadataEntity] = []

    # Manage Series form state
    manage_series_options: list[str] = []
    manage_series_value: str = ""
    manage_chapter_options: list[str] = []
    manage_chapter_value: str = ""

    # Internal state for manage series
    _manage_series_ids: list[tuple[str, str]] = []  # [(name, entity_id), ...]
    _manage_chapter_ids: list[tuple[str, str, str, str]] = []  # [(series_id, series_name, chapter_id, chapter_name)]

    # Loading states
    is_searching: bool = False
    is_adding: bool = False
    is_loading_series: bool = False
    is_deleting: bool = False
    is_resetting: bool = False
    is_cleaning: bool = False

    # Form enable/disable states
    add_button_enabled: bool = False
    delete_button_enabled: bool = False
    reset_button_enabled: bool = False

    async def search_series(self):
        """Search for series using MDX API."""
        if not self.add_search_term or len(self.add_search_term) == 0:
            self.notify("Please enter a name to search for", "warning")
            return

        self.is_searching = True
        self.add_button_enabled = False

        try:

            def _search():
                return MetadataEntity.from_server_url(query_params={"title": self.add_search_term})

            loop = asyncio.get_event_loop()
            self._meta_entries = await loop.run_in_executor(None, _search)

            # Format options for dropdown
            self.add_series_options = [
                f"{manga.title} ({manga.alt_title}) - {manga.created_at.year} - {manga.age_rating}"
                for manga in self._meta_entries
            ]

            if len(self.add_series_options) > 0:
                self.add_series_value = self.add_series_options[0]
                self.add_button_enabled = True
                # Trigger name refresh
                await self.update_series_names()
                self.notify(f"Found {len(self.add_series_options)} series", "success")
            else:
                self.notify("No series found", "warning")

        except Exception as e:
            logger.error("Error searching for series: %s", e)
            self.notify(f"Error searching: {e}", "error")
        finally:
            self.is_searching = False

    async def update_series_names(self):
        """Update available names when series selection changes."""
        if len(self._meta_entries) == 0:
            return

        try:
            entity_index = self.add_series_options.index(self.add_series_value)
            self.add_name_options = self._meta_entries[entity_index].all_titles
            if len(self.add_name_options) > 0:
                self.add_name_value = self.add_name_options[0]
        except (ValueError, IndexError) as e:
            logger.error("Error updating series names: %s", e)

    async def add_series(self):
        """Add a new series to the database."""
        if len(self._meta_entries) == 0:
            self.notify("Please search for a series first", "warning")
            return

        # Validate backend ID for non-MDX backends
        if self.add_backend_value != Plugins.MDX and len(self.add_backend_id) == 0:
            self.notify("Please enter a backend id for non-MDX backends", "warning")
            return

        self.is_adding = True
        self.add_button_enabled = False

        try:
            entity_index = self.add_series_options.index(self.add_series_value)
            entity = self._meta_entries[entity_index]
            entity_id = entity.entity_id
            entity_name = self.add_name_value

            # Prepare backend config
            backend = None
            if self.add_backend_value != Plugins.MDX:
                backend = {
                    "plugin_type": self.add_backend_value,
                    "plugin_id": self.add_backend_id,
                }

            mark_all_tracked = self.add_mark_tracked == "Yes"
            enable_tracking = self.add_mark_tracked != "Disable Tracking"

            self.notify("Adding new series... please wait", "info")

            def _add_series():
                scanner = self.get_scanner()
                scanner.entity_database.add_entity(
                    entity_name,
                    entity_id,
                    manga_name=None,
                    backend=backend,
                    update=True,
                    track=enable_tracking,
                    mark_as_tracked=mark_all_tracked,
                )
                return scanner

            await self.run_sync_operation(_add_series)
            self.notify(f"Successfully added {entity_name}!", "success")

            # Reset form
            await self.reset_add_form()

        except Exception as e:
            logger.error("Error adding series: %s", e)
            self.notify(f"Error adding series: {e}", "error")
        finally:
            self.is_adding = False

    async def reset_add_form(self):
        """Reset the add series form to initial state."""
        self._meta_entries = []
        self.add_search_term = ""
        self.add_series_options = []
        self.add_series_value = ""
        self.add_name_options = []
        self.add_name_value = ""
        self.add_backend_value = Plugins.MDX
        self.add_backend_id = ""
        self.add_mark_tracked = "No"
        self.add_button_enabled = False

    async def load_series_list(self):
        """Load the list of series for management."""
        self.is_loading_series = True

        try:

            def _load():
                scanner = self.get_scanner()
                scanner.reload_scanner()
                return list(scanner.entity_database.entity_map.items())

            loop = asyncio.get_event_loop()
            self._manage_series_ids = await loop.run_in_executor(None, _load)

            # Format options
            self.manage_series_options = [f"{name} ({entity_id})" for name, entity_id in self._manage_series_ids]

            if len(self.manage_series_options) > 0:
                self.manage_series_value = self.manage_series_options[0]
                self.delete_button_enabled = True
                self.reset_button_enabled = True
                # Load chapters for first series
                await self.load_chapters()
                self.notify("Series list refreshed", "success")
            else:
                self.manage_series_options = ["No series available"]
                self.manage_series_value = "No series available"
                self.delete_button_enabled = False
                self.reset_button_enabled = False
                self.manage_chapter_options = ["No series selected"]
                self.manage_chapter_value = "No series selected"

        except Exception as e:
            logger.error("Error loading series list: %s", e)
            self.notify(f"Error loading series: {e}", "error")
        finally:
            self.is_loading_series = False

    async def load_chapters(self):
        """Load chapters for the selected series."""
        if len(self._manage_series_ids) == 0:
            return

        try:
            entity_index = self.manage_series_options.index(self.manage_series_value)
            selected_series_name, selected_series_id = self._manage_series_ids[entity_index]

            def _load_chapters():
                scanner = self.get_scanner()
                chapters = scanner.entity_database.chapters.get(selected_series_id, [])
                return chapters

            loop = asyncio.get_event_loop()
            chapters = await loop.run_in_executor(None, _load_chapters)

            self._manage_chapter_ids = [
                (selected_series_id, selected_series_name, chapter.entity_id, f"Chapter {chapter.chapter_number}")
                for chapter in (chapters if chapters is not None else [])
            ]

            self.manage_chapter_options = [chapter_name for _, _, _, chapter_name in self._manage_chapter_ids]

            if len(self.manage_chapter_options) > 0:
                self.manage_chapter_value = self.manage_chapter_options[0]
            else:
                self.manage_chapter_options = ["No chapters available"]
                self.manage_chapter_value = "No chapters available"

        except (ValueError, IndexError) as e:
            logger.error("Error loading chapters: %s", e)

    async def delete_series(self):
        """Delete the selected series."""
        if len(self._manage_series_ids) == 0:
            return

        self.is_deleting = True
        self.delete_button_enabled = False

        try:
            entity_index = self.manage_series_options.index(self.manage_series_value)
            entity_name_to_remove, entity_id_to_remove = self._manage_series_ids[entity_index]

            def _delete():
                scanner = self.get_scanner()
                scanner.entity_database.delete_entity_id(entity_id_to_remove, entity_name_to_remove)

            await self.run_sync_operation(_delete)
            self.notify(f"Removed {entity_name_to_remove} from database", "success")

            # Refresh series list
            await self.load_series_list()

        except Exception as e:
            logger.error("Error deleting series: %s", e)
            self.notify(f"Error deleting series: {e}", "error")
        finally:
            self.is_deleting = False

    async def reset_chapter_tracking(self):
        """Reset tracking for the selected chapter."""
        if len(self._manage_chapter_ids) == 0:
            return

        self.is_resetting = True
        self.reset_button_enabled = False

        try:
            chapter_index = self.manage_chapter_options.index(self.manage_chapter_value)
            entity_id, entity_name, chapter_id, chapter_name = self._manage_chapter_ids[chapter_index]

            def _reset():
                scanner = self.get_scanner()
                scanner.entity_database.delete_chapter_entity_id_from_downloaded_chapters(entity_id, chapter_id)

            await self.run_sync_operation(_reset)
            self.notify(f"Reset tracking for {chapter_name} from {entity_name}", "success")

            # Refresh chapters
            await self.load_chapters()

        except Exception as e:
            logger.error("Error resetting chapter: %s", e)
            self.notify(f"Error resetting chapter: {e}", "error")
        finally:
            self.is_resetting = False
            self.reset_button_enabled = True

    async def clean_orphaned_files(self):
        """Clean orphaned cover files from storage."""
        self.is_cleaning = True

        try:
            self.notify("Removing orphaned files...", "info")

            def _clean():
                scanner = self.get_scanner()
                scanner.entity_database.remove_orphaned_covers()

            await self.run_sync_operation(_clean)
            self.notify("Orphaned files removed successfully", "success")

        except Exception as e:
            logger.error("Error cleaning files: %s", e)
            self.notify(f"Error cleaning files: {e}", "error")
        finally:
            self.is_cleaning = False
