import logging
import os

from nicegui import app
from nicegui import ui

from cbz_tagger.database.file_scanner import FileScanner
from cbz_tagger.gui.simple_gui import SimpleGui

logger = logging.getLogger()


class GuiContainer:
    NICEGUI_DEBUG = False
    config_path: str
    scan_path: str
    storage_path: str
    timer_delay: int
    scanner: FileScanner

    def __init__(self, config_path, scan_path, storage_path, timer_delay, environment=None):
        self.config_path = config_path
        self.scan_path = scan_path
        self.storage_path = storage_path
        self.timer_delay = timer_delay
        self.scanner = FileScanner(
            config_path=self.config_path,
            scan_path=self.scan_path,
            storage_path=self.storage_path,
            environment=environment,
        )
        # Disable automatic adding of series
        self.scanner.add_missing = False

    def run(self):
        self._info()
        self._run()

    def _info(self):
        logger.info("Container running in GUI mode.")
        logger.info("Manual scans can also be triggered through the container console.")
        logger.info("Timer Monitoring with %s(s) delay: %s", self.timer_delay, self.scan_path)

    def _run(self):
        SimpleGui(self.scanner)
        root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        static_path = os.path.join(root_path, "static")
        app.add_static_files("/static", static_path)
        ui.run(reload=self.NICEGUI_DEBUG, favicon=os.path.join(static_path, "favicon.ico"))
