"""Main Reflex application entry point."""

import asyncio
import logging

import reflex as rx

from cbz_tagger.common.env import AppEnv
from cbz_tagger.database.file_scanner import FileScanner
from cbz_tagger.reflex_gui.states.base_state import BaseState
from cbz_tagger.reflex_gui.utils.log_handler import setup_file_logging

logger = logging.getLogger()

# Set up file logging for GUI
LOG_FILE_PATH = "/tmp/cbz_tagger_gui.log"


def create_app(scanner: FileScanner | None = None) -> rx.App:
    """Create and configure the Reflex application.

    Args:
        scanner: Optional FileScanner instance. If None, will be created from environment.

    Returns:
        Configured Reflex app
    """
    env = AppEnv()

    # Set up file logging
    setup_file_logging(LOG_FILE_PATH, level=env.LOG_LEVEL)
    logger.info("File logging initialized at %s", LOG_FILE_PATH)

    # Initialize scanner if not provided
    if scanner is None:
        scanner = FileScanner(
            config_path=env.CONFIG_PATH,
            scan_path=env.SCAN_PATH,
            storage_path=env.STORAGE_PATH,
            add_missing=True,
            environment=env.get_user_environment(),
        )
        logger.info("Scanner created in reflex_app")

    # Initialize BaseState with scanner
    BaseState.initialize_scanner(scanner)

    # Create Reflex app
    app = rx.App(
        stylesheets=[
            "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
        ],
    )

    # Import pages (this registers routes)
    # We import here to avoid circular imports
    from cbz_tagger.reflex_gui.pages import config
    from cbz_tagger.reflex_gui.pages import logs
    from cbz_tagger.reflex_gui.pages import manage
    from cbz_tagger.reflex_gui.pages import series

    # Add pages
    app.add_page(series.series_page, route="/", title="CBZ Tagger - Series")
    app.add_page(manage.manage_page, route="/manage", title="CBZ Tagger - Manage")
    app.add_page(config.config_page, route="/config", title="CBZ Tagger - Config")
    app.add_page(logs.logs_page, route="/logs", title="CBZ Tagger - Logs")

    # Register background timer task
    env = AppEnv()
    timer_delay = env.TIMER_DELAY

    async def scanner_timer_task():
        """Background task to periodically refresh the scanner."""
        # Import SeriesState here to avoid circular import

        # Skip first run (first_scan logic)
        logger.info("Scanner timer task started with delay: %s seconds", timer_delay)
        await asyncio.sleep(timer_delay)
        logger.debug("Timer setup scan triggered. Skipping startup run.")

        while True:
            await asyncio.sleep(timer_delay)

            if BaseState.is_database_locked():
                logger.debug("Database locked, skipping timer refresh")
                continue

            try:
                logger.debug("Timer: Refreshing database...")
                BaseState.lock_database()

                # Run scanner refresh in executor
                loop = asyncio.get_event_loop()

                def run_scanner(scanner):
                    scanner.run()
                    return scanner

                scanner_instance = BaseState.get_scanner()
                await loop.run_in_executor(None, run_scanner, scanner_instance)
                logger.info("Timer: Database refreshed successfully")

            except Exception as e:
                logger.error("Timer: Error refreshing database: %s", e)
            finally:
                BaseState.unlock_database()

    # Register the timer task
    app.register_lifespan_task(scanner_timer_task)

    logger.info("Reflex app created successfully")
    return app


# For running with `reflex run`
app = create_app()
