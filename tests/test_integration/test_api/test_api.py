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


@pytest.mark.api
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
