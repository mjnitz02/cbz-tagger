"""Standalone FastAPI server for CBZ Tagger API."""

import logging
import os

# Import gui module to register pages and setup UI configuration
from datetime import datetime

import httpx
from nicegui import app
from nicegui import context
from nicegui import ui

from cbz_tagger.gui.enums import EmojiNamespace
from cbz_tagger.gui.enums import EnvNamespace
from cbz_tagger.gui.enums import PluginsNamespace
from cbz_tagger.gui.file_log_reader import FileLogReader

logger = logging.getLogger(__name__)


class UiState:
    Emoji: EmojiNamespace
    Plugins: PluginsNamespace
    env: EnvNamespace

    def __init__(self):
        logger.debug("Starting GUI")
        self.api_base_url = "http://localhost:8000"  # FastAPI backend port
        self.gui_elements = {}

        self.meta_entries = []
        self.meta_choices = []
        self.manage_series_ids = []
        self.manage_series_names = []
        self.manage_chapter_names = []
        self.manage_chapter_ids = []

        # Fetch enums from the API backend
        self._fetch_enums_from_api()
        self.initialize()

    def _fetch_enums_from_api(self) -> None:
        """Fetch Emoji, Plugins, and Env configuration from the FastAPI backend."""
        try:
            with httpx.Client() as client:
                # Fetch Emoji enum
                emoji_response = client.get(f"{self.api_base_url}/api/enums/emoji", timeout=5)
                emoji_response.raise_for_status()
                emoji_data = emoji_response.json()

                # Fetch Plugins enum
                plugins_response = client.get(f"{self.api_base_url}/api/enums/plugins", timeout=5)
                plugins_response.raise_for_status()
                plugins_data = plugins_response.json()

                # Fetch Env configuration
                env_response = client.get(f"{self.api_base_url}/api/enums/env", timeout=5)
                env_response.raise_for_status()
                env_data = env_response.json()

                # Create namespace objects using the module-level classes
                self.Emoji = EmojiNamespace(emoji_data)
                self.Plugins = PluginsNamespace(plugins_data)
                self.env = EnvNamespace(env_data)

                logger.debug("Successfully fetched enums and configuration from API")
        except Exception as e:
            logger.error("Failed to fetch enums from API: %s", e)
            raise RuntimeError(f"Cannot start GUI without API backend. Error: {e}") from e

    @staticmethod
    def notify_and_log(msg: str):
        try:
            # Only show UI notification if we're in a valid client context
            if context.client:
                ui.notify(msg)
        except RuntimeError:
            # Context is not available (e.g., background task, deleted element)
            pass
        logger.info("%s %s", datetime.now(), msg)

    def clear_log(self):
        self.gui_elements["logger"].clear_log_file()
        logger.info("Log file cleared. %s", datetime.now())

    def initialize(self):
        """Initialize the GUI. Background tasks are handled by the FastAPI server."""
        logger.info("NiceGUI initialized. API base URL: %s", self.api_base_url)

    def create_navigation_bar(self):
        """Create the navigation bar and left drawer for all pages."""
        with ui.left_drawer().style("background-color: #23272e").props("width=225") as left_drawer:
            button_class = "w-full mb-1"
            ui.button("Series", on_click=lambda: ui.navigate.to("/series")).classes(button_class)
            ui.button("Add Series", on_click=lambda: ui.navigate.to("/add_series")).classes(button_class)
            ui.button("Manage Series", on_click=lambda: ui.navigate.to("/manage_series")).classes(button_class)
            ui.button("Config", on_click=lambda: ui.navigate.to("/config")).classes(button_class)
            ui.button("Log", on_click=lambda: ui.navigate.to("/log")).classes(button_class)
            ui.button("Refresh Table", on_click=self.refresh_table).classes(button_class)
            ui.button("Refresh Database", on_click=self.refresh_database).classes(button_class)
            ui.space()
            ui.label(f"Version: {self.env.VERSION}").classes("text-xs text-gray-400 w-full text-center")
            ui.link("GitHub", "https://github.com/mjnitz02/cbz-tagger").classes(
                "w-full text-center text-xs text-gray-400"
            ).props("icon=code")

        with ui.header().classes(replace="row items-center"):
            # pylint: disable=unnecessary-lambda
            ui.button(on_click=lambda: left_drawer.toggle(), icon="menu").props("flat color=white")
            ui.html("<h5><strong>CBZ Tagger</strong></h5>", sanitize=False)

    def series_table(self) -> ui.table:
        columns = [
            {
                "name": "entity_name",
                "label": "Entity Name",
                "field": "entity_name",
                "required": True,
                "align": "left",
            },
            {
                "name": "entity_id",
                "label": "Entity ID",
                "field": "entity_id",
                "required": True,
                "align": "left",
                "sortable": True,
                "classes": "hidden",
                "headerClasses": "hidden",
            },
            {"name": "status", "label": "Status", "field": "status", "sortable": True},
            {
                "name": "tracked",
                "label": "Tracked",
                "field": "tracked",
                "sortable": True,
            },
            {"name": "latest_chapter", "label": "Chapter", "field": "latest_chapter", "sortable": True},
            {
                "name": "latest_chapter_date",
                "label": "Chapter Updated",
                "field": "latest_chapter_date",
                "sortable": True,
            },
            {
                "name": "updated",
                "label": "Metadata Updated",
                "field": "updated",
                "sortable": True,
                "classes": "hidden",
                "headerClasses": "hidden",
            },
            {
                "name": "plugin",
                "label": "Plugin",
                "field": "plugin",
                "sortable": True,
                "classes": "hidden",
                "headerClasses": "hidden",
            },
        ]
        table = ui.table(columns=columns, rows=[], row_key="entity_name").classes("table-auto").props("flat dense")
        table.add_slot(
            "body-cell-entity_name",
            """
            <q-td :props="props">
                <a :href="props.value.link">{{ props.value.name }}</a>
            </q-td>
            """,
        )
        table.add_slot(
            "body-cell-updated",
            """
            <q-td :props="props">
                <q-badge
                    :color="
                    Date.parse(props.value) > Date.now() - (45 * 86400000) ? 'green' :
                        Date.parse(props.value) > Date.now() - (90 * 86400000) ? 'orange' : 'red'
                ">
                    {{ new Date(props.value).toISOString().substring(0, 16) }}
                </q-badge>
            </q-td>
        """,
        )
        table.add_slot(
            "body-cell-latest_chapter_date",
            """
            <q-td :props="props">
                <q-badge
                    :color="
                    Date.parse(props.value) > Date.now() - (45 * 86400000) ? 'green' :
                        Date.parse(props.value) > Date.now() - (90 * 86400000) ? 'orange' : 'red'
                ">
                    {{ new Date(props.value).toISOString().substring(0, 16) }}
                </q-badge>
            </q-td>
        """,
        )
        table.add_slot(
            "body-cell-plugin",
            """
            <q-td :props="props">
                <a :href="props.value.link">{{ props.value.name }}</a>
            </q-td>
            """,
        )
        return table

    def config_table(self) -> ui.table:
        columns = [
            {
                "name": "property",
                "label": "property",
                "field": "property",
                "align": "left",
            },
            {
                "name": "value",
                "label": "value",
                "field": "value",
                "align": "left",
            },
        ]
        return ui.table(
            columns=columns,
            rows=[
                {"property": "container_mode", "value": self.env.CONTAINER_MODE},
                {"property": "config_path", "value": self.env.CONFIG_PATH},
                {"property": "scan_path", "value": self.env.SCAN_PATH},
                {"property": "storage_path", "value": self.env.STORAGE_PATH},
                {"property": "timer_delay", "value": self.env.TIMER_DELAY},
                {"property": "proxy_url", "value": self.env.PROXY_URL},
                {"property": "PUID", "value": self.env.PUID},
                {"property": "PGID", "value": self.env.PGID},
                {"property": "UMASK", "value": self.env.UMASK},
                {"property": "LOG_LEVEL", "value": self.env.LOG_LEVEL},
            ],
        )

    def ui_logger(self) -> FileLogReader:
        log_reader = FileLogReader(self.env.LOG_PATH)

        # Create HTML element with pre tag for log display
        log_display = (
            ui.html("", sanitize=False)
            .classes("w-full")
            .style(
                "height: 70vh; overflow-y: auto; background-color: #1e1e1e; color: #d4d4d4; "
                "padding: 10px; border-radius: 5px; font-family: 'Courier New', monospace; "
                "font-size: 12px; white-space: pre-wrap; word-wrap: break-word;"
            )
        )

        # Function to refresh log display
        def refresh_logs():
            log_content = log_reader.read_last_lines(max_lines=1000)
            # Escape HTML to prevent injection
            log_content = log_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            log_display.content = f"<pre style='margin: 0;'>{log_content}</pre>"
            # Auto-scroll to bottom
            # Logic is broken currently
            # ui.run_javascript(f'getElement({log_display.id}).scrollTop = getElement({log_display.id}).scrollHeight')

        # Initial load
        refresh_logs()

        # Set up timer to refresh logs every 2 seconds
        ui.timer(2.0, refresh_logs)

        return log_reader

    def toggle(self, column: str) -> None:
        try:
            if context.client:
                column_index = [e["label"] for e in self.gui_elements["table_series"].columns].index(column)
                column = self.gui_elements["table_series"].columns[column_index]
                visible = not column.get("classes", "") == ""
                column["classes"] = "" if visible else "hidden"
                column["headerClasses"] = "" if visible else "hidden"
                self.gui_elements["table_series"].update()
        except RuntimeError:
            # Client has been deleted, nothing to update
            pass

    async def refresh_series_search(self):
        search_term = self.gui_elements["input_box_add_series"].value
        if len(search_term) == 0:
            self.notify_and_log("Please enter a name to search for")
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/api/scanner/search-series", params={"title": search_term}
                )
                response.raise_for_status()
                data = response.json()
                results = data["results"]

            # Store the raw results for later use
            self.meta_entries = results
            # Extract display names for the dropdown
            self.meta_choices = [result["display_name"] for result in results]

            # Update UI only if client is still valid
            try:
                if context.client:
                    self.gui_elements["selector_add_series"].options = self.meta_choices
                    self.gui_elements["selector_add_series"].value = self.meta_choices[0]
                    self.gui_elements["add_new"].enable()
            except RuntimeError:
                # Client has been deleted, nothing to update
                pass
        except httpx.HTTPError as e:
            self.notify_and_log(f"Error searching for series: {e}")

    def refresh_series_names(self):
        if len(self.meta_entries) == 0:
            return
        entity_index = self.meta_choices.index(self.gui_elements["selector_add_series"].value)
        all_titles = self.meta_entries[entity_index]["all_titles"]

        # Update UI only if client is still valid
        try:
            if context.client:
                self.gui_elements["selector_add_name"].options = all_titles
                self.gui_elements["selector_add_name"].value = all_titles[0]
        except RuntimeError:
            # Client has been deleted, nothing to update
            pass

    async def refresh_manage_series(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base_url}/api/scanner/series")
            response.raise_for_status()
            data = response.json()
            series_list = data["series"]

        self.manage_series_ids = [(s["name"], s["entity_id"]) for s in series_list]
        self.manage_series_names = [f"{name} ({entity_id})" for name, entity_id in self.manage_series_ids]

        # Update UI only if client is still valid
        try:
            if context.client:
                if len(self.manage_series_names) == 0:
                    self.gui_elements["selector_manage_series"].options = ["Please refresh series list"]
                    self.gui_elements["manage_series_delete"].disable()
                    self.gui_elements["selector_manage_chapters"].value = ["Please refresh series list"]
                    self.gui_elements["manage_chapter_delete"].disable()
                else:
                    self.gui_elements["selector_manage_series"].options = self.manage_series_names
                    self.gui_elements["manage_series_delete"].enable()
                    self.gui_elements["manage_chapter_delete"].enable()
                self.gui_elements["selector_manage_series"].value = self.gui_elements["selector_manage_series"].options[
                    0
                ]
        except RuntimeError:
            # Client has been deleted, nothing to update
            pass

    async def refresh_manage_series_chapters(self):
        if len(self.manage_series_ids) == 0:
            return

        entity_index = self.manage_series_names.index(self.gui_elements["selector_manage_series"].value)
        selected_series_name, selected_series_id = self.manage_series_ids[entity_index]

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base_url}/api/scanner/series/{selected_series_id}/chapters")
            response.raise_for_status()
            data = response.json()
            chapters = data["chapters"]

        self.manage_chapter_ids = [
            (selected_series_id, selected_series_name, chapter["entity_id"], f"Chapter {chapter['chapter_number']}")
            for chapter in chapters
        ]
        self.manage_chapter_names = [chapter_name for _, _, _, chapter_name in self.manage_chapter_ids]
        if len(self.manage_chapter_ids) == 0:
            return

        # Update UI only if client is still valid
        try:
            if context.client:
                self.gui_elements["selector_manage_chapters"].options = self.manage_chapter_names
                self.gui_elements["selector_manage_chapters"].value = self.manage_chapter_names[0]
        except RuntimeError:
            # Client has been deleted, nothing to update
            pass

    def refresh_table(self):
        """Refresh the series table with current data from the API."""
        logger.debug("Refreshing series table")

        with httpx.Client() as client:
            response = client.get(f"{self.api_base_url}/api/scanner/state", timeout=30)
            response.raise_for_status()
            state = response.json()["state"]

        formatted_state = []
        for item in state:
            if len(item["entity_name"]) > 50:
                item["entity_name"] = item["entity_name"][:50] + "..."
            formatted_state.append(item)

        # Update UI only if client is still valid
        try:
            if context.client:
                self.gui_elements["table_series"].rows = formatted_state
                logger.debug("Series GUI Refreshed")
        except RuntimeError:
            # Client has been deleted, nothing to update
            logger.debug("Cannot refresh GUI - client has been deleted")

    async def add_new_series(self):
        self.gui_elements["spinner_add"].set_visibility(True)
        self.gui_elements["spinner_add_label"].set_visibility(True)
        self.gui_elements["add_new"].disable()
        entity_index = self.meta_choices.index(self.gui_elements["selector_add_series"].value)
        entity = self.meta_entries[entity_index]
        entity_id = entity["entity_id"]
        entity_name = self.gui_elements["selector_add_name"].value
        if (
            self.gui_elements["selector_add_backend"].value != self.Plugins.MDX
            and len(self.gui_elements["input_box_add_backend"].value) == 0
        ):
            self.notify_and_log("Please enter a backend id for non-MDX backends")
            return
        if self.gui_elements["selector_add_backend"].value != self.Plugins.MDX:
            backend = {
                "plugin_type": self.gui_elements["selector_add_backend"].value,
                "plugin_id": self.gui_elements["input_box_add_backend"].value,
            }
        else:
            backend = None
        mark_all_tracked = self.gui_elements["radio_add_mark_all_tracked"].value == "Yes"
        enable_tracking = self.gui_elements["radio_add_mark_all_tracked"].value != "Disable Tracking"

        self.notify_and_log("Adding new series... please wait")
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/scanner/add-series",
                    json={
                        "entity_name": entity_name,
                        "entity_id": entity_id,
                        "backend": backend,
                        "enable_tracking": enable_tracking,
                        "mark_all_tracked": mark_all_tracked,
                    },
                )
                response.raise_for_status()
            self.notify_and_log("New series added!")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                self.notify_and_log("Scanner is busy. Please wait and try again.")
                try:
                    if context.client:
                        self.gui_elements["spinner_add"].set_visibility(False)
                        self.gui_elements["spinner_add_label"].set_visibility(False)
                except RuntimeError:
                    # Client has been deleted, nothing to update
                    pass
                return
            raise

        # Reset the Add New Series form - only if client is still valid
        try:
            if context.client:
                self.gui_elements["spinner_add"].set_visibility(False)
                self.gui_elements["spinner_add_label"].set_visibility(False)
                self.meta_entries = []
                self.meta_choices = []
                self.gui_elements["input_box_add_series"].value = ""
                self.gui_elements["selector_add_series"].options = ["Please refresh series list"]
                self.gui_elements["selector_add_series"].value = self.gui_elements["selector_add_series"].options[0]
                self.gui_elements["selector_add_name"].options = ["Please refresh series list"]
                self.gui_elements["selector_add_name"].value = self.gui_elements["selector_add_name"].options[0]
                self.gui_elements["selector_add_backend"].value = self.Plugins.MDX
                self.gui_elements["input_box_add_backend"].value = ""
                self.gui_elements["radio_add_mark_all_tracked"].value = "No"
                self.refresh_table()
        except RuntimeError:
            # Client has been deleted, nothing to update
            pass

    async def delete_series(self):
        entity_index = self.manage_series_names.index(self.gui_elements["selector_manage_series"].value)
        entity_name_to_remove, entity_id_to_remove = self.manage_series_ids[entity_index]
        logger.info("Removing %s from the database...", entity_name_to_remove)
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.delete(
                    f"{self.api_base_url}/api/scanner/series/{entity_id_to_remove}",
                    params={"entity_name": entity_name_to_remove},
                )
                response.raise_for_status()
            self.notify_and_log(f"Removed {entity_name_to_remove} from the database")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                self.notify_and_log("Scanner is busy. Please wait and try again.")
                return
            raise
        await self.refresh_manage_series()
        self.refresh_table()

    async def delete_chapter_tracking(self):
        entity_index = self.manage_chapter_names.index(self.gui_elements["selector_manage_chapters"].value)
        entity_id, entity_name, chapter_id, chapter_name = self.manage_chapter_ids[entity_index]
        logger.info(
            "Removing tracking for %s (%s) from %s (%s) in the database...",
            chapter_name,
            chapter_id,
            entity_name,
            entity_id,
        )
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.delete(f"{self.api_base_url}/api/scanner/chapter/{entity_id}/{chapter_id}")
                response.raise_for_status()
            self.notify_and_log(f"Removed tracked status for {chapter_name} from {entity_name}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                self.notify_and_log("Scanner is busy. Please wait and try again.")
                return
            raise
        self.refresh_table()

    async def refresh_database(self):
        self.notify_and_log("Refreshing database... please wait")

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.post(f"{self.api_base_url}/api/scanner/refresh")
                response.raise_for_status()
            self.notify_and_log("Series Database Refreshed")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                self.notify_and_log("Scanner is busy. Please wait and try again.")
                return
            raise
        self.refresh_table()

    async def clean_orphaned_files(self):
        self.notify_and_log("Removing orphaned files...")
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.post(f"{self.api_base_url}/api/scanner/clean-orphaned")
                response.raise_for_status()
            self.notify_and_log("Orphaned files removed successfully")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                self.notify_and_log("Scanner is busy. Please wait and try again.")
                return
            raise
        self.refresh_table()


# Global GUI instance for page functions to access
gui_instance: UiState | None = None


def get_gui_instance() -> UiState:
    """Get or create the global GUI instance."""

    # Setup UI configuration on startup
    ui.add_head_html('<link rel="apple-touch-icon" href="static/apple-touch-icon.png">')
    ui.colors(primary="#535353")
    udark = ui.dark_mode()
    udark.enable()

    # Global variable to hold the GUI instance
    global gui_instance
    if gui_instance is None:
        gui_instance = UiState()
    return gui_instance


@ui.page("/")
def index_page():
    """Root page that redirects to the Series page."""
    ui.navigate.to("/series")


@ui.page("/series")
def series_page():
    """Series page showing the main series table."""
    gui = get_gui_instance()
    ui.page_title("CBZ Tagger - Series")
    gui.create_navigation_bar()

    with ui.column().classes("w-full p-4"):
        with ui.row():
            for table_columns in ["Entity ID", "Metadata Updated", "Plugin"]:
                ui.switch(table_columns, value=False, on_change=lambda _, column=table_columns: gui.toggle(column))

        gui.gui_elements["table_series"] = gui.series_table()

        with ui.row():
            ui.label(f"{gui.Emoji.CHECK_GREEN} Completed")
            ui.label(f"{gui.Emoji.CIRCLE_GREEN} Ongoing/Tracked")
            ui.label(f"{gui.Emoji.CIRCLE_BROWN} Not Tracked")
            ui.label(f"{gui.Emoji.CIRCLE_YELLOW} Hiatus")
            ui.label(f"{gui.Emoji.CIRCLE_RED} Cancelled")

        with ui.row():
            ui.label(f"{gui.Emoji.SQUARE_GREEN} Updated < 45d")
            ui.label(f"{gui.Emoji.SQUARE_ORANGE} Updated 45 - 90d")
            ui.label(f"{gui.Emoji.SQUARE_RED} Updated > 90d")
            ui.label(f"{gui.Emoji.QUESTION_MARK} Unknown")

    # Initial table refresh
    gui.refresh_table()


@ui.page("/add_series")
def add_series():
    """Manage page for adding and removing series/chapters."""
    gui = get_gui_instance()
    ui.page_title("CBZ Tagger - Add Series")
    gui.create_navigation_bar()

    with ui.column().classes("w-full p-4"):
        ui.separator()
        ui.markdown("#### Add Series")
        ui.separator()

        gui.gui_elements["add_search"] = ui.chip(
            "Search for New Series", icon="search", color="primary", on_click=gui.refresh_series_search
        )
        gui.gui_elements["input_box_add_series"] = ui.input(
            "Please enter the name of a series to search for", placeholder="Series Name"
        ).classes("w-2/3")
        gui.gui_elements["selector_add_series"] = ui.select(
            label="Select a series (type to filter)",
            options=["Please search for a series"],
            with_input=True,
            value="Please search for a series",
            on_change=gui.refresh_series_names,
        ).classes("w-2/3")
        gui.gui_elements["selector_add_name"] = ui.select(
            label="Select the name of the series (type to filter)",
            options=["Please search for a series"],
            with_input=True,
            value="Please search for a series",
        ).classes("w-2/3")
        gui.gui_elements["selector_add_backend"] = ui.select(
            label="Select a series backend (Default: MDX)", options=gui.Plugins.all(), value=gui.Plugins.MDX
        ).classes("w-2/3")
        gui.gui_elements["input_box_add_backend"] = ui.input(
            "Backend id for the series (Only for non-MDX backends)",
            placeholder="Enter the backend id for the series",
        ).classes("w-2/3")
        ui.label("Mark all chapters as tracked?")
        gui.gui_elements["radio_add_mark_all_tracked"] = (
            ui.radio(["Yes", "No", "Disable Tracking"], value="No").classes("w-2/3").props("inline")
        )
        with ui.row():
            gui.gui_elements["add_new"] = ui.chip(
                "Add New Series", icon="add", color="green", on_click=gui.add_new_series
            )
            gui.gui_elements["add_new"].disable()
            gui.gui_elements["spinner_add"] = ui.spinner()
            gui.gui_elements["spinner_add"].set_visibility(False)
            gui.gui_elements["spinner_add_label"] = ui.label("Adding new series...")
            gui.gui_elements["spinner_add_label"].set_visibility(False)


@ui.page("/manage_series")
def manage_page():
    """Manage page for adding and removing series/chapters."""
    gui = get_gui_instance()
    ui.page_title("CBZ Tagger - Manage Series")
    gui.create_navigation_bar()

    with ui.column().classes("w-full p-4"):
        ui.separator()
        ui.markdown("#### Manage Series")
        ui.separator()

        gui.gui_elements["selector_manage_series"] = ui.select(
            label="Select a series (type to filter)",
            options=["Please refresh series list"],
            with_input=True,
            value="Please refresh series list",
            on_change=gui.refresh_manage_series_chapters,
        ).classes("w-2/3")
        gui.gui_elements["selector_manage_chapters"] = ui.select(
            label="Select a chapter (type to filter)",
            options=["Please select a series first"],
            with_input=True,
            value="Please select a series first",
        ).classes("w-2/3")

        with ui.row():
            gui.gui_elements["manage_chapter_delete"] = ui.chip(
                "Refresh Series List", icon="refresh", color="primary", on_click=gui.refresh_manage_series
            )
            gui.gui_elements["manage_series_delete"] = ui.chip(
                "Delete Selected Series", icon="delete", color="red", on_click=gui.delete_series
            )
            gui.gui_elements["manage_series_delete"].disable()
            gui.gui_elements["manage_chapter_delete"] = ui.chip(
                "Reset Tracked Chapter", icon="restart_alt", color="orange", on_click=gui.delete_chapter_tracking
            )
            gui.gui_elements["manage_chapter_delete"].disable()
            gui.gui_elements["delete_clean"] = ui.chip(
                "Clean Orphaned Files", icon="cleaning_services", color="orange", on_click=gui.clean_orphaned_files
            )


@ui.page("/config")
def config_page():
    """Configuration page showing server settings."""
    gui = get_gui_instance()
    ui.page_title("CBZ Tagger - Config")
    gui.create_navigation_bar()

    with ui.column().classes("w-full p-4"):
        gui.gui_elements["table_config"] = gui.config_table()


@ui.page("/log")
def log_page():
    """Log page showing server logs."""
    gui = get_gui_instance()
    ui.page_title("CBZ Tagger - Log")
    gui.create_navigation_bar()

    with ui.column().classes("w-full p-4"):
        gui.gui_elements["logger"] = gui.ui_logger()
        ui.chip("Clear", icon="delete", color="red", on_click=gui.clear_log)


def main():
    """Run the FastAPI server."""
    if os.getenv("LOG_LEVEL") is None:
        LOG_LEVEL = logging.INFO
    else:
        LOG_LEVEL = os.getenv("LOG_LEVEL")

    # Configure logging

    logging.basicConfig(level=LOG_LEVEL)
    logger.info("Starting CBZ Tagger NiceGUI server...")

    # Run the server
    root_path = os.path.dirname(os.path.abspath(__file__))
    static_path = os.path.join(root_path, "static")
    app.add_static_files("/static", static_path)
    ui.run(reload=False, favicon=os.path.join(static_path, "favicon.ico"))


if __name__ in {"__main__", "__mp_main__"}:
    main()
