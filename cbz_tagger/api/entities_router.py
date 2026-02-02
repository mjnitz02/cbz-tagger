"""Entity management router."""

import asyncio
import logging

from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import HTTPException

from cbz_tagger.api.models import AddSeriesRequest
from cbz_tagger.api.models import ChapterItem
from cbz_tagger.api.models import ChaptersResponse
from cbz_tagger.api.models import DeleteChapterTrackingRequest
from cbz_tagger.api.models import DeleteSeriesRequest
from cbz_tagger.api.models import ManagedSeriesItem
from cbz_tagger.api.models import ManagedSeriesResponse
from cbz_tagger.api.models import MetadataSearchResult
from cbz_tagger.api.models import SearchSeriesRequest
from cbz_tagger.api.models import SearchSeriesResponse
from cbz_tagger.api.models import StatusResponse
from cbz_tagger.api.state import app_state
from cbz_tagger.entities.metadata_entity import MetadataEntity

logger = logging.getLogger()
router = APIRouter(prefix="/entities", tags=["entities"])


@router.post("/search", response_model=SearchSeriesResponse)
async def search_series(request: SearchSeriesRequest):
    """
    Search for series by name using the metadata server.

    Returns a list of matching series with their metadata.
    """
    if len(request.search_term) == 0:
        raise HTTPException(status_code=400, detail="Search term cannot be empty")

    try:
        meta_entries = MetadataEntity.from_server_url(query_params={"title": request.search_term})

        results = [
            MetadataSearchResult(
                entity_id=manga.entity_id,
                title=manga.title,
                alt_title=manga.alt_title,
                year=manga.created_at.year,
                age_rating=manga.age_rating,
                all_titles=manga.all_titles,
                display_name=f"{manga.title} ({manga.alt_title}) - {manga.created_at.year} - {manga.age_rating}",
            )
            for manga in meta_entries
        ]

        return SearchSeriesResponse(results=results, total_count=len(results))
    except Exception as e:
        logger.error("Error searching for series: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error searching for series: {str(e)}") from e


async def add_series_task(
    entity_name: str, entity_id: str, backend: dict | None, enable_tracking: bool, mark_all_tracked: bool
):
    """Add series in background thread."""
    try:
        app_state.lock_database()
        app_state.reload_scanner()

        logger.info("Adding new series: %s (%s)", entity_name, entity_id)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            app_state.scanner.entity_database.add_entity,
            entity_name,
            entity_id,
            None,  # manga_name
            backend,
            True,  # update
            enable_tracking,
            mark_all_tracked,
        )

        app_state.reload_scanner()
        logger.info("Series added successfully: %s", entity_name)
    except Exception as e:
        logger.error("Error adding series: %s", str(e))
        raise
    finally:
        app_state.unlock_database()


@router.post("/add", response_model=StatusResponse)
async def add_series(request: AddSeriesRequest, background_tasks: BackgroundTasks):
    """
    Add a new series to the database.

    This will add the series and optionally mark all chapters as tracked.
    """
    if not app_state.scanner:
        raise HTTPException(status_code=500, detail="Scanner not initialized")

    if not app_state.can_use_database():
        raise HTTPException(status_code=409, detail="Database is currently locked, please wait")

    # Prepare backend configuration
    backend = None
    if request.backend_plugin.value != "MDX":
        if not request.backend_id:
            raise HTTPException(status_code=400, detail="Backend ID is required for non-MDX plugins")
        backend = {"plugin_type": request.backend_plugin.value, "plugin_id": request.backend_id}

    # Add task to background
    background_tasks.add_task(
        add_series_task,
        request.entity_name,
        request.entity_id,
        backend,
        request.enable_tracking,
        request.mark_all_tracked,
    )

    return StatusResponse(
        success=True,
        message=f"Adding series '{request.entity_name}' in background",
        data={"entity_id": request.entity_id},
    )


@router.get("/managed", response_model=ManagedSeriesResponse)
async def get_managed_series():
    """
    Get all series currently managed in the database.

    Returns a list of all tracked series with their IDs and names.
    """
    if not app_state.scanner:
        raise HTTPException(status_code=500, detail="Scanner not initialized")

    try:
        app_state.reload_scanner()
        series_map = app_state.scanner.entity_database.entity_map.items()

        series = [
            ManagedSeriesItem(entity_id=entity_id, entity_name=name, display_name=f"{name} ({entity_id})")
            for name, entity_id in series_map
        ]

        return ManagedSeriesResponse(series=series, total_count=len(series))
    except Exception as e:
        logger.error("Error getting managed series: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error getting managed series: {str(e)}") from e


@router.get("/managed/{entity_id}/chapters", response_model=ChaptersResponse)
async def get_series_chapters(entity_id: str):
    """
    Get all chapters for a specific series.

    Returns a list of chapters with their tracking status.
    """
    if not app_state.scanner:
        raise HTTPException(status_code=500, detail="Scanner not initialized")

    try:
        app_state.reload_scanner()

        # Find entity name
        entity_name = None
        for name, eid in app_state.scanner.entity_database.entity_map.items():
            if eid == entity_id:
                entity_name = name
                break

        if not entity_name:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        chapters = app_state.scanner.entity_database.chapters.get(entity_id, [])

        chapter_items = [
            ChapterItem(
                entity_id=entity_id,
                chapter_id=chapter.entity_id,
                chapter_number=chapter.chapter_number,
                chapter_name=f"Chapter {chapter.chapter_number}",
            )
            for chapter in (chapters if chapters else [])
        ]

        return ChaptersResponse(
            entity_id=entity_id, entity_name=entity_name, chapters=chapter_items, total_count=len(chapter_items)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting chapters: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error getting chapters: {str(e)}") from e


@router.delete("/delete", response_model=StatusResponse)
async def delete_series(request: DeleteSeriesRequest):
    """
    Delete a series from the database.

    This will remove the series and all associated data.
    """
    if not app_state.scanner:
        raise HTTPException(status_code=500, detail="Scanner not initialized")

    if not app_state.can_use_database():
        raise HTTPException(status_code=409, detail="Database is currently locked, please wait")

    try:
        app_state.lock_database()
        logger.info("Deleting series: %s (%s)", request.entity_name, request.entity_id)

        app_state.scanner.entity_database.delete_entity_id(request.entity_id, request.entity_name)
        app_state.reload_scanner()

        logger.info("Series deleted successfully: %s", request.entity_name)

        return StatusResponse(success=True, message=f"Series '{request.entity_name}' deleted successfully")
    except Exception as e:
        logger.error("Error deleting series: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error deleting series: {str(e)}") from e
    finally:
        app_state.unlock_database()


@router.delete("/chapters/untrack", response_model=StatusResponse)
async def untrack_chapter(request: DeleteChapterTrackingRequest):
    """
    Remove tracking status from a chapter.

    This will mark the chapter as untracked, allowing it to be re-downloaded.
    """
    if not app_state.scanner:
        raise HTTPException(status_code=500, detail="Scanner not initialized")

    if not app_state.can_use_database():
        raise HTTPException(status_code=409, detail="Database is currently locked, please wait")

    try:
        app_state.lock_database()
        logger.info("Untracking chapter %s from entity %s", request.chapter_id, request.entity_id)

        app_state.scanner.entity_database.delete_chapter_entity_id_from_downloaded_chapters(
            request.entity_id, request.chapter_id
        )
        app_state.reload_scanner()

        logger.info("Chapter untracked successfully")

        return StatusResponse(success=True, message="Chapter tracking removed successfully")
    except Exception as e:
        logger.error("Error untracking chapter: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error untracking chapter: {str(e)}") from e
    finally:
        app_state.unlock_database()
