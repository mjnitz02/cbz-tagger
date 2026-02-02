"""Scanner operations router."""

import asyncio
import logging

from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import HTTPException

from cbz_tagger.api.models import ScannerStatusResponse
from cbz_tagger.api.models import StatusResponse
from cbz_tagger.api.state import app_state

logger = logging.getLogger()
router = APIRouter(prefix="/scanner", tags=["scanner"])


def run_scanner():
    """Run the scanner synchronously."""
    if app_state.scanner:
        app_state.scanner.run()


async def refresh_scanner_async():
    """Refresh scanner in background thread."""
    try:
        app_state.lock_database()
        app_state.reload_scanner()

        logger.info("Starting background scanner refresh...")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_scanner)

        app_state.reload_scanner()
        logger.info("Scanner refresh completed")
    except Exception as e:
        logger.error("Error during scanner refresh: %s", str(e))
        raise
    finally:
        app_state.unlock_database()


@router.post("/run", response_model=StatusResponse)
async def trigger_scan(background_tasks: BackgroundTasks):
    """
    Trigger a manual scan of the database.

    This will run the scanner in the background and update all tracked series.
    """
    if not app_state.scanner:
        raise HTTPException(status_code=500, detail="Scanner not initialized")

    if not app_state.can_use_database():
        raise HTTPException(status_code=409, detail="Scanner is currently running, please wait")

    # Add the scan task to background tasks
    background_tasks.add_task(refresh_scanner_async)

    return StatusResponse(success=True, message="Scanner refresh started in background")


@router.get("/status", response_model=ScannerStatusResponse)
async def get_scanner_status():
    """
    Get the current status of the scanner.

    Returns whether the scanner is idle, scanning, or locked.
    """
    if not app_state.scanner:
        raise HTTPException(status_code=500, detail="Scanner not initialized")

    from cbz_tagger.api.models import ScannerStatus

    status = ScannerStatus.SCANNING if app_state.scanning_state else ScannerStatus.IDLE

    return ScannerStatusResponse(
        status=status, is_first_scan=app_state.first_scan, last_scan_time=app_state.last_scan_time
    )


@router.post("/clean-orphaned", response_model=StatusResponse)
async def clean_orphaned_files():
    """
    Clean orphaned cover files from the database.

    This removes cover files that are no longer associated with any series.
    """
    if not app_state.scanner:
        raise HTTPException(status_code=500, detail="Scanner not initialized")

    if not app_state.can_use_database():
        raise HTTPException(status_code=409, detail="Database is currently locked, please wait")

    try:
        app_state.lock_database()
        app_state.scanner.entity_database.remove_orphaned_covers()
        app_state.reload_scanner()
        logger.info("Orphaned files cleaned")

        return StatusResponse(success=True, message="Orphaned files removed successfully")
    except Exception as e:
        logger.error("Error cleaning orphaned files: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error cleaning orphaned files: {str(e)}") from e
    finally:
        app_state.unlock_database()
