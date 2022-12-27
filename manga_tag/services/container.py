import time

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from manga_tag.common.enums import ContainerMode, AppEnv
from manga_tag.services.manga_scanner import MangaScanner


class Container(object):
    def __init__(self):
        if AppEnv.timer_mode:
            self.mode = ContainerMode.TIMER
        elif AppEnv.continuous_mode:
            self.mode = ContainerMode.CONTINUOUS
        else:
            self.mode = ContainerMode.MANUAL

        self.scanner = None

    def run(self):
        if self.mode == ContainerMode.TIMER:
            self.timer()
        elif self.mode == ContainerMode.CONTINUOUS:
            self.continuous()
        else:
            self.manual()

    def initial_scan(self):
        print("Running initial scan.")
        self.scanner = MangaScanner({"auto": True})
        time.sleep(5)
        self.scanner.run()

    def timer(self):
        print("Container running in Timer Scan mode.")
        print("Manual scans can also be triggered through the container console.")
        print("Available manual modes: 'auto', 'manual', 'retag'.")

        self.initial_scan()

        print(
            "Timer Monitoring with {}s delay: {}".format(
                AppEnv.timer_mode_delay, AppEnv.downloads_path
            )
        )
        while True:
            time.sleep(AppEnv.timer_mode_delay)
            self.scanner.run()

    def continuous(self):
        print("Container running in Continuous Scan mode.")
        print("Manual scans can also be triggered through the container console.")
        print("Available manual modes: 'auto', 'manual', 'retag'.")

        self.initial_scan()

        print("Continous Monitoring: {}".format(AppEnv.downloads_path))
        my_event_handler = PatternMatchingEventHandler(["*"], None, False, True)

        def run_scan(event):
            print("Change detected - waiting to scan...")
            time.sleep(5)
            self.scanner.run()

        my_event_handler.on_created = run_scan
        my_event_handler.on_modified = run_scan

        my_observer = Observer()
        my_observer.schedule(my_event_handler, AppEnv.downloads_path, recursive=True)
        my_observer.start()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            my_observer.stop()
            my_observer.join()

    def manual(self):
        print("Container running in Manual Scan mode.")
        print("Manual scans are triggered through the container console.")
        print("Available manual modes: 'auto', 'manual', 'retag'.")
        while True:
            time.sleep(600)
