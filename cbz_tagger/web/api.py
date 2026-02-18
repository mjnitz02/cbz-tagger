import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from cbz_tagger.common.enums import Emoji
from cbz_tagger.common.env import AppEnv
from cbz_tagger.common.plugins import Plugins
from cbz_tagger.database.file_scanner import FileScanner
from cbz_tagger.entities.metadata_entity import MetadataEntity

logger = logging.getLogger(__name__)

# Initialize the scanner from environment
env = AppEnv()
scanner = FileScanner(
    config_path=os.path.abspath(env.CONFIG_PATH),
    scan_path=os.path.abspath(env.SCAN_PATH),
    storage_path=os.path.abspath(env.STORAGE_PATH),
    environment=env.get_user_environment(),
)

# Simple in-memory state storage (replaces NiceGUI app.storage)
_app_state = {"scanning_state": False, "background_timer_started": False}


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(_: FastAPI):
    """Manage application lifespan events."""
    # Startup: Initialize background tasks
    if not _app_state["background_timer_started"]:
        timer_delay = env.TIMER_DELAY
        logger.info("Starting background scanner timer with delay: %s seconds", timer_delay)
        _app_state["background_timer_started"] = True

        async def background_refresh():
            """Background task that periodically refreshes the scanner."""
            # Skip first run - wait for the initial delay
            await asyncio.sleep(timer_delay)

            while True:
                try:
                    logger.info("Starting background scanner refresh at %s", datetime.now())
                    # Call the refresh operation directly instead of making an HTTP request
                    await run_scanner_operation(refresh_scanner_operation)
                    logger.info("Background scanner refresh completed at %s", datetime.now())
                except Exception as e:
                    logger.error("Error in background scanner refresh: %s", e)

                # Wait for the next cycle
                await asyncio.sleep(timer_delay)

        # Start the background task
        asyncio.create_task(background_refresh())
        logger.info("Background scanner timer started successfully")

    yield  # Application is running

    # Shutdown: Cleanup if needed
    logger.info("Shutting down application")


# Create the FastAPI app with lifespan handler
app = FastAPI(title="CBZ Tagger API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response bodies
class AddSeriesRequest(BaseModel):
    entity_name: str
    entity_id: str
    backend: dict[str, str] | None = None
    enable_tracking: bool = True
    mark_all_tracked: bool = False


class SeriesSearchResult(BaseModel):
    entity_id: str
    title: str
    alt_title: str | None
    all_titles: list[str]
    created_at_year: int
    age_rating: str
    display_name: str  # Formatted for display in UI


# Helper functions
def is_scanner_busy() -> bool:
    """Check if the scanner is currently busy."""
    return _app_state.get("scanning_state", False)


def lock_scanner():
    """Lock the scanner to prevent concurrent operations."""
    _app_state["scanning_state"] = True


def unlock_scanner():
    """Unlock the scanner after an operation completes."""
    _app_state["scanning_state"] = False


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
    chapters = scanner.entity_database.chapters.database.get(entity_id, [])
    return [
        {
            "entity_id": chapter.entity_id,
            "chapter_number": chapter.chapter_number,
        }
        for chapter in (chapters if chapters is not None else [])
    ]


# API Endpoints
@app.get("/api/scanner/status")
async def get_scanner_status():
    """Get the current status of the scanner."""
    return {
        "busy": is_scanner_busy(),
        "scanner_initialized": scanner is not None,
    }


@app.post("/api/scanner/refresh")
async def refresh_scanner():
    """Refresh the scanner database."""
    await run_scanner_operation(refresh_scanner_operation)
    return {"message": "Scanner refresh completed successfully"}


@app.post("/api/scanner/reload")
async def reload_scanner():
    """Reload the scanner to refresh its internal state."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, reload_scanner_operation)
    return {"message": "Scanner reloaded successfully"}


@app.get("/api/scanner/state")
async def get_scanner_state():
    """Get the current state of the scanner."""
    loop = asyncio.get_event_loop()
    state = await loop.run_in_executor(None, get_scanner_state_operation)
    return {"state": state}


@app.get("/api/scanner/series")
async def get_series_list():
    """Get the list of all series."""
    loop = asyncio.get_event_loop()
    series_list = await loop.run_in_executor(None, get_series_list_operation)
    return {"series": [{"name": name, "entity_id": entity_id} for name, entity_id in series_list]}


@app.get("/api/scanner/series/{entity_id}/chapters")
async def get_series_chapters(entity_id: str):
    """Get chapters for a specific series."""
    loop = asyncio.get_event_loop()
    chapters = await loop.run_in_executor(None, get_chapters_operation, entity_id)
    return {"chapters": chapters}


@app.get("/api/scanner/search-series")
async def search_series(title: str):
    """Search for series by title using MangaDex API."""
    if not title or len(title.strip()) == 0:
        raise HTTPException(status_code=400, detail="Title query parameter is required and cannot be empty")

    def search_operation():
        """Search for series using MetadataEntity."""
        return MetadataEntity.from_server_url(query_params={"title": title})

    # Run the search in an executor to avoid blocking
    loop = asyncio.get_event_loop()
    meta_entries = await loop.run_in_executor(None, search_operation)

    # Convert MetadataEntity objects to serializable dictionaries
    results = []
    for manga in meta_entries:
        result = SeriesSearchResult(
            entity_id=manga.entity_id,
            title=manga.title or "",
            alt_title=manga.alt_title,
            all_titles=manga.all_titles,
            created_at_year=manga.created_at.year,
            age_rating=manga.age_rating,
            display_name=f"{manga.title} ({manga.alt_title}) - {manga.created_at.year} - {manga.age_rating}",
        )
        results.append(result)

    return {"results": results}


@app.post("/api/scanner/add-series")
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


@app.delete("/api/scanner/series/{entity_id}")
async def delete_series(entity_id: str, entity_name: str):
    """Delete a series from the scanner."""
    await run_scanner_operation(delete_series_operation, entity_id, entity_name)
    return {"message": f"Series '{entity_name}' deleted successfully"}


@app.delete("/api/scanner/chapter/{entity_id}/{chapter_id}")
async def delete_chapter_tracking(entity_id: str, chapter_id: str):
    """Delete chapter tracking for a specific chapter."""
    await run_scanner_operation(delete_chapter_tracking_operation, entity_id, chapter_id)
    return {"message": "Chapter tracking deleted successfully"}


@app.post("/api/scanner/clean-orphaned")
async def clean_orphaned_files():
    """Clean orphaned files."""
    await run_scanner_operation(clean_orphaned_files_operation)
    return {"message": "Orphaned files cleaned successfully"}


@app.get("/api/enums/emoji")
async def get_emoji_enum():
    """Get the Emoji enum values."""
    return Emoji.to_api()


@app.get("/api/enums/plugins")
async def get_plugins_enum():
    """Get the Plugins enum values and list."""
    return Plugins.to_api()


@app.get("/api/enums/env")
async def get_env_config():
    """Get the AppEnv configuration values."""
    return env.to_api()
