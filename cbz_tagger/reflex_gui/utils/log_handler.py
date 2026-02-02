"""File-based log handler for Reflex GUI."""

import logging


class FileLogHandler(logging.Handler):
    """A logging handler that writes to a file for GUI display."""

    def __init__(self, filepath: str, level: int = logging.NOTSET) -> None:
        """Initialize the file log handler.

        Args:
            filepath: Path to the log file
            level: Logging level
        """
        self.filepath = filepath
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the file.

        Args:
            record: The log record to emit
        """
        try:
            msg = f"{record.levelname}:{record.filename}:{record.funcName}:{self.format(record)}\n"
            with open(self.filepath, "a") as f:
                f.write(msg)
        except Exception:  # pylint: disable=broad-except
            self.handleError(record)


def setup_file_logging(filepath: str, level: int = logging.INFO):
    """Set up file logging for the GUI.

    Args:
        filepath: Path to the log file
        level: Logging level
    """
    logger = logging.getLogger()
    handler = FileLogHandler(filepath, level=level)
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
