"""Logging and monitoring router."""

import logging

from fastapi import APIRouter
from fastapi import HTTPException

from cbz_tagger.api.models import LogMessage
from cbz_tagger.api.models import LogsResponse
from cbz_tagger.api.models import StatusResponse
from cbz_tagger.api.state import app_state

logger = logging.getLogger()
router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/", response_model=LogsResponse)
async def get_logs(limit: int = 100):
    """
    Get recent log messages.

    Args:
        limit: Maximum number of logs to return (default: 100)

    Returns:
        List of recent log messages with timestamps and levels
    """
    try:
        logs = app_state.get_logs(limit=limit)

        log_messages = [
            LogMessage(timestamp=log["timestamp"], level=log["level"], message=log["message"]) for log in logs
        ]

        return LogsResponse(logs=log_messages, total_count=len(log_messages))
    except Exception as e:
        logger.error("Error retrieving logs: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}") from e


@router.delete("/clear", response_model=StatusResponse)
async def clear_logs():
    """
    Clear all log messages.

    This will remove all stored logs from memory.
    """
    try:
        app_state.clear_logs()

        return StatusResponse(success=True, message="Logs cleared successfully")
    except Exception as e:
        logger.error("Error clearing logs: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error clearing logs: {str(e)}") from e
