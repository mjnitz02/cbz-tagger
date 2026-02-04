import os
from collections import deque


class FileLogReader:
    """A utility class for reading log files."""

    def __init__(self, log_file_path: str) -> None:
        self.log_file_path = log_file_path

    def read_last_lines(self, max_lines: int = 1000) -> str:
        """Read the last N lines from the log file.

        Args:
            max_lines: Maximum number of lines to read from the end of the file

        Returns:
            String containing the last N lines of the log file
        """
        if not os.path.exists(self.log_file_path):
            return ""

        try:
            with open(self.log_file_path, encoding="utf-8") as f:
                # Use deque to efficiently keep only the last N lines
                lines = deque(f, maxlen=max_lines)
                return "".join(lines)
        except Exception:  # pylint: disable=broad-except
            return f"Error reading log file: {self.log_file_path}"

    def clear_log_file(self) -> None:
        """Clear the contents of the log file."""
        if os.path.exists(self.log_file_path):
            try:
                with open(self.log_file_path, "w", encoding="utf-8") as f:
                    f.truncate(0)
            except Exception:  # pylint: disable=broad-except
                pass
