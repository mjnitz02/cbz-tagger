import time

from manga_tag.common.env import AppEnv
from manga_tag.container.base import BaseAutoContainer


class TimerContainer(BaseAutoContainer):
    def _info(self):
        print("Container running in Timer Scan mode.")
        print("Manual scans can also be triggered through the container console.")
        print("Available manual modes: 'auto', 'manual', 'retag'.")
        print(
            "Timer Monitoring with {}s delay: {}".format(
                AppEnv.timer_mode_delay, AppEnv.downloads_path
            )
        )

    def _run(self):
        self.scanner.run()
        while True:
            time.sleep(AppEnv.timer_mode_delay)
            self.scanner.run()
