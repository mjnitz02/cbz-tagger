from cbz_tagger.cbz_entity.cbz_scanner import CbzScanner


class BaseContainer:
    config_path: str
    scan_path: str
    storage_path: str
    timer_delay: int
    scanner: CbzScanner

    def __init__(self, config_path, scan_path, storage_path, timer_delay):
        self.config_path = config_path
        self.scan_path = scan_path
        self.storage_path = storage_path
        self.timer_delay = timer_delay
        self.scanner = CbzScanner(
            config_path=self.config_path, scan_path=self.scan_path, storage_path=self.storage_path
        )

    def run(self):
        self._info()
        self._run()

    def _info(self):
        raise NotImplementedError("Must be implemented by descendents")

    def _run(self):
        raise NotImplementedError("Must be implemented by descendents")
