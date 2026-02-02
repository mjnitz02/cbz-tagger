"""Base state class with locking mechanism and shared scanner instance."""

import asyncio
import logging
from typing import Any
from typing import Callable

import reflex as rx

from cbz_tagger.database.file_scanner import FileScanner

logger = logging.getLogger()


class BaseState(rx.State):
    """Base state class for all Reflex GUI states.

    Provides:
    - Shared scanner instance (class-level, shared across all sessions)
    - Database locking mechanism (class-level, prevents concurrent operations)
    - Helper methods for running sync operations in executor
    - Notification system for user feedback
    """

    # Class-level shared state (shared across all sessions)
    _scanner: FileScanner | None = None
    _scanning_state: bool = False

    # Instance-level notification state
    notification_message: str = ""
    notification_severity: str = "info"  # "info", "success", "warning", "error"
    show_notification: bool = False

    @classmethod
    def initialize_scanner(cls, scanner: FileScanner):
        """Initialize the shared scanner instance.

        Should be called once at app startup.

        Args:
            scanner: The FileScanner instance to share across all sessions
        """
        cls._scanner = scanner
        logger.info("Scanner initialized in BaseState")

    @classmethod
    def get_scanner(cls) -> FileScanner:
        """Get the shared scanner instance.

        Returns:
            The shared FileScanner instance

        Raises:
            RuntimeError: If scanner hasn't been initialized
        """
        if cls._scanner is None:
            raise RuntimeError("Scanner not initialized. Call BaseState.initialize_scanner() first.")
        return cls._scanner

    @classmethod
    def is_database_locked(cls) -> bool:
        """Check if database is currently locked.

        Returns:
            True if database is locked, False otherwise
        """
        return cls._scanning_state

    @classmethod
    def lock_database(cls):
        """Lock the database to prevent concurrent operations."""
        cls._scanning_state = True
        logger.debug("Database locked")

    @classmethod
    def unlock_database(cls):
        """Unlock the database to allow operations."""
        cls._scanning_state = False
        logger.debug("Database unlocked")

    async def run_sync_operation(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Run a synchronous database operation in executor.

        This method handles the async/sync bridge for database operations.
        It checks the lock, runs the operation in an executor, and handles errors.

        Args:
            func: The synchronous function to run
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The result of the function call

        Raises:
            RuntimeError: If database is currently locked
        """
        if self.is_database_locked():
            self.notify("Database currently in use, please wait...", "warning")
            raise RuntimeError("Database is locked")

        self.lock_database()
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, func, *args, **kwargs)
            return result
        except Exception as e:
            logger.error("Error in sync operation: %s", e)
            self.notify(f"Error: {e}", "error")
            raise
        finally:
            self.unlock_database()

    def notify(self, message: str, severity: str = "info"):
        """Show a notification to the user.

        Args:
            message: The notification message
            severity: The notification severity ("info", "success", "warning", "error")
        """
        self.notification_message = message
        self.notification_severity = severity
        self.show_notification = True
        logger.info("%s: %s", severity.upper(), message)

    def clear_notification(self):
        """Clear the current notification."""
        self.show_notification = False
        self.notification_message = ""
