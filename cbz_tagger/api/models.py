"""Pydantic models for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class PluginType(str, Enum):
    """Plugin types for series backends."""

    MDX = "MDX"
    CMK = "CMK"
    KAL = "KAL"
    WBC = "WBC"


class TrackingOption(str, Enum):
    """Tracking options for series."""

    YES = "Yes"
    NO = "No"
    DISABLE = "Disable Tracking"


class ScannerStatus(str, Enum):
    """Scanner operation status."""

    IDLE = "idle"
    SCANNING = "scanning"
    LOCKED = "locked"


# Request Models
class AddSeriesRequest(BaseModel):
    """Request model for adding a new series."""

    entity_id: str = Field(..., description="Entity ID from metadata server")
    entity_name: str = Field(..., description="Name of the series to add")
    backend_plugin: PluginType = Field(default=PluginType.MDX, description="Backend plugin to use")
    backend_id: str | None = Field(default=None, description="Backend ID for non-MDX plugins")
    mark_all_tracked: bool = Field(default=False, description="Mark all chapters as tracked")
    enable_tracking: bool = Field(default=True, description="Enable tracking for this series")


class DeleteSeriesRequest(BaseModel):
    """Request model for deleting a series."""

    entity_id: str = Field(..., description="Entity ID to delete")
    entity_name: str = Field(..., description="Name of entity being deleted")


class DeleteChapterTrackingRequest(BaseModel):
    """Request model for resetting chapter tracking."""

    entity_id: str = Field(..., description="Series entity ID")
    chapter_id: str = Field(..., description="Chapter entity ID to untrack")


class SearchSeriesRequest(BaseModel):
    """Request model for searching series."""

    search_term: str = Field(..., min_length=1, description="Series name to search for")


# Response Models
class SeriesStateItem(BaseModel):
    """Individual series state item."""

    entity_id: str
    entity_name: str
    status: str
    last_updated: datetime | None = None
    plugin: str
    metadata_updated: str | None = None


class SeriesStateResponse(BaseModel):
    """Response model for series state."""

    items: list[SeriesStateItem]
    total_count: int


class MetadataSearchResult(BaseModel):
    """Metadata search result item."""

    entity_id: str
    title: str
    alt_title: str
    year: int
    age_rating: str
    all_titles: list[str]
    display_name: str


class SearchSeriesResponse(BaseModel):
    """Response model for series search."""

    results: list[MetadataSearchResult]
    total_count: int


class ManagedSeriesItem(BaseModel):
    """Item for managed series list."""

    entity_id: str
    entity_name: str
    display_name: str


class ManagedSeriesResponse(BaseModel):
    """Response model for managed series."""

    series: list[ManagedSeriesItem]
    total_count: int


class ChapterItem(BaseModel):
    """Chapter item for a series."""

    entity_id: str
    chapter_id: str
    chapter_number: str
    chapter_name: str


class ChaptersResponse(BaseModel):
    """Response model for chapters."""

    entity_id: str
    entity_name: str
    chapters: list[ChapterItem]
    total_count: int


class StatusResponse(BaseModel):
    """Response model for operation status."""

    success: bool
    message: str
    data: dict[str, Any] | None = None


class ScannerStatusResponse(BaseModel):
    """Response model for scanner status."""

    status: ScannerStatus
    is_first_scan: bool
    last_scan_time: datetime | None = None


class LogMessage(BaseModel):
    """Log message model."""

    timestamp: datetime
    level: str
    message: str


class LogsResponse(BaseModel):
    """Response model for logs."""

    logs: list[LogMessage]
    total_count: int
