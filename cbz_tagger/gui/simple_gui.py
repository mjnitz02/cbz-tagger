import asyncio
import logging
from datetime import datetime

from nicegui import ui

from cbz_tagger.common.enums import Emoji
from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.env import AppEnv
from cbz_tagger.common.log_element_handler import FileLogReader
from cbz_tagger.database.file_scanner import FileScanner
from cbz_tagger.entities.metadata_entity import MetadataEntity

logger = logging.getLogger()


def refresh_scanner(scanner: FileScanner) -> FileScanner:
    scanner.run()
    return scanner


def add_new_to_scanner(
    scanner: FileScanner, entity_name: str, entity_id: str, backend: str, enable_tracking: bool, mark_all_tracked: bool
) -> FileScanner:
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


def notify_and_log(msg: str):
    ui.notify(msg)
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


def ui_logger() -> ui.html:
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

    return log_display


class SimpleGui:
    def __init__(self, scanner):
        logger.debug("Starting GUI")
        self.env = AppEnv()
        self.first_scan = True
        self.scanning_state = False
        self.scanner: FileScanner = scanner
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
        logger.info("UI scan timer started with delay: %s", self.env.TIMER_DELAY)
        self.gui_elements["timer_scanner"] = ui.timer(self.env.TIMER_DELAY, self.refresh_database)
        self.refresh_table()

    @staticmethod
    def database_operation(func):
        def wrapper(self):
            if self.can_use_database():
                self.lock_database()
            else:
                return
            try:
                func(self)
            finally:
                self.unlock_database()
                self.refresh_table()

        return wrapper

    @staticmethod
    def database_operation_async(func):
        async def wrapper(self):
            if self.can_use_database():
                self.lock_database()
            else:
                return
            self.scanner.reload_scanner()
            try:
                await func(self)
                self.scanner.reload_scanner()
                self.refresh_table()
            finally:
                self.unlock_database()

        return wrapper

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

    def refresh_manage_series(self):
        self.scanner.reload_scanner()
        self.manage_series_ids = list(self.scanner.entity_database.entity_map.items())
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

    def refresh_manage_series_chapters(self):
        if len(self.manage_series_ids) == 0:
            return

        entity_index = self.manage_series_names.index(self.gui_elements["selector_manage_series"].value)
        selected_series_name, selected_series_id = self.manage_series_ids[entity_index]

        chapters = self.scanner.entity_database.chapters[selected_series_id]
        self.manage_chapter_ids = [
            (selected_series_id, selected_series_name, chapter.entity_id, f"Chapter {chapter.chapter_number}")
            for chapter in (chapters if chapters is not None else [])
        ]
        self.manage_chapter_names = [chapter_name for _, _, _, chapter_name in self.manage_chapter_ids]
        if len(self.manage_chapter_ids) == 0:
            return

        self.gui_elements["selector_manage_chapters"].options = self.manage_chapter_names
        self.gui_elements["selector_manage_chapters"].value = self.manage_chapter_names[0]

    def refresh_table(self):
        logger.debug("Refreshing series table")
        self.scanner.reload_scanner()
        state = self.scanner.to_state()
        formatted_state = []
        for item in state:
            if len(item["entity_name"]) > 50:
                item["entity_name"] = item["entity_name"][:50] + "..."
            formatted_state.append(item)
        self.gui_elements["table_series"].rows = formatted_state
        logger.debug("Series GUI Refreshed")

    def can_use_database(self):
        if self.scanning_state:
            notify_and_log("Database currently in use, please wait...")
            return False
        return True

    def lock_database(self):
        self.scanning_state = True

    def unlock_database(self):
        self.scanning_state = False

    @database_operation_async
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
        loop = asyncio.get_event_loop()
        self.scanner = await loop.run_in_executor(
            None, add_new_to_scanner, self.scanner, entity_name, entity_id, backend, enable_tracking, mark_all_tracked
        )

        notify_and_log("New series added!")

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

    @database_operation
    def delete_series(self):
        entity_index = self.manage_series_names.index(self.gui_elements["selector_manage_series"].value)
        entity_name_to_remove, entity_id_to_remove = self.manage_series_ids[entity_index]
        logger.info("Removing %s from the database...", entity_name_to_remove)
        self.scanner.entity_database.delete_entity_id(entity_id_to_remove, entity_name_to_remove)
        notify_and_log(f"Removed {entity_name_to_remove} from the database")
        self.refresh_manage_series()

    @database_operation
    def delete_chapter_tracking(self):
        entity_index = self.manage_chapter_names.index(self.gui_elements["selector_manage_chapters"].value)
        entity_id, entity_name, chapter_id, chapter_name = self.manage_chapter_ids[entity_index]
        logger.info(
            "Removing tracking for %s (%s) from %s (%s) in the database...",
            chapter_name,
            chapter_id,
            entity_name,
            entity_id,
        )
        self.scanner.entity_database.delete_chapter_entity_id_from_downloaded_chapters(entity_id, chapter_id)
        notify_and_log(f"Removed tracked status for {chapter_name} from {entity_name}")

    @database_operation_async
    async def refresh_database(self):
        if self.first_scan:
            self.first_scan = False
            logger.debug("Timer setup scan triggered. Skipping startup run.")
            return
        notify_and_log("Refreshing database... please wait")

        loop = asyncio.get_event_loop()
        self.scanner = await loop.run_in_executor(None, refresh_scanner, self.scanner)

        notify_and_log("Series Database Refreshed")

    @database_operation
    def clean_orphaned_files(self):
        notify_and_log("Removing orphaned files...")
        self.scanner.entity_database.remove_orphaned_covers()
