import time

from cbz_tagger.common.env import AppEnv
from cbz_tagger.container.base import BaseAutoContainer


class TimerContainer(BaseAutoContainer):
    def _info(self):
        print("Container running in Timer Scan mode.")
        print("Manual scans can also be triggered through the container console.")
        print("Available manual modes: 'auto', 'manual', 'retag'.")
        print(f"Timer Monitoring with {AppEnv.TIMER_DELAY}s delay: {AppEnv.DOWNLOADS}")

    def _run(self):
        self.scanner.run()
        while True:
            time.sleep(AppEnv.TIMER_DELAY)
            self.scanner.run()
