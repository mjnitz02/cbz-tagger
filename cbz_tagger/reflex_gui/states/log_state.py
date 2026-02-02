"""Log state for displaying server logs."""

import asyncio
import logging
from pathlib import Path

from cbz_tagger.reflex_gui.states.base_state import BaseState

logger = logging.getLogger()

# Log file path
LOG_FILE_PATH = "/tmp/cbz_tagger_gui.log"
MAX_LOG_LINES = 1000


class LogState(BaseState):
    """State for the logs page.

    Manages:
    - Display of server logs
    - Log file reading and refresh
    - Auto-refresh of logs
    """

    log_lines: list[str] = []
    is_auto_refresh: bool = True
    is_loading: bool = False

    async def refresh_logs(self):
        """Refresh logs from file."""
        self.is_loading = True

        try:

            def _read_logs():
                log_file = Path(LOG_FILE_PATH)
                if not log_file.exists():
                    return ["Log file not found. Logs will appear here once generated."]

                # Read last MAX_LOG_LINES lines
                with open(log_file) as f:
                    lines = f.readlines()
                    # Return last 1000 lines
                    return lines[-MAX_LOG_LINES:] if len(lines) > MAX_LOG_LINES else lines

            loop = asyncio.get_event_loop()
            lines = await loop.run_in_executor(None, _read_logs)
            self.log_lines = [line.strip() for line in lines if line.strip()]
            logger.debug("Logs refreshed: %d lines", len(self.log_lines))

        except Exception as e:
            logger.error("Error refreshing logs: %s", e)
            self.log_lines = [f"Error reading logs: {e}"]
        finally:
            self.is_loading = False

    async def clear_logs(self):
        """Clear the log file."""
        try:

            def _clear_logs():
                log_file = Path(LOG_FILE_PATH)
                if log_file.exists():
                    with open(log_file, "w") as f:
                        f.write("")

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _clear_logs)
            self.log_lines = []
            self.notify("Logs cleared", "success")
            logger.info("Log file cleared")

        except Exception as e:
            logger.error("Error clearing logs: %s", e)
            self.notify(f"Error clearing logs: {e}", "error")

    def toggle_auto_refresh(self):
        """Toggle auto-refresh of logs."""
        self.is_auto_refresh = not self.is_auto_refresh
