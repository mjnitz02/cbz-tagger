"""Background task scheduler for periodic scanner execution."""

import asyncio
import logging
from datetime import datetime

from cbz_tagger.api.state import app_state

logger = logging.getLogger()


class ScannerScheduler:
    """Scheduler for running scanner tasks periodically."""

    def __init__(self, delay_seconds: int = 3600):
        """
        Initialize the scanner scheduler.

        Args:
            delay_seconds: Time between scanner runs (default: 3600 = 1 hour)
        """
        self.delay_seconds = delay_seconds
        self.task = None
        self.is_running = False
        self.first_run = True

    async def run_scanner(self):
        """Run the scanner task."""
        if self.first_run:
            self.first_run = False
            logger.info("Timer setup - skipping first run")
            return

        if not app_state.scanner:
            logger.warning("Scanner not initialized, skipping scheduled run")
            return

        if not app_state.can_use_database():
            logger.warning("Database locked, skipping scheduled scanner run")
            return

        try:
            app_state.lock_database()
            app_state.reload_scanner()

            logger.info("Starting scheduled scanner refresh...")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, app_state.scanner.run)

            app_state.reload_scanner()
            app_state.last_scan_time = datetime.now()
            logger.info("Scheduled scanner refresh completed")
        except Exception as e:
            logger.error("Error during scheduled scanner run: %s", str(e))
        finally:
            app_state.unlock_database()

    async def scheduler_loop(self):
        """Main scheduler loop."""
        logger.info("Scanner scheduler started with delay: %d seconds", self.delay_seconds)

        while self.is_running:
            try:
                await self.run_scanner()
                await asyncio.sleep(self.delay_seconds)
            except asyncio.CancelledError:
                logger.info("Scanner scheduler cancelled")
                break
            except Exception as e:
                logger.error("Error in scheduler loop: %s", str(e))
                await asyncio.sleep(60)  # Wait a bit before retrying

    def start(self):
        """Start the scheduler."""
        if not self.is_running:
            self.is_running = True
            self.task = asyncio.create_task(self.scheduler_loop())
            logger.info("Scanner scheduler task created")

    async def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            self.is_running = False
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
            logger.info("Scanner scheduler stopped")


# Global scheduler instance
scheduler = ScannerScheduler()
