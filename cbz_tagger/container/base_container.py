from cbz_tagger.container.file_scanner import FileScanner


class BaseContainer:
    config_path: str
    scan_path: str
    storage_path: str
    timer_delay: int
    scanner: FileScanner

    def __init__(self, config_path, scan_path, storage_path, timer_delay, environment=None):
        self.config_path = config_path
        self.scan_path = scan_path
        self.storage_path = storage_path
        self.timer_delay = timer_delay
        self.scanner = FileScanner(
            config_path=self.config_path,
            scan_path=self.scan_path,
            storage_path=self.storage_path,
            environment=environment,
        )

    def run(self):
        self._info()
        self._run()

    def _info(self):
        raise NotImplementedError("Must be implemented by descendents")

    def _run(self):
        raise NotImplementedError("Must be implemented by descendents")
