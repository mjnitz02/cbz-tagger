import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cbz_tagger.entities.base_entity import BaseEntity


def test_base_entity(manga_request_content):
    entity = BaseEntity(content=manga_request_content)
    assert entity.entity_id == "831b12b8-2d0e-4397-8719-1efee4c32f40"
    assert entity.content["id"] == "831b12b8-2d0e-4397-8719-1efee4c32f40"
    assert entity.entity_type == "manga"
    assert entity.content["type"] == "manga"
    assert entity.content["attributes"] == entity.attributes
    assert entity.content["relationships"] == entity.relationships


def test_base_entity_from_json(manga_request_content):
    json_str = json.dumps(manga_request_content)
    entity_from_json = BaseEntity.from_json(json_str)
    assert entity_from_json.content == manga_request_content


def test_base_entity_to_json(manga_request_content):
    entity = BaseEntity(content=manga_request_content)
    entity_json = entity.to_json()
    json_str = json.dumps(manga_request_content)
    assert entity_json == json_str


@patch("cbz_tagger.entities.base_entity.requests.get")
@patch("cbz_tagger.entities.base_entity.sleep")
def test_download_file_success(mock_sleep, mock_requests_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"file content"
    mock_requests_get.return_value = mock_response

    result = BaseEntity.download_file("http://example.com/file")

    assert result == b"file content"
    mock_requests_get.assert_called_once_with("http://example.com/file", timeout=60)
    mock_sleep.assert_called_once()


@patch("cbz_tagger.entities.base_entity.requests.get")
@patch("cbz_tagger.entities.base_entity.sleep")
def test_download_file_retry_success(mock_sleep, mock_requests_get):
    mock_response_fail = MagicMock()
    mock_response_fail.status_code = 500
    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.content = b"file content"
    mock_requests_get.side_effect = [mock_response_fail, mock_response_success]

    result = BaseEntity.download_file("http://example.com/file")

    assert result == b"file content"
    assert mock_requests_get.call_count == 2
    mock_sleep.assert_called_with(0.5)


@patch("cbz_tagger.entities.base_entity.requests.get")
@patch("cbz_tagger.entities.base_entity.sleep")
def test_download_file_failure(mock_sleep, mock_requests_get):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_requests_get.return_value = mock_response

    with pytest.raises(EnvironmentError, match="Failed to download http://example.com/file after 3 attempts"):
        BaseEntity.download_file("http://example.com/file")

    assert mock_requests_get.call_count == 3
    assert mock_sleep.call_count == 3
