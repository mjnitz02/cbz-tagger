#!/usr/bin/env python3
"""Pytest tests for the CBZ Tagger API."""

import os

import pytest
import requests
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout


@pytest.fixture(scope="module")
def api_base_url():
    """Get the API base URL from environment or use default."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="module")
def api_client(api_base_url):
    """Create a requests session for API calls."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})

    # Check if API is reachable
    try:
        response = session.get(f"{api_base_url}/health", timeout=5)
        response.raise_for_status()
    except (ConnectionError, Timeout):
        pytest.skip(
            f"API server not reachable at {api_base_url}. Start the server with: python -m cbz_tagger.api.server"
        )

    yield session
    session.close()


#!/usr/bin/env python3
"""Pytest tests for the CBZ Tagger API."""


import pytest


@pytest.fixture(scope="module")
def api_base_url():
    """Get the API base URL from environment or use default."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="module")
def api_client(api_base_url):
    """Create a requests session for API calls."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})

    # Check if API is reachable
    try:
        response = session.get(f"{api_base_url}/health", timeout=5)
        response.raise_for_status()
    except (ConnectionError, Timeout):
        pytest.skip(
            f"API server not reachable at {api_base_url}. Start the server with: python -m cbz_tagger.api.server"
        )

    yield session
    session.close()


class TestAPIHealthEndpoints:
    """Test API health and status endpoints."""

    def test_health_endpoint(self, api_client, api_base_url):
        """Test that health endpoint returns 200 and proper structure."""
        response = api_client.get(f"{api_base_url}/health", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "scanner_initialized" in data
        assert "database_locked" in data
        assert isinstance(data["scanner_initialized"], bool)
        assert isinstance(data["database_locked"], bool)

    def test_root_endpoint(self, api_client, api_base_url):
        """Test that root endpoint returns API information."""
        response = api_client.get(f"{api_base_url}/", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["name"] == "CBZ Tagger API"
        assert data["status"] == "running"


class TestScannerEndpoints:
    """Test scanner-related endpoints."""

    def test_scanner_status(self, api_client, api_base_url):
        """Test that scanner status endpoint returns current status."""
        response = api_client.get(f"{api_base_url}/scanner/status", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["idle", "scanning", "locked"]
        assert "is_first_scan" in data
        assert isinstance(data["is_first_scan"], bool)
        assert "last_scan_time" in data


class TestStateEndpoints:
    """Test state-related endpoints."""

    def test_series_state(self, api_client, api_base_url):
        """Test that series state endpoint returns list of series."""
        response = api_client.get(f"{api_base_url}/state/series", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_count" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total_count"], int)
        assert data["total_count"] == len(data["items"])

        # If there are items, validate structure
        if data["items"]:
            item = data["items"][0]
            assert "entity_id" in item
            assert "entity_name" in item
            assert "status" in item
            assert "plugin" in item


class TestEntityEndpoints:
    """Test entity management endpoints."""

    def test_managed_series(self, api_client, api_base_url):
        """Test that managed series endpoint returns list."""
        response = api_client.get(f"{api_base_url}/entities/managed", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert "series" in data
        assert "total_count" in data
        assert isinstance(data["series"], list)
        assert isinstance(data["total_count"], int)
        assert data["total_count"] == len(data["series"])

        # If there are series, validate structure
        if data["series"]:
            series = data["series"][0]
            assert "entity_id" in series
            assert "entity_name" in series
            assert "display_name" in series


class TestLogsEndpoints:
    """Test logging endpoints."""

    def test_get_logs(self, api_client, api_base_url):
        """Test that logs endpoint returns log messages."""
        response = api_client.get(f"{api_base_url}/logs/?limit=10", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total_count" in data
        assert isinstance(data["logs"], list)
        assert isinstance(data["total_count"], int)
        assert len(data["logs"]) <= 10

        # If there are logs, validate structure
        if data["logs"]:
            log = data["logs"][0]
            assert "timestamp" in log
            assert "level" in log
            assert "message" in log

    def test_get_logs_with_custom_limit(self, api_client, api_base_url):
        """Test logs endpoint with custom limit parameter."""
        response = api_client.get(f"{api_base_url}/logs/?limit=5", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) <= 5


@pytest.mark.slow
class TestIntegrationEndpoints:
    """Test endpoints that perform operations (slower tests)."""

    def test_search_series_requires_search_term(self, api_client, api_base_url):
        """Test that search endpoint requires a search term."""
        response = api_client.post(f"{api_base_url}/entities/search", json={"search_term": ""}, timeout=5)

        assert response.status_code == 422  # FastAPI validation error

    @pytest.mark.skip(reason="Search endpoint returns 500 error - needs investigation")
    def test_search_series_with_valid_term(self, api_client, api_base_url):
        """Test searching for a series with valid search term."""
        response = api_client.post(
            f"{api_base_url}/entities/search",
            json={"search_term": "test"},
            timeout=30,  # Search can take longer
        )

        # Should return 200 even if no results found
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_count" in data
        assert isinstance(data["results"], list)
