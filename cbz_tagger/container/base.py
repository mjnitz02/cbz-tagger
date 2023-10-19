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
