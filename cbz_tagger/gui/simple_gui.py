import asyncio
import logging
import os
from collections import deque
from datetime import datetime

import httpx
from nicegui import app
from nicegui import context
from nicegui import run
from nicegui import ui

from cbz_tagger.common.enums import Emoji
from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.env import AppEnv
from cbz_tagger.entities.metadata_entity import MetadataEntity
from cbz_tagger.gui import api

# Register the API router with the NiceGUI app
app.include_router(api.router)

logger = logging.getLogger()

if "background_timer_started" not in app.storage.general:
    app.storage.general["background_timer_started"] = False
if "scanning_state" not in app.storage.general:
    app.storage.general["scanning_state"] = False


class FileLogReader:
    """A utility class for reading log files."""

    def __init__(self, log_file_path: str) -> None:
        self.log_file_path = log_file_path

    def read_last_lines(self, max_lines: int = 1000) -> str:
        """Read the last N lines from the log file.

        Args:
            max_lines: Maximum number of lines to read from the end of the file

        Returns:
            String containing the last N lines of the log file
        """
        if not os.path.exists(self.log_file_path):
            return ""

        try:
            with open(self.log_file_path, encoding="utf-8") as f:
                # Use deque to efficiently keep only the last N lines
                lines = deque(f, maxlen=max_lines)
                return "".join(lines)
        except Exception:  # pylint: disable=broad-except
            return f"Error reading log file: {self.log_file_path}"

    def clear_log_file(self) -> None:
        """Clear the contents of the log file."""
        if os.path.exists(self.log_file_path):
            try:
                with open(self.log_file_path, "w", encoding="utf-8") as f:
                    f.truncate(0)
            except Exception:  # pylint: disable=broad-except
                pass


def notify_and_log(msg: str):
    try:
        # Only show UI notification if we're in a valid client context
        if context.client:
            ui.notify(msg)
    except RuntimeError:
        # Context is not available (e.g., background task, deleted element)
        pass
    logger.info("%s %s", datetime.now(), msg)


def config_table() -> ui.table:
    env = AppEnv()
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
            {"property": "container_mode", "value": env.CONTAINER_MODE},
            {"property": "config_path", "value": env.CONFIG_PATH},
            {"property": "scan_path", "value": env.SCAN_PATH},
            {"property": "storage_path", "value": env.STORAGE_PATH},
            {"property": "timer_delay", "value": env.TIMER_DELAY},
            {"property": "proxy_url", "value": env.PROXY_URL},
            {"property": "PUID", "value": env.PUID},
            {"property": "PGID", "value": env.PGID},
            {"property": "UMASK", "value": env.UMASK},
            {"property": "LOG_LEVEL", "value": env.LOG_LEVEL},
        ],
    )


def series_table() -> ui.table:
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


def ui_logger() -> FileLogReader:
    env = AppEnv()
    log_reader = FileLogReader(env.LOG_PATH)

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


class SimpleGui:
    def __init__(self):
        logger.debug("Starting GUI")
        self.env = AppEnv()
        self.api_base_url = "http://localhost:8080"  # NiceGUI default port
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
            ui.html(f"<h5><strong>CBZ Tagger {self.env.VERSION}</strong></h5>", sanitize=False)
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
        self.gui_elements["logger"].clear_log_file()
        logger.info("Log file cleared. %s", datetime.now())

    def initialize(self):
        logger.info("proxy_url: %s", self.env.PROXY_URL)

        # Set up background timer that runs even when no clients are connected
        # Only register once, regardless of how many clients connect
        if not app.storage.general["background_timer_started"]:
            logger.info("UI scan timer started with delay: %s", self.env.TIMER_DELAY)
            app.storage.general["background_timer_started"] = True
            timer_delay = self.env.TIMER_DELAY
            api_base_url = self.api_base_url

            async def background_refresh():
                # Skip first run
                await asyncio.sleep(timer_delay)
                while True:
                    try:
                        # Call the refresh API endpoint
                        async with httpx.AsyncClient() as client:
                            response = await client.post(f"{api_base_url}/api/scanner/refresh", timeout=None)
                            response.raise_for_status()
                        logger.info("Background database refresh completed at %s", datetime.now())
                    except Exception as e:
                        logger.error("Error in background refresh: %s", e)
                    await asyncio.sleep(timer_delay)

            app.on_startup(lambda: asyncio.create_task(background_refresh()))
            logger.info("Background timer registered (will start on app startup)")
        # await self.refresh_table()

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

        self.meta_entries = MetadataEntity.from_server_url(query_params={"title": search_term})
        self.meta_choices = list(
            f"{manga.title} ({manga.alt_title}) - {manga.created_at.year} - {manga.age_rating}"
            for manga in self.meta_entries
        )
        self.gui_elements["selector_add_series"].options = self.meta_choices
        self.gui_elements["selector_add_series"].value = self.meta_choices[0]
        self.gui_elements["add_new"].enable()

    def refresh_series_names(self):
        if len(self.meta_entries) == 0:
            return
        entity_index = self.meta_choices.index(self.gui_elements["selector_add_series"].value)
        self.gui_elements["selector_add_name"].options = self.meta_entries[entity_index].all_titles
        self.gui_elements["selector_add_name"].value = self.meta_entries[entity_index].all_titles[0]

    async def refresh_manage_series(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base_url}/api/scanner/series")
            response.raise_for_status()
            data = response.json()
            series_list = data["series"]

        self.manage_series_ids = [(s["name"], s["entity_id"]) for s in series_list]
        self.manage_series_names = [f"{name} ({entity_id})" for name, entity_id in self.manage_series_ids]
        if len(self.manage_series_names) == 0:
            self.gui_elements["selector_manage_series"].options = ["Please refresh series list"]
            self.gui_elements["manage_series_delete"].disable()
            self.gui_elements["selector_manage_chapters"].value = ["Please refresh series list"]
            self.gui_elements["manage_chapter_delete"].disable()
        else:
            self.gui_elements["selector_manage_series"].options = self.manage_series_names
            self.gui_elements["manage_series_delete"].enable()
            self.gui_elements["manage_chapter_delete"].enable()
        self.gui_elements["selector_manage_series"].value = self.gui_elements["selector_manage_series"].options[0]

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

        self.gui_elements["selector_manage_chapters"].options = self.manage_chapter_names
        self.gui_elements["selector_manage_chapters"].value = self.manage_chapter_names[0]

    async def refresh_table(self):
        logger.debug("Refreshing series table")

        def fetch_state():
            with httpx.Client() as client:
                response = client.get(f"{self.api_base_url}/api/scanner/state", timeout=30)
                response.raise_for_status()
                return response.json()["state"]

        state = await run.io_bound(fetch_state)

        formatted_state = []
        for item in state:
            if len(item["entity_name"]) > 50:
                item["entity_name"] = item["entity_name"][:50] + "..."
            formatted_state.append(item)
        self.gui_elements["table_series"].rows = formatted_state
        logger.debug("Series GUI Refreshed")

    async def add_new_series(self):
        self.gui_elements["spinner_add"].set_visibility(True)
        self.gui_elements["spinner_add_label"].set_visibility(True)
        self.gui_elements["add_new"].disable()
        entity_index = self.meta_choices.index(self.gui_elements["selector_add_series"].value)
        entity = self.meta_entries[entity_index]
        entity_id = entity.entity_id
        entity_name = self.gui_elements["selector_add_name"].value
        if (
            self.gui_elements["selector_add_backend"].value != Plugins.MDX
            and len(self.gui_elements["input_box_add_backend"].value) == 0
        ):
            notify_and_log("Please enter a backend id for non-MDX backends")
            return
        if self.gui_elements["selector_add_backend"].value != Plugins.MDX:
            backend = {
                "plugin_type": self.gui_elements["selector_add_backend"].value,
                "plugin_id": self.gui_elements["input_box_add_backend"].value,
            }
        else:
            backend = None
        mark_all_tracked = self.gui_elements["radio_add_mark_all_tracked"].value == "Yes"
        enable_tracking = self.gui_elements["radio_add_mark_all_tracked"].value != "Disable Tracking"

        notify_and_log("Adding new series... please wait")
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
            notify_and_log("New series added!")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                notify_and_log("Scanner is busy. Please wait and try again.")
                self.gui_elements["spinner_add"].set_visibility(False)
                self.gui_elements["spinner_add_label"].set_visibility(False)
                return
            raise

        # Reset the Add New Series form
        self.gui_elements["spinner_add"].set_visibility(False)
        self.gui_elements["spinner_add_label"].set_visibility(False)
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
        await self.refresh_table()

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
            notify_and_log(f"Removed {entity_name_to_remove} from the database")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                notify_and_log("Scanner is busy. Please wait and try again.")
                return
            raise
        await self.refresh_manage_series()
        await self.refresh_table()

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
            notify_and_log(f"Removed tracked status for {chapter_name} from {entity_name}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                notify_and_log("Scanner is busy. Please wait and try again.")
                return
            raise
        await self.refresh_table()

    async def refresh_database(self):
        notify_and_log("Refreshing database... please wait")

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.post(f"{self.api_base_url}/api/scanner/refresh")
                response.raise_for_status()
            notify_and_log("Series Database Refreshed")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                notify_and_log("Scanner is busy. Please wait and try again.")
                return
            raise
        await self.refresh_table()

    async def clean_orphaned_files(self):
        notify_and_log("Removing orphaned files...")
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.post(f"{self.api_base_url}/api/scanner/clean-orphaned")
                response.raise_for_status()
            notify_and_log("Orphaned files removed successfully")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                notify_and_log("Scanner is busy. Please wait and try again.")
                return
            raise
        await self.refresh_table()
