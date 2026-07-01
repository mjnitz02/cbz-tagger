"""Unit tests for web/api.py."""

import asyncio
from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from cbz_tagger.web import api


@pytest.fixture
def reset_app_state():
    """Reset the app state before each test."""
    api._app_state["scanning_state"] = False
    api._app_state["background_timer_started"] = False
    yield
    api._app_state["scanning_state"] = False
    api._app_state["background_timer_started"] = False


@pytest.fixture
def mock_scanner():
    """Create a mock scanner object."""
    scanner = MagicMock()
    scanner.entity_database = MagicMock()
    scanner.entity_database.entity_map = {"test_series": "test_id"}
    scanner.entity_database.chapters = MagicMock()
    scanner.entity_database.chapters.database = {}
    scanner.entity_database.entity_downloads = set()
    return scanner


@pytest.fixture
def mock_env():
    """Create a mock environment object."""
    env = MagicMock()
    env.TIMER_DELAY = 300
    env.to_api = MagicMock(return_value={"config": "value"})
    return env


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    # Use the app without lifespan to avoid background tasks during tests
    from cbz_tagger.web.api import app

    return TestClient(app)


class TestHelperFunctions:
    """Test helper functions for scanner state management."""

    def test_is_scanner_busy_initially_false(self, reset_app_state):
        """Test that scanner is not busy initially."""
        assert api.is_scanner_busy() is False

    def test_lock_scanner(self, reset_app_state):
        """Test locking the scanner."""
        api.lock_scanner()
        assert api.is_scanner_busy() is True

    def test_unlock_scanner(self, reset_app_state):
        """Test unlocking the scanner."""
        api.lock_scanner()
        assert api.is_scanner_busy() is True
        api.unlock_scanner()
        assert api.is_scanner_busy() is False

    def test_lock_unlock_cycle(self, reset_app_state):
        """Test multiple lock/unlock cycles."""
        for _ in range(3):
            api.lock_scanner()
            assert api.is_scanner_busy() is True
            api.unlock_scanner()
            assert api.is_scanner_busy() is False


class TestRunScannerOperation:
    """Test the run_scanner_operation async function."""

    @pytest.mark.asyncio
    async def test_run_scanner_operation_success(self, reset_app_state):
        """Test running a scanner operation successfully."""

        def mock_operation():
            return "success"

        result = await api.run_scanner_operation(mock_operation)
        assert result == "success"
        assert api.is_scanner_busy() is False

    @pytest.mark.asyncio
    async def test_run_scanner_operation_with_args(self, reset_app_state):
        """Test running a scanner operation with arguments."""

        def mock_operation(arg1, arg2):
            return f"{arg1}-{arg2}"

        result = await api.run_scanner_operation(mock_operation, "a", "b")
        assert result == "a-b"
        assert api.is_scanner_busy() is False

    @pytest.mark.asyncio
    async def test_run_scanner_operation_raises_when_busy(self, reset_app_state):
        """Test that operation raises HTTPException when scanner is busy."""
        api.lock_scanner()

        def mock_operation():
            return "success"

        with pytest.raises(HTTPException) as exc_info:
            await api.run_scanner_operation(mock_operation)

        assert exc_info.value.status_code == 409
        assert "Scanner is currently busy" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_run_scanner_operation_unlocks_on_exception(self, reset_app_state):
        """Test that scanner is unlocked even when operation raises exception."""

        def failing_operation():
            raise ValueError("Operation failed")

        with pytest.raises(ValueError, match="Operation failed"):
            await api.run_scanner_operation(failing_operation)

        # Scanner should be unlocked after exception
        assert api.is_scanner_busy() is False


class TestScannerOperations:
    """Test scanner operation functions."""

    @patch("cbz_tagger.web.api.scanner")
    def test_refresh_scanner_operation(self, mock_scanner):
        """Test refresh scanner operation."""
        api.refresh_scanner_operation()
        mock_scanner.run.assert_called_once()

    @patch("cbz_tagger.web.api.scanner")
    def test_add_series_operation(self, mock_scanner):
        """Test add series operation."""
        api.add_series_operation(
            entity_name="Test Series",
            entity_id="test_id",
            backend={"key": "value"},
            enable_tracking=True,
            mark_all_tracked=False,
        )
        mock_scanner.entity_database.add_entity.assert_called_once_with(
            "Test Series",
            "test_id",
            manga_name=None,
            backend={"key": "value"},
            update=True,
            track=True,
            mark_as_tracked=False,
        )

    @patch("cbz_tagger.web.api.scanner")
    def test_delete_series_operation(self, mock_scanner):
        """Test delete series operation."""
        api.delete_series_operation("entity_id", "Entity Name")
        mock_scanner.entity_database.delete_entity_id.assert_called_once_with("entity_id", "Entity Name")

    @patch("cbz_tagger.web.api.scanner")
    def test_set_downloads_operation(self, mock_scanner):
        """Test set downloads operation."""
        api.set_downloads_operation("entity_id", ["chapter_id_1", "chapter_id_2"])
        mock_scanner.entity_database.set_downloaded_chapters.assert_called_once_with(
            "entity_id", ["chapter_id_1", "chapter_id_2"]
        )

    @patch("cbz_tagger.web.api.scanner")
    def test_clean_orphaned_files_operation(self, mock_scanner):
        """Test clean orphaned files operation."""
        api.clean_orphaned_files_operation()
        mock_scanner.entity_database.remove_orphaned_covers.assert_called_once()

    @patch("cbz_tagger.web.api.scanner")
    def test_reload_scanner_operation(self, mock_scanner):
        """Test reload scanner operation."""
        api.reload_scanner_operation()
        mock_scanner.reload_scanner.assert_called_once()

    @patch("cbz_tagger.web.api.FileLogReader")
    def test_get_logs_operation(self, mock_log_reader_class):
        """Test get logs operation."""
        mock_log_reader = MagicMock()
        mock_log_reader.read_last_lines.return_value = "log line 1\nlog line 2\n"
        mock_log_reader_class.return_value = mock_log_reader

        result = api.get_logs_operation(500)

        mock_log_reader_class.assert_called_once_with(api.env.LOG_PATH)
        mock_log_reader.read_last_lines.assert_called_once_with(500)
        assert result == "log line 1\nlog line 2\n"

    @patch("cbz_tagger.web.api.FileLogReader")
    def test_clear_logs_operation(self, mock_log_reader_class):
        """Test clear logs operation."""
        mock_log_reader = MagicMock()
        mock_log_reader_class.return_value = mock_log_reader

        api.clear_logs_operation()

        mock_log_reader_class.assert_called_once_with(api.env.LOG_PATH)
        mock_log_reader.clear_log_file.assert_called_once()

    @patch("cbz_tagger.web.api.scanner")
    def test_get_scanner_state_operation(self, mock_scanner):
        """Test get scanner state operation."""
        mock_scanner.to_state.return_value = []
        result = api.get_scanner_state_operation()
        mock_scanner.reload_scanner.assert_called_once()
        mock_scanner.to_state.assert_called_once()
        assert result == []

    @patch("cbz_tagger.web.api.scanner")
    def test_get_series_list_operation(self, mock_scanner):
        """Test get series list operation."""
        mock_scanner.entity_database.entity_map.items.return_value = [("Series1", "id1"), ("Series2", "id2")]
        result = api.get_series_list_operation()
        mock_scanner.reload_scanner.assert_called_once()
        assert result == [("Series1", "id1"), ("Series2", "id2")]

    @patch("cbz_tagger.web.api.scanner")
    def test_get_chapters_operation_with_chapters(self, mock_scanner):
        """Test get chapters operation when chapters exist."""
        mock_chapter1 = MagicMock()
        mock_chapter1.entity_id = "entity1"
        mock_chapter1.chapter_string = "1"

        mock_chapter2 = MagicMock()
        mock_chapter2.entity_id = "entity2"
        mock_chapter2.chapter_string = "2"

        mock_scanner.entity_database.chapters.database.get.return_value = [mock_chapter1, mock_chapter2]
        mock_scanner.entity_database.entity_downloads = {("test_entity_id", "entity1")}

        result = api.get_chapters_operation("test_entity_id")

        mock_scanner.reload_scanner.assert_called_once()
        assert len(result) == 2
        assert result[0] == {"entity_id": "entity1", "chapter_number": "1", "downloaded": True}
        assert result[1] == {"entity_id": "entity2", "chapter_number": "2", "downloaded": False}

    @patch("cbz_tagger.web.api.scanner")
    def test_get_chapters_operation_no_chapters(self, mock_scanner):
        """Test get chapters operation when no chapters exist."""
        mock_scanner.entity_database.chapters.database.get.return_value = None
        result = api.get_chapters_operation("test_entity_id")
        assert result == []

    @patch("cbz_tagger.web.api.scanner")
    def test_get_chapters_operation_empty_list(self, mock_scanner):
        """Test get chapters operation when chapters list is empty."""
        mock_scanner.entity_database.chapters.database.get.return_value = []
        result = api.get_chapters_operation("test_entity_id")
        assert result == []


class TestAPIEndpoints:
    """Test FastAPI endpoint handlers."""

    @patch("cbz_tagger.web.api.scanner")
    def test_get_scanner_status(self, mock_scanner, reset_app_state, client):
        """Test GET /api/scanner/status endpoint."""
        response = client.get("/api/scanner/status")
        assert response.status_code == 200
        data = response.json()
        assert "busy" in data
        assert "scanner_initialized" in data
        assert data["busy"] is False
        assert data["scanner_initialized"] is True

    @patch("cbz_tagger.web.api.scanner")
    def test_get_scanner_status_when_busy(self, mock_scanner, reset_app_state, client):
        """Test GET /api/scanner/status endpoint when scanner is busy."""
        api.lock_scanner()
        response = client.get("/api/scanner/status")
        assert response.status_code == 200
        data = response.json()
        assert data["busy"] is True
        api.unlock_scanner()

    @patch("cbz_tagger.web.api.scanner")
    def test_refresh_scanner_endpoint(self, mock_scanner, reset_app_state, client):
        """Test POST /api/scanner/refresh endpoint."""
        response = client.post("/api/scanner/refresh")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "refresh completed successfully" in data["message"]
        mock_scanner.run.assert_called_once()

    @patch("cbz_tagger.web.api.scanner")
    def test_reload_scanner_endpoint(self, mock_scanner, reset_app_state, client):
        """Test POST /api/scanner/reload endpoint."""
        response = client.post("/api/scanner/reload")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "reloaded successfully" in data["message"]
        mock_scanner.reload_scanner.assert_called_once()

    @patch("cbz_tagger.web.api.scanner")
    def test_get_scanner_state_endpoint(self, mock_scanner, reset_app_state, client):
        """Test GET /api/scanner/state endpoint."""
        mock_scanner.to_state.return_value = [
            {
                "entity_id": "id1",
                "name": "Series1",
                "name_link": "https://example.com/title/id1",
                "status": "ongoing",
                "tracked": True,
                "latest_chapter": "11",
                "latest_chapter_date": "2021-07-13T08:28:01+00:00",
                "metadata_updated": "2022-12-31T11:57:41+00:00",
                "plugin": "mdx",
                "plugin_link": "https://example.com/title/id1",
            }
        ]
        response = client.get("/api/scanner/state")
        assert response.status_code == 200
        data = response.json()
        assert "series" in data
        assert data["series"][0]["entity_id"] == "id1"
        assert data["series"][0]["status"] == "ongoing"
        assert data["series"][0]["tracked"] is True

    @patch("cbz_tagger.web.api.scanner")
    def test_get_series_list_endpoint(self, mock_scanner, reset_app_state, client):
        """Test GET /api/scanner/series endpoint."""
        mock_scanner.entity_database.entity_map.items.return_value = [("Series1", "id1"), ("Series2", "id2")]
        response = client.get("/api/scanner/series")
        assert response.status_code == 200
        data = response.json()
        assert "series" in data
        assert len(data["series"]) == 2
        assert data["series"][0] == {"name": "Series1", "entity_id": "id1"}
        assert data["series"][1] == {"name": "Series2", "entity_id": "id2"}

    @patch("cbz_tagger.web.api.scanner")
    def test_get_series_chapters_endpoint(self, mock_scanner, reset_app_state, client):
        """Test GET /api/scanner/series/{entity_id}/chapters endpoint."""
        mock_chapter = MagicMock()
        mock_chapter.entity_id = "chapter1"
        mock_chapter.chapter_string = "1"
        mock_scanner.entity_database.chapters.database.get.return_value = [mock_chapter]
        mock_scanner.entity_database.entity_downloads = {("test_id", "chapter1")}

        response = client.get("/api/scanner/series/test_id/chapters")
        assert response.status_code == 200
        data = response.json()
        assert "chapters" in data
        assert len(data["chapters"]) == 1
        assert data["chapters"][0]["entity_id"] == "chapter1"
        assert data["chapters"][0]["chapter_number"] == "1"
        assert data["chapters"][0]["downloaded"] is True

    @patch("cbz_tagger.entities.metadata_entity.MetadataEntity.from_server_url")
    def test_search_series_endpoint(self, mock_from_server, reset_app_state, client):
        """Test GET /api/scanner/search-series endpoint."""
        mock_manga = MagicMock()
        mock_manga.entity_id = "manga_id"
        mock_manga.title = "Test Manga"
        mock_manga.alt_title = "Alt Title"
        mock_manga.all_titles = ["Test Manga", "Alt Title"]
        mock_manga.created_at = datetime(2020, 1, 1)
        mock_manga.age_rating = "safe"
        mock_from_server.return_value = [mock_manga]

        response = client.get("/api/scanner/search-series?title=Test")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1
        result = data["results"][0]
        assert result["entity_id"] == "manga_id"
        assert result["title"] == "Test Manga"
        assert result["alt_title"] == "Alt Title"
        assert result["created_at_year"] == 2020
        assert result["age_rating"] == "safe"

    def test_search_series_endpoint_empty_title(self, reset_app_state, client):
        """Test GET /api/scanner/search-series endpoint with empty title."""
        response = client.get("/api/scanner/search-series?title=")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "required" in data["detail"].lower()

    def test_search_series_endpoint_no_title(self, reset_app_state, client):
        """Test GET /api/scanner/search-series endpoint without title parameter."""
        response = client.get("/api/scanner/search-series")
        assert response.status_code == 422  # FastAPI validation error

    @patch("cbz_tagger.web.api.scanner")
    def test_add_series_endpoint(self, mock_scanner, reset_app_state, client):
        """Test POST /api/scanner/add-series endpoint."""
        request_data = {
            "entity_name": "New Series",
            "entity_id": "new_id",
            "backend": {"key": "value"},
            "enable_tracking": True,
            "mark_all_tracked": False,
        }
        response = client.post("/api/scanner/add-series", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "New Series" in data["message"]
        assert "added successfully" in data["message"]

    @patch("cbz_tagger.web.api.scanner")
    def test_add_series_endpoint_minimal(self, mock_scanner, reset_app_state, client):
        """Test POST /api/scanner/add-series endpoint with minimal data."""
        request_data = {
            "entity_name": "Minimal Series",
            "entity_id": "minimal_id",
        }
        response = client.post("/api/scanner/add-series", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @patch("cbz_tagger.web.api.scanner")
    def test_delete_series_endpoint(self, mock_scanner, reset_app_state, client):
        """Test DELETE /api/scanner/series/{entity_id} endpoint."""
        response = client.delete("/api/scanner/series/test_id?entity_name=Test%20Series")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Test Series" in data["message"]
        assert "deleted successfully" in data["message"]

    @patch("cbz_tagger.web.api.scanner")
    def test_set_series_downloads_endpoint(self, mock_scanner, reset_app_state, client):
        """Test PUT /api/scanner/series/{entity_id}/downloads endpoint."""
        response = client.put(
            "/api/scanner/series/entity_id/downloads",
            json={"downloaded_chapter_ids": ["chapter_id_1", "chapter_id_2"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "updated successfully" in data["message"]
        mock_scanner.entity_database.set_downloaded_chapters.assert_called_once_with(
            "entity_id", ["chapter_id_1", "chapter_id_2"]
        )

    def test_delete_chapter_tracking_route_removed(self, reset_app_state, client):
        """Test the old DELETE /api/scanner/chapter/{entity_id}/{chapter_id} route no longer exists."""
        response = client.delete("/api/scanner/chapter/entity_id/chapter_id")
        assert response.status_code in (404, 405)

    @patch("cbz_tagger.web.api.scanner")
    def test_clean_orphaned_files_endpoint(self, mock_scanner, reset_app_state, client):
        """Test POST /api/scanner/clean-orphaned endpoint."""
        response = client.post("/api/scanner/clean-orphaned")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "cleaned successfully" in data["message"]

    @patch("cbz_tagger.web.api.FileLogReader")
    def test_get_logs_endpoint(self, mock_log_reader_class, reset_app_state, client):
        """Test GET /api/logs endpoint."""
        mock_log_reader = MagicMock()
        mock_log_reader.read_last_lines.return_value = "log contents"
        mock_log_reader_class.return_value = mock_log_reader

        response = client.get("/api/logs")
        assert response.status_code == 200
        data = response.json()
        assert data == {"logs": "log contents"}
        mock_log_reader.read_last_lines.assert_called_once_with(1000)

    @patch("cbz_tagger.web.api.FileLogReader")
    def test_get_logs_endpoint_with_max_lines(self, mock_log_reader_class, reset_app_state, client):
        """Test GET /api/logs endpoint with max_lines query parameter."""
        mock_log_reader = MagicMock()
        mock_log_reader.read_last_lines.return_value = "log contents"
        mock_log_reader_class.return_value = mock_log_reader

        response = client.get("/api/logs?max_lines=50")
        assert response.status_code == 200
        mock_log_reader.read_last_lines.assert_called_once_with(50)

    @patch("cbz_tagger.web.api.FileLogReader")
    def test_clear_logs_endpoint(self, mock_log_reader_class, reset_app_state, client):
        """Test POST /api/logs/clear endpoint."""
        mock_log_reader = MagicMock()
        mock_log_reader_class.return_value = mock_log_reader

        response = client.post("/api/logs/clear")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "cleared successfully" in data["message"]
        mock_log_reader.clear_log_file.assert_called_once()

    @patch("cbz_tagger.common.plugins.Plugins.to_api")
    def test_get_plugins_enum_endpoint(self, mock_to_api, reset_app_state, client):
        """Test GET /api/enums/plugins endpoint."""
        mock_to_api.return_value = {"DEFAULT": "mdx", "all": ["mdx", "kal"]}
        response = client.get("/api/enums/plugins")
        assert response.status_code == 200
        data = response.json()
        assert data == {"DEFAULT": "mdx", "all": ["mdx", "kal"]}

    @patch("cbz_tagger.web.api.env")
    def test_get_env_config_endpoint(self, mock_env, reset_app_state, client):
        """Test GET /api/enums/env endpoint."""
        env_config = {
            "VERSION": "1.0.0",
            "PUID": 1000,
            "PGID": 1000,
            "DEBUG_MODE": False,
            "UMASK": "022",
            "CONFIG_PATH": "/config",
            "SCAN_PATH": "/scan",
            "STORAGE_PATH": "/storage",
            "LOG_PATH": "/config/logs/cbz_tagger.log",
            "TIMER_DELAY": 6000,
            "PROXY_URL": None,
            "DELAY_PER_REQUEST": 0.5,
            "LOG_LEVEL": 20,
        }
        mock_env.to_api.return_value = env_config
        response = client.get("/api/enums/env")
        assert response.status_code == 200
        data = response.json()
        assert data == env_config


class TestPydanticModels:
    """Test Pydantic model validation."""

    def test_add_series_request_full(self):
        """Test AddSeriesRequest with all fields."""
        request = api.AddSeriesRequest(
            entity_name="Test Series",
            entity_id="test_id",
            backend={"key": "value"},
            enable_tracking=False,
            mark_all_tracked=True,
        )
        assert request.entity_name == "Test Series"
        assert request.entity_id == "test_id"
        assert request.backend == {"key": "value"}
        assert request.enable_tracking is False
        assert request.mark_all_tracked is True

    def test_add_series_request_minimal(self):
        """Test AddSeriesRequest with minimal fields (defaults)."""
        request = api.AddSeriesRequest(entity_name="Test", entity_id="id")
        assert request.entity_name == "Test"
        assert request.entity_id == "id"
        assert request.backend is None
        assert request.enable_tracking is True
        assert request.mark_all_tracked is False

    def test_series_search_result(self):
        """Test SeriesSearchResult model."""
        result = api.SeriesSearchResult(
            entity_id="manga_id",
            title="Test Manga",
            alt_title="Alt Title",
            all_titles=["Test Manga", "Alt Title"],
            created_at_year=2020,
            age_rating="safe",
            display_name="Test Manga (Alt Title) - 2020 - safe",
        )
        assert result.entity_id == "manga_id"
        assert result.title == "Test Manga"
        assert result.alt_title == "Alt Title"
        assert len(result.all_titles) == 2
        assert result.created_at_year == 2020
        assert result.age_rating == "safe"
        assert "2020" in result.display_name


class TestConcurrency:
    """Test concurrent operations and scanner locking."""

    @pytest.mark.asyncio
    async def test_concurrent_operations_blocked(self, reset_app_state):
        """Test that concurrent scanner operations are blocked."""
        import time

        def long_operation():
            """A blocking operation that takes some time."""
            time.sleep(0.1)
            return "done"

        # Start first operation
        task1 = asyncio.create_task(api.run_scanner_operation(long_operation))

        # Wait a bit to ensure first operation has started and locked the scanner
        await asyncio.sleep(0.05)

        # Try to start second operation - should fail because scanner is locked
        with pytest.raises(HTTPException) as exc_info:
            await api.run_scanner_operation(lambda: "should_fail")

        assert exc_info.value.status_code == 409

        # Wait for first operation to complete
        result = await task1
        assert result == "done"

        # Now scanner should be available again
        assert api.is_scanner_busy() is False
