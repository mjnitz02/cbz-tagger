import asyncio
import logging
from datetime import datetime

from nicegui import ui

from cbz_tagger.common.env import AppEnv
from cbz_tagger.database.file_scanner import FileScanner

logger = logging.getLogger()


class Backend:
    @classmethod
    def get_scanner(cls):
        env = AppEnv()
        scanner = FileScanner(
            config_path=env.CONFIG_PATH,
            scan_path=env.SCAN_PATH,
            storage_path=env.STORAGE_PATH,
            environment=env.get_user_environment(),
        )
        return scanner

    def refresh(self):
        scanner = self.get_scanner()
        scanner.refresh()

    @classmethod
    def get_scanner_state(cls):
        scanner = cls.get_scanner()
        state = scanner.entity_database.to_state()
        formatted_state = []
        for item in state:
            if len(item["entity_name"]) > 50:
                item["entity_name"] = item["entity_name"][:50] + "..."
            formatted_state.append(item)
        return formatted_state


class LogElementHandler(logging.Handler):
    """A logging handler that emits messages to a log element."""

    def __init__(self, element: ui.log, level: int = logging.DEBUG) -> None:
        self.element = element
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        # noinspection PyBroadException
        try:
            msg = f"{record.levelname}:{record.filename}:{record.funcName}:{self.format(record)}"
            self.element.push(msg)
        except Exception:  # pylint: disable=broad-except
            self.handleError(record)


class CbzGui:
    def __init__(self):
        self.backend = Backend()
        self.table = None

        with ui.header().classes(replace="row items-center"):
            # pylint: disable=unnecessary-lambda
            ui.button(icon="menu").props("flat color=white")
            # ui.button(on_click=lambda: left_drawer.toggle(), icon="menu").props("flat color=white")
            ui.html("<h2><strong>CBZ Tagger GUI v0.1 </strong></h2>")
            ui.space()
            with ui.tabs() as tabs:
                ui.tab("Series")
                ui.tab("Log")
            ui.space()

        with ui.footer(value=True):
            ui.label("Footer")

        with ui.left_drawer().classes("bg-blue-100") as left_drawer:
            ui.label("Side menu")
            ui.button("Refresh Database", on_click=self.refresh)
            ui.button("Refresh Table", on_click=self.refresh_table)

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

    def refresh_table(self):
        state = self.backend.get_scanner_state()
        self.table.rows = state
        ui.notify("Series GUI Refreshed")

    async def refresh(self):
        ui.notify("Refreshing database... please wait")
        logger.warning(datetime.now().strftime("%X.%f")[:-5])
        logger.info("info")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.backend.refresh)
        self.refresh_table()
        ui.notify("Series Database Refreshed")


gui = CbzGui()
ui.run()
