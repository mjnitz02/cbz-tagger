import asyncio
import logging

from nicegui import ui

from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.env import AppEnv
from cbz_tagger.entities.metadata_entity import MetadataEntity
from cbz_tagger.gui.elements.config_table import config_table
from cbz_tagger.gui.elements.series_table import series_table
from cbz_tagger.gui.elements.ui_logger import ui_logger

logger = logging.getLogger()


def refresh_scanner(scanner):
    scanner.run()
    return scanner


def add_new_to_scanner(scanner, entity_name, entity_id, backend, mark_as_tracked):
    scanner.entity_database.add(
        entity_name,
        entity_id,
        manga_name=None,
        backend=backend,
        update=True,
        track=True,
        mark_as_tracked=mark_as_tracked,
    )
    return scanner


def notify_and_log(msg):
    ui.notify(msg)
    logger.info(msg)


class SimpleGui:
    def __init__(self, scanner):
        logger.info("Starting GUI")
        self.env = AppEnv()
        self.scanning_state = False
        self.scanner = scanner
        self.series_table = None
        self.config_table = None
        self.ui_logger = None

        self.meta_entries = []
        self.meta_choices = []
        self.add_series_input_box = None
        self.add_series_selector = None
        self.add_name_selector = None
        self.add_backend_selector = None
        self.add_backend_input_box = None
        self.add_mark_all_tracked = None

        self.initialize_gui()
        self.initialize()

    def initialize_gui(self):
        with ui.left_drawer().classes("bg-blue-100") as left_drawer:
            ui.label("Navigation")
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
                ui.tab("Configuration")
                ui.tab("Log")
            ui.space()

        with ui.footer(value=True):
            ui.label("CBZ Tagger GUI v0.1")

        with ui.tab_panels(tabs, value="Series").classes("w-full"):
            with ui.tab_panel("Series"):
                ui.label("Series")
                self.series_table = series_table()
                ui.label("Latest chapter may not be the highest number. Sometimes chapters are retroactively updated.")
            with ui.tab_panel("Add"):
                ui.label("Add Series")
                with ui.row():
                    ui.button("Refresh Series List", on_click=self.refresh_series_search)
                    ui.button("Refresh Series Name List", on_click=self.refresh_series_names)

                self.add_series_input_box = ui.input(
                    "Please enter the name of a series to search for", placeholder="Series Name"
                ).classes("w-2/3")
                self.add_series_selector = ui.select(
                    label="Select a series (type to filter)",
                    options=["Please refresh series list"],
                    with_input=True,
                    value="Please refresh series list",
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
            with ui.tab_panel("Configuration"):
                ui.label("Server Configuration")
                self.config_table = config_table()
            with ui.tab_panel("Log"):
                ui.label("Server Logs")
                self.ui_logger = ui_logger()

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

        ui.notify("Adding new series... please wait")
        loop = asyncio.get_event_loop()
        self.scanner = await loop.run_in_executor(
            None, add_new_to_scanner, self.scanner, entity_name, entity_id, backend, mark_as_tracked
        )

        ui.notify("New series added!")

    def initialize(self):
        logger.info("proxy_url: %s", self.env.PROXY_URL)
        logger.info("UI scan timer started with delay: %s", self.env.TIMER_DELAY)
        ui.timer(self.env.TIMER_DELAY, self.refresh_database, once=True)
        self.refresh_table()

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
