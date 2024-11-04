import asyncio
import logging

from nicegui import ui

from cbz_tagger.common.env import AppEnv
from cbz_tagger.gui.elements.config_table import config_table
from cbz_tagger.gui.elements.series_table import series_table
from cbz_tagger.gui.elements.ui_logger import ui_logger

logger = logging.getLogger()


def refresh_scanner(scanner):
    scanner.run()
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
            with ui.tab_panel("Configuration"):
                ui.label("Server Configuration")
                self.config_table = config_table()
            with ui.tab_panel("Log"):
                ui.label("Server Logs")
                self.ui_logger = ui_logger()

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
