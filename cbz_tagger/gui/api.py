import asyncio
import logging
import os
from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from nicegui import app
from pydantic import BaseModel

from cbz_tagger.common.env import AppEnv
from cbz_tagger.database.file_scanner import FileScanner

logger = logging.getLogger()

# Initialize the scanner from environment
env = AppEnv()
scanner = FileScanner(
    config_path=os.path.abspath(env.CONFIG_PATH),
    scan_path=os.path.abspath(env.SCAN_PATH),
    storage_path=os.path.abspath(env.STORAGE_PATH),
    environment=env.get_user_environment(),
)

# Create the API router
router = APIRouter(prefix="/api/scanner", tags=["scanner"])


# Pydantic models for request bodies
class AddSeriesRequest(BaseModel):
    entity_name: str
    entity_id: str
    backend: dict[str, str] | None = None
    enable_tracking: bool = True
    mark_all_tracked: bool = False


# Helper functions
def is_scanner_busy() -> bool:
    """Check if the scanner is currently busy."""
    return app.storage.general.get("scanning_state", False)


def lock_scanner():
    """Lock the scanner to prevent concurrent operations."""
    app.storage.general["scanning_state"] = True


def unlock_scanner():
    """Unlock the scanner after an operation completes."""
    app.storage.general["scanning_state"] = False


async def run_scanner_operation(operation, *args, **kwargs):
    """Run a scanner operation asynchronously with proper locking."""
    if is_scanner_busy():
        raise HTTPException(status_code=409, detail="Scanner is currently busy. Please wait.")

    lock_scanner()
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, operation, *args, **kwargs)
        return result
    finally:
        unlock_scanner()


# Scanner operation functions
def refresh_scanner_operation():
    """Refresh the scanner by running a full scan."""
    scanner.run()


def add_series_operation(
    entity_name: str, entity_id: str, backend: dict | None, enable_tracking: bool, mark_all_tracked: bool
):
    """Add a new series to the scanner."""
    scanner.entity_database.add_entity(
        entity_name,
        entity_id,
        manga_name=None,
        backend=backend,
        update=True,
        track=enable_tracking,
        mark_as_tracked=mark_all_tracked,
    )


def delete_series_operation(entity_id: str, entity_name: str):
    """Delete a series from the scanner."""
    scanner.entity_database.delete_entity_id(entity_id, entity_name)


def delete_chapter_tracking_operation(entity_id: str, chapter_id: str):
    """Delete chapter tracking for a specific chapter."""
    scanner.entity_database.delete_chapter_entity_id_from_downloaded_chapters(entity_id, chapter_id)


def clean_orphaned_files_operation():
    """Clean orphaned files from the scanner."""
    scanner.entity_database.remove_orphaned_covers()


def reload_scanner_operation():
    """Reload the scanner to refresh its internal state."""
    scanner.reload_scanner()


def get_scanner_state_operation():
    """Get the current state of the scanner."""
    scanner.reload_scanner()
    return scanner.to_state()


def get_series_list_operation():
    """Get the list of all series in the database."""
    scanner.reload_scanner()
    return list(scanner.entity_database.entity_map.items())


def get_chapters_operation(entity_id: str):
    """Get chapters for a specific series."""
    scanner.reload_scanner()
    chapters = scanner.entity_database.chapters.get(entity_id, [])
    return [
        {
            "entity_id": chapter.entity_id,
            "chapter_number": chapter.chapter_number,
        }
        for chapter in (chapters if chapters is not None else [])
    ]


# API Endpoints
@router.get("/status")
async def get_scanner_status():
    """Get the current status of the scanner."""
    return {
        "busy": is_scanner_busy(),
        "scanner_initialized": scanner is not None,
    }


@router.post("/refresh")
async def refresh_scanner():
    """Refresh the scanner database."""
    await run_scanner_operation(refresh_scanner_operation)
    return {"message": "Scanner refresh completed successfully"}


@router.post("/reload")
async def reload_scanner():
    """Reload the scanner to refresh its internal state."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, reload_scanner_operation)
    return {"message": "Scanner reloaded successfully"}


@router.get("/state")
async def get_scanner_state():
    """Get the current state of the scanner."""
    loop = asyncio.get_event_loop()
    state = await loop.run_in_executor(None, get_scanner_state_operation)
    return {"state": state}


@router.get("/series")
async def get_series_list():
    """Get the list of all series."""
    loop = asyncio.get_event_loop()
    series_list = await loop.run_in_executor(None, get_series_list_operation)
    return {"series": [{"name": name, "entity_id": entity_id} for name, entity_id in series_list]}


@router.get("/series/{entity_id}/chapters")
async def get_series_chapters(entity_id: str):
    """Get chapters for a specific series."""
    loop = asyncio.get_event_loop()
    chapters = await loop.run_in_executor(None, get_chapters_operation, entity_id)
    return {"chapters": chapters}


@router.post("/add-series")
async def add_series(request: AddSeriesRequest):
    """Add a new series to the scanner."""
    await run_scanner_operation(
        add_series_operation,
        request.entity_name,
        request.entity_id,
        request.backend,
        request.enable_tracking,
        request.mark_all_tracked,
    )
    return {"message": f"Series '{request.entity_name}' added successfully"}


@router.delete("/series/{entity_id}")
async def delete_series(entity_id: str, entity_name: str):
    """Delete a series from the scanner."""
    await run_scanner_operation(delete_series_operation, entity_id, entity_name)
    return {"message": f"Series '{entity_name}' deleted successfully"}


@router.delete("/chapter/{entity_id}/{chapter_id}")
async def delete_chapter_tracking(entity_id: str, chapter_id: str):
    """Delete chapter tracking for a specific chapter."""
    await run_scanner_operation(delete_chapter_tracking_operation, entity_id, chapter_id)
    return {"message": "Chapter tracking deleted successfully"}


@router.post("/clean-orphaned")
async def clean_orphaned_files():
    """Clean orphaned files."""
    await run_scanner_operation(clean_orphaned_files_operation)
    return {"message": "Orphaned files cleaned successfully"}
