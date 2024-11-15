import asyncio
import logging

from nicegui import ui

from cbz_tagger.common.enums import Emoji
from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.env import AppEnv
from cbz_tagger.entities.metadata_entity import MetadataEntity
from cbz_tagger.gui.elements.config_table import config_table
from cbz_tagger.gui.elements.series_table import series_table
from cbz_tagger.gui.elements.ui_logger import ui_logger
from cbz_tagger.gui.functions import add_new_to_scanner
from cbz_tagger.gui.functions import notify_and_log
from cbz_tagger.gui.functions import refresh_scanner

logger = logging.getLogger()


class SimpleGui:
    def __init__(self, scanner):
        logger.info("Starting GUI")
        self.env = AppEnv()
        self.first_scan = True
        self.scanning_state = False
        self.scanner = scanner
        self.series_table = None
        self.config_table = None
        self.ui_logger = None
        self.timer = None

        self.meta_entries = []
        self.meta_choices = []
        self.add_series_input_box = None
        self.add_series_selector = None
        self.add_name_selector = None
        self.add_backend_selector = None
        self.add_backend_input_box = None
        self.add_mark_all_tracked = None

        self.delete_series_ids = []
        self.delete_series_selector = None

        self.initialize_gui()
        self.initialize()

    def initialize_gui(self):
        ui.page_title("CBZ Tagger")
        ui.colors(primary="#2F4F4F")

        with ui.left_drawer().style("background-color: #bfd9d9").props("width=225") as left_drawer:
            ui.button("Refresh Table", on_click=self.refresh_table)
            ui.button("Refresh Database", on_click=self.refresh_database)

        with ui.header().classes(replace="row items-center"):
            # pylint: disable=unnecessary-lambda
            ui.button(on_click=lambda: left_drawer.toggle(), icon="menu").props("flat color=white")
            ui.html("<h2><strong>CBZ Tagger</strong></h2>")
            ui.space()
            with ui.tabs() as tabs:
                ui.tab("Series")
                ui.tab("Add")
                ui.tab("Delete")
                ui.tab("Config")
                ui.tab("Log")
            ui.space()

        with ui.tab_panels(tabs, value="Series").classes("w-full"):
            with ui.tab_panel("Series"):
                with ui.row():
                    for column in ["Entity ID", "Metadata Updated", "Plugin"]:
                        # noinspection PyUnresolvedReferences
                        ui.switch(column, value=False, on_change=lambda e, column=column: self.toggle(column))
                self.series_table = series_table()
                with ui.row():
                    ui.label(f"{Emoji.CHECK_GREEN} Completed")
                    ui.label(f"{Emoji.CIRCLE_GREEN} Ongoing/Tracked")
                    ui.label(f"{Emoji.CIRCLE_YELLOW} Hiatus")
                    ui.label(f"{Emoji.CIRCLE_RED} Cancelled")
                    ui.label(f"{Emoji.QUESTION_MARK} Unknown/Other")
                with ui.row():
                    ui.label(f"{Emoji.SQUARE_GREEN} Updated < 45 days")
                    ui.label(f"{Emoji.SQUARE_ORANGE} Updated 45 - 90 days")
                    ui.label(f"{Emoji.SQUARE_RED} Updated > 90 days")
            with ui.tab_panel("Add"):
                ui.label("Add Series")
                ui.button("Search for New Series", on_click=self.refresh_series_search)

                self.add_series_input_box = ui.input(
                    "Please enter the name of a series to search for", placeholder="Series Name"
                ).classes("w-2/3")
                self.add_series_selector = ui.select(
                    label="Select a series (type to filter)",
                    options=["Please refresh series list"],
                    with_input=True,
                    value="Please refresh series list",
                    on_change=self.refresh_series_names,
                ).classes("w-2/3")
                self.add_name_selector = ui.select(
                    label="Select the name of the series (type to filter)",
                    options=["Please refresh series name list"],
                    with_input=True,
                    value="Please refresh series name list",
                ).classes("w-2/3")
                self.add_backend_selector = ui.select(
                    label="Select a series backend (Default: MDX)", options=Plugins.all(), value=Plugins.MDX
                ).classes("w-2/3")
                self.add_backend_input_box = ui.input(
                    "Backend id for the series (Only for non-MDX backends)",
                    placeholder="Enter the backend id for the series",
                ).classes("w-2/3")
                ui.label("Mark all chapters as tracked?")
                self.add_mark_all_tracked = ui.radio(["Yes", "No"], value="No").classes("w-2/3").props("inline")
                ui.button("Add New Series", on_click=self.add_new_series)
            with ui.tab_panel("Delete"):
                ui.label("Delete Series")
                self.delete_series_selector = ui.select(
                    label="Select a series (type to filter)",
                    options=["Please refresh series list"],
                    with_input=True,
                    value="Please refresh series list",
                ).classes("w-2/3")
                with ui.row():
                    ui.button("Refresh Series List", on_click=self.refresh_delete_series)
                    ui.button("Delete Selected Series", on_click=self.delete_series)
                    ui.button("Clean Orphaned Files", on_click=self.clean_orphaned_files)
            with ui.tab_panel("Config"):
                ui.label("Server Configuration")
                self.config_table = config_table()
            with ui.tab_panel("Log"):
                ui.label("Server Logs")
                self.ui_logger = ui_logger()

    def initialize(self):
        logger.info("proxy_url: %s", self.env.PROXY_URL)
        logger.info("UI scan timer started with delay: %s", self.env.TIMER_DELAY)
        self.timer = ui.timer(self.env.TIMER_DELAY, self.refresh_database)
        self.refresh_table()

    def toggle(self, column: str) -> None:
        column_index = [e["label"] for e in self.series_table.columns].index(column)
        column = self.series_table.columns[column_index]
        visible = not column.get("classes", "") == ""
        column["classes"] = "" if visible else "hidden"
        column["headerClasses"] = "" if visible else "hidden"
        self.series_table.update()

    def refresh_series_search(self):
        search_term = self.add_series_input_box.value
        if len(search_term) == 0:
            notify_and_log("Please enter a name to search for")
            return
        self.meta_entries = MetadataEntity.from_server_url(query_params={"title": search_term})
        self.meta_choices = list(
            f"{manga.title} ({manga.alt_title}) - {manga.created_at.year} - {manga.age_rating}"
            for manga in self.meta_entries
        )
        self.add_series_selector.options = self.meta_choices
        self.add_series_selector.value = self.meta_choices[0]

    def refresh_series_names(self):
        if len(self.meta_entries) == 0:
            notify_and_log("Please search before refreshing names")
            return
        entity_index = self.meta_choices.index(self.add_series_selector.value)
        self.add_name_selector.options = self.meta_entries[entity_index].all_titles
        self.add_name_selector.value = self.meta_entries[entity_index].all_titles[0]

    def refresh_delete_series(self):
        self.delete_series_ids = list(self.scanner.entity_database.entity_map.items())
        choices = [f"{name} ({entity_id})" for name, entity_id in self.delete_series_ids]
        self.delete_series_selector.options = choices
        self.delete_series_selector.value = choices[0]

    def delete_series(self):
        self.delete_series_ids = list(self.scanner.entity_database.entity_map.items())
        choices = [f"{name} ({entity_id})" for name, entity_id in self.delete_series_ids]
        entity_index = choices.index(self.delete_series_selector.value)
        entity_name_to_remove, entity_id_to_remove = self.delete_series_ids[entity_index]
        notify_and_log(f"Removing {entity_name_to_remove} from the database...")
        self.scanner.entity_database.delete_entity_id(entity_id_to_remove, entity_name_to_remove)
        notify_and_log(f"Removed {entity_name_to_remove} from the database")

    async def add_new_series(self):
        entity_index = self.meta_choices.index(self.add_series_selector.value)
        entity = self.meta_entries[entity_index]
        entity_id = entity.entity_id
        entity_name = self.add_name_selector.value
        if self.add_backend_selector.value != Plugins.MDX and len(self.add_backend_input_box.value) == 0:
            notify_and_log("Please enter a backend id for non-MDX backends")
            return
        if self.add_backend_selector.value != Plugins.MDX:
            backend = {
                "plugin_type": self.add_backend_selector.value,
                "plugin_id": self.add_backend_input_box.value,
            }
        else:
            backend = None
        mark_as_tracked = self.add_mark_all_tracked.value == "Yes"

        notify_and_log("Adding new series... please wait")
        loop = asyncio.get_event_loop()
        self.scanner = await loop.run_in_executor(
            None, add_new_to_scanner, self.scanner, entity_name, entity_id, backend, mark_as_tracked
        )

        notify_and_log("New series added!")

    def refresh_table(self):
        logger.info("Refreshing series table")
        state = self.scanner.to_state()
        formatted_state = []
        for item in state:
            if len(item["entity_name"]) > 50:
                item["entity_name"] = item["entity_name"][:50] + "..."
            formatted_state.append(item)
        self.series_table.rows = formatted_state
        notify_and_log("Series GUI Refreshed")

    async def refresh_database(self):
        if self.first_scan:
            self.first_scan = False
            logger.info("Timer setup scan triggered. Skipping startup run.")
            return
        if self.scanning_state:
            notify_and_log("Scanning in progress already...")
            return
        self.scanning_state = True
        notify_and_log("Refreshing database... please wait")

        loop = asyncio.get_event_loop()
        self.scanner = await loop.run_in_executor(None, refresh_scanner, self.scanner)
        self.refresh_table()

        notify_and_log("Series Database Refreshed")
        self.scanning_state = False

    def clean_orphaned_files(self):
        notify_and_log("Removing orphaned files...")
        self.scanner.entity_database.remove_orphaned_covers()
