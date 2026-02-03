import logging
import os
import time

from nicegui import app
from nicegui import ui

from cbz_tagger.common.env import AppEnv
from cbz_tagger.database.file_scanner import FileScanner
from cbz_tagger.gui.simple_gui import SimpleGui

logger = logging.getLogger(__name__)


class Container:
    NICEGUI_DEBUG = False
    config_path: str
    scan_path: str
    storage_path: str
    timer_delay: int
    scanner: FileScanner

    def __init__(self):
        env = AppEnv()

        logger.info("Environment Variables:")
        logger.info(env.get_user_environment())
        logger.info("proxy_url: %s", env.PROXY_URL)
        self.timer_delay = env.TIMER_DELAY
        self.scan_path = os.path.abspath(env.SCAN_PATH)

        self.scanner = FileScanner(
            config_path=os.path.abspath(env.CONFIG_PATH),
            scan_path=self.scan_path,
            storage_path=os.path.abspath(env.STORAGE_PATH),
            environment=env.get_user_environment(),
        )
        # Disable automatic adding of series
        self.scanner.add_missing = False

    def run_gui(self):
        logger.info("Container running in GUI mode.")
        logger.info("Timer Monitoring with %s(s) delay: %s", self.timer_delay, self.scan_path)
        SimpleGui()
        root_path = os.path.dirname(os.path.abspath(__file__))
        static_path = os.path.join(root_path, "static")
        app.add_static_files("/static", static_path)
        ui.run(reload=self.NICEGUI_DEBUG, favicon=os.path.join(static_path, "favicon.ico"))

    def run_timer(self):
        logger.info("Container running in Timer Monitoring mode.")
        logger.info("Timer Monitoring with %s(s) delay: %s", self.timer_delay, self.scan_path)
        while True:
            self.scanner.run()
            time.sleep(self.timer_delay)

    def run_manual(self, **kwargs):
        logger.info("Container running in Manual Scan mode.")
        logger.info("Manual scans are triggered through the container console.")
        self.scanner.add_missing = True
        if len(kwargs) > 0:
            if kwargs.get("add"):
                self.scanner.add_tracked_entity()
            elif kwargs.get("remove"):
                self.scanner.remove_tracked_entity()
            elif kwargs.get("delete"):
                self.scanner.delete_entity()
            elif kwargs.get("refresh"):
                self.scanner.refresh()
        else:
            self.scanner.run()
