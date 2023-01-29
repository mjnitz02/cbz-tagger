from abc import ABC

from cbz_tagger.scanner.manga_scanner import MangaScanner


class BaseContainer:
    def __init__(self):
        self.scanner = None

    def run(self):
        self._info()
        self._run()

    def _info(self):
        raise NotImplementedError("Must be implemented by descendents")

    def _run(self):
        raise NotImplementedError("Must be implemented by descendents")


class BaseAutoContainer(BaseContainer, ABC):
    def __init__(self):
        super().__init__()
        self.scanner = MangaScanner({"auto": True})
