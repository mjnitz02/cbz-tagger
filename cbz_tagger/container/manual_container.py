import time

from cbz_tagger.container.base_container import BaseContainer


class ManualContainer(BaseContainer):
    def _info(self):
        print("Container running in Manual Scan mode.")
        print("Manual scans are triggered through the container console.")

    def _run(self):
        while True:
            time.sleep(600)
