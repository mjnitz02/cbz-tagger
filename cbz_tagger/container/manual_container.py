import logging
import time

from cbz_tagger.container.base_container import BaseContainer

logger = logging.getLogger()


class ManualContainer(BaseContainer):
    def _info(self):
        logger.info("Container running in Manual Scan mode.")
        logger.info("Manual scans are triggered through the container console.")

    def _run(self):
        while True:
            time.sleep(600)
