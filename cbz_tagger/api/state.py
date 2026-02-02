"""Application state management for FastAPI."""

import logging
from datetime import datetime
from queue import Queue
from threading import Lock

from cbz_tagger.database.file_scanner import FileScanner

logger = logging.getLogger()


class LogHandler(logging.Handler):
    """Custom log handler that stores logs in memory for API access."""

    def __init__(self, max_logs: int = 1000):
        super().__init__()
        self.logs: Queue = Queue(maxsize=max_logs)

    def emit(self, record):
        """Emit a log record."""
        try:
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created),
                "level": record.levelname,
                "message": self.format(record),
            }
            # If queue is full, remove oldest
            if self.logs.full():
                try:
                    self.logs.get_nowait()
                except Exception:
                    pass
            self.logs.put_nowait(log_entry)
        except Exception:
            self.handleError(record)

    def get_logs(self, limit: int = 100) -> list[dict]:
        """Get recent logs."""
        temp_logs = []

        # Get all logs from queue
        while not self.logs.empty():
            try:
                log = self.logs.get_nowait()
                temp_logs.append(log)
            except Exception:
                break

        # Put them back and return limited set
        for log in temp_logs:
            try:
                self.logs.put_nowait(log)
            except Exception:
                pass

        # Return most recent logs
        return temp_logs[-limit:] if len(temp_logs) > limit else temp_logs

    def clear_logs(self):
        """Clear all logs."""
        while not self.logs.empty():
            try:
                self.logs.get_nowait()
            except Exception:
                break


class AppState:
    """Application state singleton."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Create singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize application state."""
        if self._initialized:
            return

        self.scanner: FileScanner | None = None
        self.scanning_state = False
        self.first_scan = True
        self.last_scan_time: datetime | None = None
        self.log_handler = LogHandler()

        # Add log handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)

        self._initialized = True
        logger.info("Application state initialized")

    def initialize_scanner(self, scanner: FileScanner):
        """Initialize the file scanner."""
        self.scanner = scanner
        logger.info("Scanner initialized in app state")

    def can_use_database(self) -> bool:
        """Check if database is available."""
        return not self.scanning_state

    def lock_database(self):
        """Lock database for operations."""
        self.scanning_state = True
        logger.debug("Database locked")

    def unlock_database(self):
        """Unlock database after operations."""
        self.scanning_state = False
        logger.debug("Database unlocked")

    def reload_scanner(self):
        """Reload scanner from disk."""
        if self.scanner:
            self.scanner.reload_scanner()
            logger.debug("Scanner reloaded")

    def get_scanner_state(self) -> list[dict]:
        """Get current scanner state."""
        if self.scanner:
            self.reload_scanner()
            return self.scanner.to_state()
        return []

    def get_logs(self, limit: int = 100) -> list[dict]:
        """Get recent logs."""
        return self.log_handler.get_logs(limit)

    def clear_logs(self):
        """Clear all logs."""
        self.log_handler.clear_logs()
        logger.info("Logs cleared")


# Global state instance
app_state = AppState()
