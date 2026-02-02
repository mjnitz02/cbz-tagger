"""Reflex GUI container for CBZ Tagger."""

import logging
import subprocess
import sys

from cbz_tagger.container.base_container import BaseContainer
from cbz_tagger.reflex_gui.states.base_state import BaseState

logger = logging.getLogger()


class ReflexGuiContainer(BaseContainer):
    """Container for running CBZ Tagger with Reflex GUI.

    This container initializes the scanner and runs the Reflex app
    via subprocess to ensure proper Reflex initialization.
    """

    def __init__(self, config_path, scan_path, storage_path, timer_delay, environment=None):
        """Initialize the Reflex GUI container.

        Args:
            config_path: Path to configuration directory
            scan_path: Path to scan directory
            storage_path: Path to storage directory
            timer_delay: Timer delay in seconds
            environment: Environment variables dict
        """
        super().__init__(config_path, scan_path, storage_path, timer_delay, environment=environment)
        # Disable automatic adding of series
        self.scanner.add_missing = False

    def _info(self):
        """Log container information."""
        logger.info("Container running in Reflex GUI mode.")
        logger.info("Access the web interface at http://0.0.0.0:8080")
        logger.info("Timer Monitoring with %s(s) delay: %s", self.timer_delay, self.scan_path)

    def _run(self):
        """Run the Reflex application.

        Initializes the scanner in BaseState, then runs Reflex via subprocess.
        This ensures Reflex properly initializes its server infrastructure.
        """
        # Initialize scanner in BaseState so it's available to the app
        logger.info("Initializing scanner in BaseState...")
        BaseState.initialize_scanner(self.scanner)
        logger.info("Scanner initialized successfully")

        # Run Reflex via subprocess
        logger.info("Starting Reflex server...")
        logger.info("Access the web interface at http://0.0.0.0:8080")

        # Run reflex with production settings
        try:
            subprocess.run(
                [sys.executable, "-m", "reflex", "run", "--env", "prod", "--backend-only"],
                check=True,
                cwd="/app",
            )
        except subprocess.CalledProcessError as e:
            logger.error("Reflex process failed: %s", e)
            raise
        except KeyboardInterrupt:
            logger.info("Shutting down Reflex GUI container...")
