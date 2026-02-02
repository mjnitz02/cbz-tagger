import logging
import os

from nicegui import app
from nicegui import ui

from cbz_tagger.container.base_container import BaseContainer
from cbz_tagger.gui.simple_gui import SimpleGui

logger = logging.getLogger()


class GuiContainer(BaseContainer):
    NICEGUI_DEBUG = False

    def __init__(
        self, config_path, scan_path, storage_path, timer_delay, api_url="http://localhost:8000", environment=None
    ):
        super().__init__(config_path, scan_path, storage_path, timer_delay, environment=environment)
        self.api_url = api_url
        # Disable automatic adding of series
        self.scanner.add_missing = False

    def _info(self):
        logger.info("Container running in GUI mode.")
        logger.info("GUI connects to API at: %s", self.api_url)
        logger.info("Manual scans can be triggered through the GUI interface.")

    def _run(self):
        SimpleGui(api_base_url=self.api_url)
        root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        static_path = os.path.join(root_path, "static")
        app.add_static_files("/static", static_path)
        ui.run(reload=self.NICEGUI_DEBUG, favicon=os.path.join(static_path, "favicon.ico"))
