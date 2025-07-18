import json
from unittest import mock
from unittest.mock import patch

import pytest
import requests
import requests_mock

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


def test_base_entity_to_hash(manga_request_content):
    # Create an entity from the content
    entity = BaseEntity(content=manga_request_content)
    hash_value = entity.to_hash()

    # Hash should be consistent for the same content
    assert entity.to_hash() == hash_value

    # Create a new entity with the same content
    # It should have the same hash
    entity2 = BaseEntity(content=manga_request_content.copy())
    assert entity2.to_hash() == hash_value

    # Modify the content and check that the hash changes
    modified_content = manga_request_content.copy()
    modified_content["id"] = "different-id"
    entity3 = BaseEntity(content=modified_content)
    assert entity3.to_hash() != hash_value

    # Test with reordered keys - hash should be the same due to sort_keys=True
    reordered_content = {}
    # Reverse the order of keys to ensure they're different
    for key in reversed(list(manga_request_content.keys())):
        reordered_content[key] = manga_request_content[key]
    entity4 = BaseEntity(content=reordered_content)
    assert entity4.to_hash() == hash_value


@patch("cbz_tagger.entities.base_entity.sleep")
def test_request_with_retry_success(mock_sleep):
    with requests_mock.Mocker() as rm:
        rm.get("http://example.com/file", json={"data": "file content"})

        result = BaseEntity.request_with_retry("http://example.com/file")

        assert result.status_code == 200
        assert result.json() == {"data": "file content"}
        mock_sleep.assert_called_once_with(0.3)


@patch("cbz_tagger.entities.base_entity.sleep")
def test_request_with_retry_retry_success(mock_sleep):
    with requests_mock.Mocker() as rm:
        rm.get(
            "http://example.com/file",
            [
                {"json": {"data": "file content"}, "status_code": 500},
                {"json": {"data": "file content"}, "status_code": 200},
            ],
        )

        result = BaseEntity.request_with_retry("http://example.com/file")

        assert result.status_code == 200
        # Should have 1 retry of 5s sleep, and one default sleep of 0.3 on success
        mock_sleep.assert_has_calls(
            [
                mock.call(5),
                mock.call(0.3),
            ]
        )


@patch("cbz_tagger.entities.base_entity.sleep")
def test_request_with_retry_timeout(mock_sleep):
    with requests_mock.Mocker() as rm:
        rm.get("http://example.com/file", exc=requests.exceptions.ConnectTimeout)

        with pytest.raises(
            EnvironmentError, match="Failed to receive response from http://example.com/file after 3 attempts"
        ):
            BaseEntity.request_with_retry("http://example.com/file")

        # Assert has 3 retry sleeps of increasing time
        mock_sleep.assert_has_calls(
            [
                mock.call(5),
                mock.call(10),
                mock.call(15),
            ]
        )


@patch("cbz_tagger.entities.base_entity.sleep")
def test_request_with_retry_failure(mock_sleep):
    with requests_mock.Mocker() as rm:
        rm.get("http://example.com/file", json={"data": "file content"}, status_code=500)

        with pytest.raises(
            EnvironmentError, match="Failed to receive response from http://example.com/file after 3 attempts"
        ):
            BaseEntity.request_with_retry("http://example.com/file")

        # Assert has 3 retry sleeps of increasing time
        mock_sleep.assert_has_calls(
            [
                mock.call(5),
                mock.call(10),
                mock.call(15),
            ]
        )


@patch("cbz_tagger.entities.base_entity.sleep")
@patch("cbz_tagger.entities.base_entity.AppEnv")
def test_request_with_retry_with_proxy(mock_app_env, mock_sleep):
    def verify_proxy_in_headers(request, content):
        _ = content
        assert request.proxies == {"http": "http://proxy.example.com", "https": "http://proxy.example.com"}
        return "passed"

    with requests_mock.Mocker() as rm:
        rm.get("http://example.com/file", text=verify_proxy_in_headers)
        mock_app_env.return_value.PROXY_URL = "http://proxy.example.com"

        result = BaseEntity.request_with_retry("http://example.com/file")

        assert result.status_code == 200
        assert result.text == "passed"
        mock_sleep.assert_called_once_with(0.3)


@patch("cbz_tagger.entities.base_entity.sleep")
def test_download_file_success(mock_sleep):
    with requests_mock.Mocker() as rm:
        rm.get("http://example.com/file", content=b"file content")

        result = BaseEntity.download_file("http://example.com/file")

        assert result == b"file content"
        mock_sleep.assert_called_once()


@patch("cbz_tagger.entities.base_entity.sleep")
def test_download_file_retry_success(mock_sleep):
    with requests_mock.Mocker() as rm:
        rm.get("http://example.com/file", [{"status_code": 500}, {"content": b"file content"}])

        result = BaseEntity.download_file("http://example.com/file")

        assert result == b"file content"
        # assert mock_requests_get.call_count == 2
        mock_sleep.assert_called_with(0.3)


@patch("cbz_tagger.entities.base_entity.sleep")
def test_download_file_failure(mock_sleep):
    with requests_mock.Mocker() as rm:
        rm.get("http://example.com/file", status_code=500)

        with pytest.raises(
            EnvironmentError, match="Failed to receive response from http://example.com/file after 3 attempts"
        ):
            BaseEntity.download_file("http://example.com/file")

        assert mock_sleep.call_count == 3
