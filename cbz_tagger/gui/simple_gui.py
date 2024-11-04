import asyncio
import logging
from datetime import datetime

from nicegui import ui

from cbz_tagger.common.env import AppEnv
from cbz_tagger.common.log_element_handler import LogElementHandler

logger = logging.getLogger()


def refresh_scanner(scanner):
    scanner.refresh()


class SimpleGui:
    def __init__(self, scanner):
        self.env = AppEnv()
        self.scanning_state = False
        self.scanner = scanner
        self.table = None

        with ui.left_drawer().classes("bg-blue-100") as left_drawer:
            ui.label("Side menu")
            ui.button("Refresh Database", on_click=self.refresh)
            ui.button("Refresh Table", on_click=self.refresh_table)

        with ui.header().classes(replace="row items-center"):
            # pylint: disable=unnecessary-lambda
            ui.button(on_click=lambda: left_drawer.toggle(), icon="menu").props("flat color=white")
            ui.html("<h2><strong>CBZ Tagger GUI v0.1 </strong></h2>")
            ui.space()
            with ui.tabs() as tabs:
                ui.tab("Series")
                ui.tab("Log")
            ui.space()

        with ui.footer(value=True):
            ui.label("Footer")

        with ui.tab_panels(tabs, value="Series").classes("w-full"):
            with ui.tab_panel("Series"):
                self.series_tab()
            with ui.tab_panel("Log"):
                ui.label("Show logs")
                log = ui.log(max_lines=1000).classes("w-full").style("height: 70vh")
                handler = LogElementHandler(log)
                handler.setLevel(logging.INFO)
                logger.addHandler(handler)
                # ui.context.client.on_disconnect(lambda: logger.removeHandler(handler))

        logger.info("UI scan timer started with delay: %s", self.env.TIMER_DELAY)
        ui.timer(self.env.TIMER_DELAY, self.refresh_on_timer)

    def series_tab(self):
        columns = [
            {
                "name": "entity_name",
                "label": "Entity Name",
                "field": "entity_name",
                "required": True,
                "align": "left",
                "sortable": True,
            },
            {"name": "entity_id", "label": "Entity ID", "field": "entity_id", "sortable": True},
            {"name": "updated", "label": "Metadata Updated", "field": "updated", "sortable": True},
            {"name": "latest_chapter", "label": "Latest Chapter", "field": "latest_chapter", "sortable": True},
            {
                "name": "latest_chapter_date",
                "label": "Chapter Updated",
                "field": "latest_chapter_date",
                "sortable": True,
            },
        ]
        self.table = ui.table(columns=columns, rows=[], row_key="entity_name")
        self.refresh_table()

    def get_scanner_state(self):
        state = self.scanner.entity_database.to_state()
        formatted_state = []
        for item in state:
            if len(item["entity_name"]) > 50:
                item["entity_name"] = item["entity_name"][:50] + "..."
            formatted_state.append(item)
        return formatted_state

    def refresh_table(self):
        state = self.get_scanner_state()
        self.table.rows = state
        ui.notify("Series GUI Refreshed")

    async def refresh_on_timer(self):
        await self.refresh()

    async def refresh(self):
        if self.scanning_state:
            ui.notify("Scanning in progress already...")
            return
        self.scanning_state = True
        ui.notify("Refreshing database... please wait")
        logger.warning(datetime.now().strftime("%X.%f")[:-5])
        logger.info("info")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, refresh_scanner, self.scanner)
        self.refresh_table()
        ui.notify("Series Database Refreshed")
        self.scanning_state = False
