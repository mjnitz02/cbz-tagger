import time

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver

from cbz_tagger.common.env import AppEnv
from cbz_tagger.container.base import BaseAutoContainer


class ContinuousContainer(BaseAutoContainer):
    def _info(self):
        print("Container running in Continuous Scan mode.")
        print("Manual scans can also be triggered through the container console.")
        print("Available manual modes: 'auto', 'manual', 'retag'.")
        print("Continous Monitoring: {}".format(AppEnv.DOWNLOADS))

    def _run(self):
        self.initial_scan()
        my_event_handler = PatternMatchingEventHandler(["*"], None, False, True)

        def _run_scan(event):
            print("Change detected - waiting to scan...")
            time.sleep(5)
            self.scanner.run()

        my_event_handler.on_created = _run_scan
        my_event_handler.on_modified = _run_scan

        my_observer = Observer()
        my_observer.schedule(my_event_handler, AppEnv.DOWNLOADS, recursive=True)
        my_observer.start()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            my_observer.stop()
            my_observer.join()
