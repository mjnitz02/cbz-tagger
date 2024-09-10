import time

from cbz_tagger.container.base_container import BaseContainer


class TimerContainer(BaseContainer):
    def __init__(self, config_path, scan_path, storage_path, timer_delay, environment=None):
        super().__init__(config_path, scan_path, storage_path, timer_delay, environment=environment)
        # Disable automatic adding of series
        self.scanner.cbz_database.add_missing = False

    def _info(self):
        print("Container running in Timer Scan mode.")
        print("Manual scans can also be triggered through the container console.")
        print(f"Timer Monitoring with {self.timer_delay}s delay: {self.scan_path}")

    def _run(self):
        self.scanner.run()
        while True:
            time.sleep(self.timer_delay)
            self.scanner.run()
