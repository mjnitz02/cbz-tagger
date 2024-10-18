import logging
import time

from cbz_tagger.container.base_container import BaseContainer

logger = logging.getLogger()


class TimerContainer(BaseContainer):
    def __init__(self, config_path, scan_path, storage_path, timer_delay, environment=None):
        super().__init__(config_path, scan_path, storage_path, timer_delay, environment=environment)
        # Disable automatic adding of series
        self.scanner.add_missing = False

    def _info(self):
        logger.info("Container running in Timer Scan mode.")
        logger.info("Manual scans can also be triggered through the container console.")
        logger.info("Timer Monitoring with %s(s) delay: %s", self.timer_delay, self.scan_path)

    def _run(self):
        self.scanner.run()
        while True:
            time.sleep(self.timer_delay)
            self.scanner.run()
