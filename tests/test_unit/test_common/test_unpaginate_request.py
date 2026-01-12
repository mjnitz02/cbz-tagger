from unittest.mock import patch

import pytest
import requests

from cbz_tagger.entities.base_entity import BaseEntity


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_unpaginate_request_success(mock_sleep, mock_random, requests_mock):
    url = "https://api.example.com/data"
    data = [{"id": 1}, {"id": 2}]
    requests_mock.get(url, json={"data": data, "total": 2})

    result = BaseEntity.unpaginate_request(url)
    assert result == data


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_unpaginate_request_multiple_pages(mock_sleep, mock_random, requests_mock):
    url = "https://api.example.com/data"
    data_page_1 = [{"id": 1}, {"id": 2}]
    data_page_2 = [{"id": 3}, {"id": 4}]
    requests_mock.get(url, [{"json": {"data": data_page_1, "total": 4}}, {"json": {"data": data_page_2, "total": 4}}])

    result = BaseEntity.unpaginate_request(url, limit=2)
    assert result == data_page_1 + data_page_2


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_unpaginate_request_api_down(mock_sleep, mock_random, requests_mock):
    url = "https://api.example.com/data"
    requests_mock.get(url, exc=requests.exceptions.JSONDecodeError("Expecting value", "", 0))

    with pytest.raises(
        EnvironmentError, match="Failed to receive response from https://api.example.com/data after 3 attempts"
    ):
        BaseEntity.unpaginate_request(url)


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_unpaginate_request_with_duplicates_single_page(mock_sleep, mock_random, requests_mock, caplog):
    """Test that duplicates in a single page response are detected and removed."""
    url = "https://api.example.com/data"
    # Response contains duplicates - id 1 appears twice, but total says 2 (which should match unique count)
    data_with_duplicates = [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}, {"id": 1, "name": "duplicate"}]
    requests_mock.get(url, json={"data": data_with_duplicates, "total": 3})  # total says 3, matches data length

    with patch("cbz_tagger.entities.base_entity.logger") as mock_logger:
        result = BaseEntity.unpaginate_request(url)

        # Should have logged a warning - we have 3 items but only 2 unique IDs
        mock_logger.warning.assert_called_once_with(
            "Paginated response contains duplicate entries. Expected %s unique entries, got %s. Removing duplicates.",
            3,  # total from API
            2,  # actual unique count
        )

        # Should return deduplicated data (first occurrence preserved)
        expected_result = [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}]
        assert result == expected_result


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_unpaginate_request_with_duplicates_multiple_pages(mock_sleep, mock_random, requests_mock):
    """Test that duplicates across multiple pages are detected and removed."""
    url = "https://api.example.com/data"
    # Page 1 has ids 1, 2
    # Page 2 has ids 2, 3 (id 2 is a duplicate)
    data_page_1 = [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}]
    data_page_2 = [{"id": 2, "name": "duplicate"}, {"id": 3, "name": "third"}]
    requests_mock.get(url, [{"json": {"data": data_page_1, "total": 4}}, {"json": {"data": data_page_2, "total": 4}}])

    with patch("cbz_tagger.entities.base_entity.logger") as mock_logger:
        result = BaseEntity.unpaginate_request(url, limit=2)

        # Should have logged a warning - we have 4 items but only 3 unique IDs
        mock_logger.warning.assert_called_once_with(
            "Paginated response contains duplicate entries. Expected %s unique entries, got %s. Removing duplicates.",
            4,  # total from API
            3,  # actual unique count
        )

        # Should return deduplicated data (first occurrence preserved, order maintained)
        expected_result = [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}, {"id": 3, "name": "third"}]
        assert result == expected_result


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_unpaginate_request_no_duplicates_no_warning(mock_sleep, mock_random, requests_mock):
    """Test that no warning is logged when there are no duplicates."""
    url = "https://api.example.com/data"
    data = [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}]
    requests_mock.get(url, json={"data": data, "total": 2})

    with patch("cbz_tagger.entities.base_entity.logger") as mock_logger:
        result = BaseEntity.unpaginate_request(url)

        # Should not have logged any warning
        mock_logger.warning.assert_not_called()

        # Should return original data
        assert result == data


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_unpaginate_request_preserves_order_when_deduplicating(mock_sleep, mock_random, requests_mock):
    """Test that the original order is preserved when removing duplicates."""
    url = "https://api.example.com/data"
    # Complex case with multiple duplicates in different positions
    data_with_duplicates = [
        {"id": 1, "name": "first"},
        {"id": 2, "name": "second"},
        {"id": 3, "name": "third"},
        {"id": 1, "name": "duplicate_first"},  # duplicate of id 1
        {"id": 4, "name": "fourth"},
        {"id": 2, "name": "duplicate_second"},  # duplicate of id 2
        {"id": 5, "name": "fifth"},
    ]
    requests_mock.get(url, json={"data": data_with_duplicates, "total": 5})

    with patch("cbz_tagger.entities.base_entity.logger") as mock_logger:
        result = BaseEntity.unpaginate_request(url)

        # Should have logged a warning
        mock_logger.warning.assert_called_once()

        # Should return deduplicated data in original order (first occurrences only)
        expected_result = [
            {"id": 1, "name": "first"},
            {"id": 2, "name": "second"},
            {"id": 3, "name": "third"},
            {"id": 4, "name": "fourth"},
            {"id": 5, "name": "fifth"},
        ]
        assert result == expected_result
        assert len(result) == 5  # Should have exactly 5 unique items
