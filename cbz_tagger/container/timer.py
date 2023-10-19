import time

from cbz_tagger.common.env import AppEnv
from cbz_tagger.container.base import BaseContainer
from cbz_tagger.container.cbz_scanner import CbzScanner


class TimerContainer(BaseContainer):
    def __init__(self):
        super().__init__()
        self.scanner = CbzScanner(add_missing=False)

    def _info(self):
        print("Container running in Timer Scan mode.")
        print("Manual scans can also be triggered through the container console.")
        print(f"Timer Monitoring with {AppEnv.TIMER_DELAY}s delay: {AppEnv.DOWNLOADS}")

    def _run(self):
        self.scanner.run()
        while True:
            time.sleep(AppEnv.TIMER_DELAY)
            self.scanner.run()
