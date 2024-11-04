import logging

from nicegui import ui


class LogElementHandler(logging.Handler):
    """A logging handler that emits messages to a log element."""

    def __init__(self, element: ui.log, level: int = logging.DEBUG) -> None:
        self.element = element
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        # noinspection PyBroadException
        try:
            msg = f"{record.levelname}:{record.filename}:{record.funcName}:{self.format(record)}"
            self.element.push(msg)
        except Exception:  # pylint: disable=broad-except
            self.handleError(record)
