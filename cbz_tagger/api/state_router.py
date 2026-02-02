"""Series state and status router."""

import logging

from fastapi import APIRouter
from fastapi import HTTPException

from cbz_tagger.api.models import SeriesStateItem
from cbz_tagger.api.models import SeriesStateResponse
from cbz_tagger.api.state import app_state

logger = logging.getLogger()
router = APIRouter(prefix="/state", tags=["state"])


@router.get("/series", response_model=SeriesStateResponse)
async def get_series_state():
    """
    Get the current state of all series in the database.

    Returns information about each tracked series including:
    - Entity ID and name
    - Current status (ongoing, completed, etc.)
    - Last update time
    - Plugin/backend type
    """
    if not app_state.scanner:
        raise HTTPException(status_code=500, detail="Scanner not initialized")

    try:
        state = app_state.get_scanner_state()

        # Format entity names if too long
        formatted_state = []
        for item in state:
            if len(item.get("entity_name", "")) > 50:
                item["entity_name"] = item["entity_name"][:50] + "..."

            formatted_state.append(
                SeriesStateItem(
                    entity_id=item.get("entity_id", ""),
                    entity_name=item.get("entity_name", ""),
                    status=item.get("status", ""),
                    last_updated=item.get("last_updated"),
                    plugin=item.get("plugin", ""),
                    metadata_updated=item.get("metadata_updated"),
                )
            )

        return SeriesStateResponse(items=formatted_state, total_count=len(formatted_state))
    except Exception as e:
        logger.error("Error getting series state: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error getting series state: {str(e)}") from e


@router.post("/refresh", response_model=SeriesStateResponse)
async def refresh_series_state():
    """
    Refresh and return the current state of all series.

    This reloads the scanner state from disk before returning.
    """
    if not app_state.scanner:
        raise HTTPException(status_code=500, detail="Scanner not initialized")

    try:
        app_state.reload_scanner()
        return await get_series_state()
    except Exception as e:
        logger.error("Error refreshing series state: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error refreshing series state: {str(e)}") from e
