import asyncio
import logging
from datetime import datetime

import httpx
from nicegui import ui

from cbz_tagger.common.enums import Emoji
from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.env import AppEnv
from cbz_tagger.gui.elements.config_table import config_table
from cbz_tagger.gui.elements.series_table import series_table
from cbz_tagger.gui.elements.ui_logger import ui_logger

logger = logging.getLogger()


def notify_and_log(msg):
    """Helper to notify user and log message."""
    ui.notify(msg)
    logger.info("%s %s", datetime.now(), msg)


class SimpleGui:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        logger.debug("Starting GUI")
        self.env = AppEnv()
        self.first_scan = True
        self.scanning_state = False
        self.api_base_url = api_base_url
        self.gui_elements = {}

        self.meta_entries = []
        self.meta_choices = []
        self.manage_series_ids = []
        self.manage_series_names = []
        self.manage_chapter_names = []
        self.manage_chapter_ids = []

        self.initialize_gui()
        self.initialize()

    def initialize_gui(self):
        ui.add_head_html('<link rel="apple-touch-icon" href="static/apple-touch-icon.png">')
        ui.page_title("CBZ Tagger")
        ui.colors(primary="#2F4F4F")

        with ui.left_drawer().style("background-color: #bfd9d9").props("width=225") as left_drawer:
            ui.button("Refresh Table", on_click=self.refresh_table)
            ui.button("Refresh Database", on_click=self.refresh_database)

        with ui.header().classes(replace="row items-center"):
            # pylint: disable=unnecessary-lambda
            ui.button(on_click=lambda: left_drawer.toggle(), icon="menu").props("flat color=white")
            ui.html(f"<h2><strong>CBZ Tagger {self.env.VERSION}</strong></h2>")
            ui.space()
            with ui.tabs() as tabs:
                ui.tab("Series")
                ui.tab("Manage")
                ui.tab("Config")
                ui.tab("Log")
            ui.space()

        with ui.tab_panels(tabs, value="Series").classes("w-full"):
            with ui.tab_panel("Series"):
                with ui.row():
                    for table_columns in ["Entity ID", "Metadata Updated", "Plugin"]:
                        # noinspection PyUnresolvedReferences
                        ui.switch(
                            table_columns, value=False, on_change=lambda e, column=table_columns: self.toggle(column)
                        )
                self.gui_elements["table_series"] = series_table()
                with ui.row():
                    ui.label(f"{Emoji.CHECK_GREEN} Completed")
                    ui.label(f"{Emoji.CIRCLE_GREEN} Ongoing/Tracked")
                    ui.label(f"{Emoji.CIRCLE_BROWN} Not Tracked")
                    ui.label(f"{Emoji.CIRCLE_YELLOW} Hiatus")
                    ui.label(f"{Emoji.CIRCLE_RED} Cancelled")
                with ui.row():
                    ui.label(f"{Emoji.SQUARE_GREEN} Updated < 45d")
                    ui.label(f"{Emoji.SQUARE_ORANGE} Updated 45 - 90d")
                    ui.label(f"{Emoji.SQUARE_RED} Updated > 90d")
                    ui.label(f"{Emoji.QUESTION_MARK} Unknown")
            with ui.tab_panel("Manage"):
                ui.separator()
                ui.markdown("#### Add Series")
                ui.separator()
                self.gui_elements["add_search"] = ui.button(
                    "Search for New Series", on_click=self.refresh_series_search
                )
                self.gui_elements["input_box_add_series"] = ui.input(
                    "Please enter the name of a series to search for", placeholder="Series Name"
                ).classes("w-2/3")
                self.gui_elements["selector_add_series"] = ui.select(
                    label="Select a series (type to filter)",
                    options=["Please search for a series"],
                    with_input=True,
                    value="Please search for a series",
                    on_change=self.refresh_series_names,
                ).classes("w-2/3")
                self.gui_elements["selector_add_name"] = ui.select(
                    label="Select the name of the series (type to filter)",
                    options=["Please search for a series"],
                    with_input=True,
                    value="Please search for a series",
                ).classes("w-2/3")
                self.gui_elements["selector_add_backend"] = ui.select(
                    label="Select a series backend (Default: MDX)", options=Plugins.all(), value=Plugins.MDX
                ).classes("w-2/3")
                self.gui_elements["input_box_add_backend"] = ui.input(
                    "Backend id for the series (Only for non-MDX backends)",
                    placeholder="Enter the backend id for the series",
                ).classes("w-2/3")
                ui.label("Mark all chapters as tracked?")
                self.gui_elements["radio_add_mark_all_tracked"] = (
                    ui.radio(["Yes", "No", "Disable Tracking"], value="No").classes("w-2/3").props("inline")
                )
                with ui.row():
                    self.gui_elements["add_new"] = ui.button("Add New Series", on_click=self.add_new_series)
                    self.gui_elements["add_new"].disable()
                    self.gui_elements["spinner_add"] = ui.spinner()
                    self.gui_elements["spinner_add"].set_visibility(False)
                    self.gui_elements["spinner_add_label"] = ui.label("Adding new series...")
                    self.gui_elements["spinner_add_label"].set_visibility(False)

                ui.separator()
                ui.markdown("#### Manage Series")
                ui.separator()
                self.gui_elements["selector_manage_series"] = ui.select(
                    label="Select a series (type to filter)",
                    options=["Please refresh series list"],
                    with_input=True,
                    value="Please refresh series list",
                    on_change=self.refresh_manage_series_chapters,
                ).classes("w-2/3")
                self.gui_elements["selector_manage_chapters"] = ui.select(
                    label="Select a chapter (type to filter)",
                    options=["Please select a series first"],
                    with_input=True,
                    value="Please select a series first",
                ).classes("w-2/3")
                with ui.row():
                    self.gui_elements["manage_chapter_delete"] = ui.button(
                        "Refresh Series List", on_click=self.refresh_manage_series
                    )
                    self.gui_elements["manage_series_delete"] = ui.button(
                        "Delete Selected Series", on_click=self.delete_series
                    )
                    self.gui_elements["manage_series_delete"].disable()
                    self.gui_elements["manage_chapter_delete"] = ui.button(
                        "Reset Tracked Chapter", on_click=self.delete_chapter_tracking
                    )
                    self.gui_elements["manage_chapter_delete"].disable()
                with ui.row():
                    self.gui_elements["delete_clean"] = ui.button(
                        "Clean Orphaned Files", on_click=self.clean_orphaned_files
                    )

            with ui.tab_panel("Config"):
                ui.label("Server Configuration")
                self.gui_elements["table_config"] = config_table()
            with ui.tab_panel("Log"):
                ui.label("Server Logs")
                self.gui_elements["logger"] = ui_logger()
                ui.chip("Clear", icon="delete", color="red", on_click=self.clear_log)

    def clear_log(self):
        self.gui_elements["logger"].clear()
        logger.info("Log file cleared. %s", datetime.now())

    def initialize(self):
        logger.info("proxy_url: %s", self.env.PROXY_URL)
        logger.info("UI initialized with API base URL: %s", self.api_base_url)
        # Timer is now handled by the backend scheduler, but we still refresh the UI periodically
        if self.env.TIMER_DELAY > 0:
            logger.info("UI refresh timer started with delay: %s", self.env.TIMER_DELAY)
            self.gui_elements["timer_scanner"] = ui.timer(self.env.TIMER_DELAY, self.refresh_table)
        self.refresh_table()

    async def api_request(self, method: str, endpoint: str, **kwargs):
        """Make an HTTP request to the API."""
        url = f"{self.api_base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

    def can_use_database(self):
        if self.scanning_state:
            notify_and_log("Operation in progress, please wait...")
            return False
        return True

    def lock_database(self):
        self.scanning_state = True

    def unlock_database(self):
        self.scanning_state = False

    def toggle(self, column: str) -> None:
        column_index = [e["label"] for e in self.gui_elements["table_series"].columns].index(column)
        column = self.gui_elements["table_series"].columns[column_index]
        visible = not column.get("classes", "") == ""
        column["classes"] = "" if visible else "hidden"
        column["headerClasses"] = "" if visible else "hidden"
        self.gui_elements["table_series"].update()

    def refresh_series_search(self):
        search_term = self.gui_elements["input_box_add_series"].value
        if len(search_term) == 0:
            notify_and_log("Please enter a name to search for")
            return

        async def search():
            try:
                response = await self.api_request("POST", "/entities/search", json={"search_term": search_term})
                self.meta_entries = response["results"]
                self.meta_choices = [entry["display_name"] for entry in self.meta_entries]

                if len(self.meta_choices) > 0:
                    self.gui_elements["selector_add_series"].options = self.meta_choices
                    self.gui_elements["selector_add_series"].value = self.meta_choices[0]
                    self.gui_elements["add_new"].enable()
                else:
                    notify_and_log("No series found")
            except Exception as e:
                logger.error("Error searching for series: %s", str(e))
                notify_and_log(f"Error searching for series: {str(e)}")

        asyncio.create_task(search())

    def refresh_series_names(self):
        if len(self.meta_entries) == 0:
            return
        entity_index = self.meta_choices.index(self.gui_elements["selector_add_series"].value)
        self.gui_elements["selector_add_name"].options = self.meta_entries[entity_index]["all_titles"]
        self.gui_elements["selector_add_name"].value = self.meta_entries[entity_index]["all_titles"][0]

    def refresh_manage_series(self):
        async def fetch():
            try:
                response = await self.api_request("GET", "/entities/managed")
                series_list = response["series"]
                self.manage_series_ids = [(item["entity_name"], item["entity_id"]) for item in series_list]
                self.manage_series_names = [item["display_name"] for item in series_list]

                if len(self.manage_series_names) == 0:
                    self.gui_elements["selector_manage_series"].options = ["Please refresh series list"]
                    self.gui_elements["manage_series_delete"].disable()
                    self.gui_elements["selector_manage_chapters"].options = ["Please refresh series list"]
                    self.gui_elements["manage_chapter_delete"].disable()
                else:
                    self.gui_elements["selector_manage_series"].options = self.manage_series_names
                    self.gui_elements["manage_series_delete"].enable()
                    self.gui_elements["manage_chapter_delete"].enable()
                self.gui_elements["selector_manage_series"].value = self.gui_elements["selector_manage_series"].options[
                    0
                ]
            except Exception as e:
                logger.error("Error refreshing series list: %s", str(e))
                notify_and_log(f"Error refreshing series list: {str(e)}")

        asyncio.create_task(fetch())

    def refresh_manage_series_chapters(self):
        if len(self.manage_series_ids) == 0:
            return

        async def fetch():
            try:
                entity_index = self.manage_series_names.index(self.gui_elements["selector_manage_series"].value)
                selected_series_name, selected_series_id = self.manage_series_ids[entity_index]

                response = await self.api_request("GET", f"/entities/managed/{selected_series_id}/chapters")
                chapters = response["chapters"]

                self.manage_chapter_ids = [
                    (selected_series_id, selected_series_name, chapter["chapter_id"], chapter["chapter_name"])
                    for chapter in chapters
                ]
                self.manage_chapter_names = [chapter["chapter_name"] for chapter in chapters]

                if len(self.manage_chapter_ids) > 0:
                    self.gui_elements["selector_manage_chapters"].options = self.manage_chapter_names
                    self.gui_elements["selector_manage_chapters"].value = self.manage_chapter_names[0]
            except Exception as e:
                logger.error("Error refreshing chapters: %s", str(e))
                notify_and_log(f"Error refreshing chapters: {str(e)}")

        asyncio.create_task(fetch())

    def refresh_table(self):
        logger.debug("Refreshing series table")

        async def fetch():
            try:
                response = await self.api_request("GET", "/state/series")
                state = response["items"]

                formatted_state = []
                for item in state:
                    if len(item.get("entity_name", "")) > 50:
                        item["entity_name"] = item["entity_name"][:50] + "..."
                    formatted_state.append(item)

                self.gui_elements["table_series"].rows = formatted_state
                logger.debug("Series GUI Refreshed")
            except Exception as e:
                logger.error("Error refreshing table: %s", str(e))

        # Ensure the event loop is running
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(fetch())
        except RuntimeError:
            asyncio.run(fetch())

    async def add_new_series(self):
        if not self.can_use_database():
            return

        self.lock_database()
        self.gui_elements["spinner_add"].set_visibility(True)
        self.gui_elements["spinner_add_label"].set_visibility(True)
        self.gui_elements["add_new"].disable()

        try:
            entity_index = self.meta_choices.index(self.gui_elements["selector_add_series"].value)
            entity = self.meta_entries[entity_index]
            entity_id = entity["entity_id"]
            entity_name = self.gui_elements["selector_add_name"].value

            if (
                self.gui_elements["selector_add_backend"].value != Plugins.MDX
                and len(self.gui_elements["input_box_add_backend"].value) == 0
            ):
                notify_and_log("Please enter a backend id for non-MDX backends")
                return

            backend_id = None
            if self.gui_elements["selector_add_backend"].value != Plugins.MDX:
                backend_id = self.gui_elements["input_box_add_backend"].value

            mark_all_tracked = self.gui_elements["radio_add_mark_all_tracked"].value == "Yes"
            enable_tracking = self.gui_elements["radio_add_mark_all_tracked"].value != "Disable Tracking"

            notify_and_log("Adding new series... please wait")

            await self.api_request(
                "POST",
                "/entities/add",
                json={
                    "entity_id": entity_id,
                    "entity_name": entity_name,
                    "backend_plugin": self.gui_elements["selector_add_backend"].value,
                    "backend_id": backend_id,
                    "mark_all_tracked": mark_all_tracked,
                    "enable_tracking": enable_tracking,
                },
            )

            notify_and_log("New series added!")

            # Reset the Add New Series form
            self.meta_entries = []
            self.meta_choices = []
            self.gui_elements["input_box_add_series"].value = ""
            self.gui_elements["selector_add_series"].options = ["Please refresh series list"]
            self.gui_elements["selector_add_series"].value = self.gui_elements["selector_add_series"].options[0]
            self.gui_elements["selector_add_name"].options = ["Please refresh series list"]
            self.gui_elements["selector_add_name"].value = self.gui_elements["selector_add_name"].options[0]
            self.gui_elements["selector_add_backend"].value = Plugins.MDX
            self.gui_elements["input_box_add_backend"].value = ""
            self.gui_elements["radio_add_mark_all_tracked"].value = "No"

            # Refresh table
            self.refresh_table()
        except Exception as e:
            logger.error("Error adding series: %s", str(e))
            notify_and_log(f"Error adding series: {str(e)}")
        finally:
            self.gui_elements["spinner_add"].set_visibility(False)
            self.gui_elements["spinner_add_label"].set_visibility(False)
            self.unlock_database()

    async def delete_series(self):
        if not self.can_use_database():
            return

        self.lock_database()
        try:
            entity_index = self.manage_series_names.index(self.gui_elements["selector_manage_series"].value)
            entity_name_to_remove, entity_id_to_remove = self.manage_series_ids[entity_index]

            logger.info("Removing %s from the database...", entity_name_to_remove)

            await self.api_request(
                "DELETE",
                "/entities/delete",
                json={
                    "entity_id": entity_id_to_remove,
                    "entity_name": entity_name_to_remove,
                },
            )

            notify_and_log(f"Removed {entity_name_to_remove} from the database")
            self.refresh_manage_series()
            self.refresh_table()
        except Exception as e:
            logger.error("Error deleting series: %s", str(e))
            notify_and_log(f"Error deleting series: {str(e)}")
        finally:
            self.unlock_database()

    async def delete_chapter_tracking(self):
        if not self.can_use_database():
            return

        self.lock_database()
        try:
            entity_index = self.manage_chapter_names.index(self.gui_elements["selector_manage_chapters"].value)
            entity_id, entity_name, chapter_id, chapter_name = self.manage_chapter_ids[entity_index]

            logger.info(
                "Removing tracking for %s (%s) from %s (%s) in the database...",
                chapter_name,
                chapter_id,
                entity_name,
                entity_id,
            )

            await self.api_request(
                "DELETE",
                "/entities/chapters/untrack",
                json={
                    "entity_id": entity_id,
                    "chapter_id": chapter_id,
                },
            )

            notify_and_log(f"Removed tracked status for {chapter_name} from {entity_name}")
            self.refresh_table()
        except Exception as e:
            logger.error("Error untracking chapter: %s", str(e))
            notify_and_log(f"Error untracking chapter: {str(e)}")
        finally:
            self.unlock_database()

    async def refresh_database(self):
        if not self.can_use_database():
            return

        if self.first_scan:
            self.first_scan = False
            logger.debug("Timer setup scan triggered. Skipping startup run.")
            return

        self.lock_database()
        try:
            notify_and_log("Triggering database refresh... please wait")

            await self.api_request("POST", "/scanner/run")

            notify_and_log("Database refresh started")
            self.refresh_table()
        except Exception as e:
            logger.error("Error triggering refresh: %s", str(e))
            notify_and_log(f"Error triggering refresh: {str(e)}")
        finally:
            self.unlock_database()

    async def clean_orphaned_files(self):
        if not self.can_use_database():
            return

        self.lock_database()
        try:
            notify_and_log("Removing orphaned files...")

            await self.api_request("POST", "/scanner/clean-orphaned")

            notify_and_log("Orphaned files removed")
            self.refresh_table()
        except Exception as e:
            logger.error("Error cleaning orphaned files: %s", str(e))
            notify_and_log(f"Error cleaning orphaned files: {str(e)}")
        finally:
            self.unlock_database()
