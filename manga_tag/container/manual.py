import time

from manga_tag.container.base import BaseContainer


class ManualContainer(BaseContainer):
    def _info(self):
        print("Container running in Manual Scan mode.")
        print("Manual scans are triggered through the container console.")
        print("Available manual modes: 'auto', 'manual', 'retag'.")

    def _run(self):
        while True:
            time.sleep(600)
