from unittest import mock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cbz_tagger.common.enums import Urls
from cbz_tagger.entities.base_entity import BaseEntity
from cbz_tagger.entities.chapter_plugins.plugin_mdx import ChapterEntityMDX
from cbz_tagger.entities.cover_entity import CoverEntity


@pytest.fixture
def chapter_entity():
    return ChapterEntityMDX(
        {
            "id": "chapter_id",
            "attributes": {"chapter": "1", "translatedLanguage": "en", "pages": 2},
            "relationships": [{"type": "scanlation_group", "id": "group_id"}],
        }
    )


def test_chapter_entity(chapter_request_content):
    entity = ChapterEntityMDX(content=chapter_request_content)
    assert entity.entity_id == "1361d404-d03c-4fd9-97b4-2c297914b098"
    assert entity.entity_type == "chapter"

    assert entity.volume_number == 1.0
    assert entity.chapter_number == 5
    assert entity.chapter_string == "5"
    assert entity.padded_chapter_string == "005"
    assert entity.quality == "data"
    assert entity.translated_language == "en"


def test_chapter_entity_with_decimal_chapter(chapter_request_content):
    chapter_request_content["attributes"]["chapter"] = "5.5"
    entity = ChapterEntityMDX(content=chapter_request_content)
    assert entity.entity_id == "1361d404-d03c-4fd9-97b4-2c297914b098"
    assert entity.entity_type == "chapter"

    assert entity.volume_number == 1.0
    assert entity.chapter_number == 5.5
    assert entity.chapter_string == "5.5"
    assert entity.padded_chapter_string == "005.5"
    assert entity.quality == "data"
    assert entity.translated_language == "en"


def test_chapter_entity_with_double_decimal_chapter(chapter_request_content):
    chapter_request_content["attributes"]["chapter"] = "5.5.1"
    entity = ChapterEntityMDX(content=chapter_request_content)
    assert entity.entity_id == "1361d404-d03c-4fd9-97b4-2c297914b098"
    assert entity.entity_type == "chapter"

    assert entity.volume_number == 1.0
    assert entity.chapter_number == 5.51
    assert entity.chapter_string == "5.51"
    assert entity.padded_chapter_string == "005.51"
    assert entity.quality == "data"
    assert entity.translated_language == "en"


def test_chapter_entity_with_triple_decimal_chapter(chapter_request_content):
    chapter_request_content["attributes"]["chapter"] = "5.5.1.2"
    entity = ChapterEntityMDX(content=chapter_request_content)
    assert entity.entity_id == "1361d404-d03c-4fd9-97b4-2c297914b098"
    assert entity.entity_type == "chapter"

    assert entity.volume_number == 1.0
    assert entity.chapter_number == 5.512
    assert entity.chapter_string == "5.512"
    assert entity.padded_chapter_string == "005.512"
    assert entity.quality == "data"
    assert entity.translated_language == "en"


def test_chapter_from_url(chapter_request_response):
    with mock.patch("cbz_tagger.entities.chapter_plugins.ChapterEntityMDX.unpaginate_request") as mock_request:
        mock_request.return_value = chapter_request_response["data"]
        entities = ChapterEntityMDX.from_server_url(query_params={"ids[]": ["1361d404-d03c-4fd9-97b4-2c297914b098"]})
        # This test will see the english cover
        assert len(entities) == 4
        assert entities[0].entity_id == "1361d404-d03c-4fd9-97b4-2c297914b098"
        assert entities[1].entity_id == "057c0bce-fd18-44ea-ad64-cefa92378d49"
        assert entities[2].entity_id == "01c86808-46fb-4108-aa5d-4e87aee8b2f1"
        assert entities[3].entity_id == "19020b28-67b1-48a2-82a6-9b7ad18a5c37"
        mock_request.assert_called_once_with(
            f"{BaseEntity.base_url}/manga/1361d404-d03c-4fd9-97b4-2c297914b098/feed?"
            f"order%5BcreatedAt%5D=asc&order%5BupdatedAt%5D=asc&order%5BpublishAt%5D=asc&"
            f"order%5BreadableAt%5D=asc&order%5Bvolume%5D=asc&order%5Bchapter%5D=asc"
        )


def test_cover_entity_can_store_and_load(cover_request_content, check_entity_for_save_and_load):
    entity = CoverEntity(content=cover_request_content)
    check_entity_for_save_and_load(entity)


@patch("cbz_tagger.entities.chapter_plugins.ChapterEntityMDX.request_with_retry")
@patch("cbz_tagger.entities.chapter_entity.Image.open")
@patch("cbz_tagger.entities.chapter_entity.os.path.exists", return_value=False)
@patch("cbz_tagger.entities.chapter_plugins.ChapterEntityMDX.download_file")
def test_download_chapter(mock_download_file, mock_path_exists, mock_image_open, mock_requests_get, chapter_entity):
    _ = mock_path_exists
    mock_requests_get.return_value.json.return_value = {
        "baseUrl": "http://example.com",
        "chapter": {"hash": "hash_value", "data": ["image1.jpg", "image2.jpg"]},
    }
    mock_download_file.return_value = b"image data"
    mock_image = MagicMock()
    mock_image.format = "JPEG"
    mock_image_open.return_value = mock_image

    result = chapter_entity.download_chapter("/fake/filepath")

    assert result == ["/fake/filepath/001.jpg", "/fake/filepath/002.jpg"]
    mock_requests_get.assert_called_once_with(f"https://api.{Urls.MDX}/at-home/server/chapter_id")
    mock_download_file.assert_any_call("http://example.com/data/hash_value/image1.jpg")
    mock_download_file.assert_any_call("http://example.com/data/hash_value/image2.jpg")
    assert mock_image.save.call_count == 2


@patch("cbz_tagger.entities.chapter_plugins.ChapterEntityMDX.request_with_retry")
@patch("cbz_tagger.entities.chapter_entity.os.path.exists", return_value=False)
@patch("cbz_tagger.entities.chapter_plugins.ChapterEntityMDX.download_file")
def test_download_chapter_raises_environment_error(
    mock_download_file, mock_path_exists, mock_requests_get, chapter_entity
):
    _ = mock_path_exists
    mock_requests_get.return_value.json.return_value = {
        "baseUrl": "http://example.com",
        "chapter": {"hash": "hash_value", "data": ["image1.jpg", "image2.jpg"]},
    }
    mock_download_file.side_effect = EnvironmentError("Failed to download file")

    with pytest.raises(EnvironmentError, match="Failed to download file"):
        chapter_entity.download_chapter("/fake/filepath")

    mock_requests_get.assert_called_once_with(f"https://api.{Urls.MDX}/at-home/server/chapter_id")


@patch("cbz_tagger.entities.chapter_plugins.ChapterEntityMDX.request_with_retry")
def test_mdx_parse_chapter_download_links(mock_request_with_retry, chapter_entity):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "baseUrl": "http://example.com",
        "chapter": {"hash": "hash_value", "data": ["image1.jpg", "image2.jpg"]},
    }
    mock_request_with_retry.return_value = mock_response

    result = chapter_entity.parse_chapter_download_links("http://example.com/chapter")

    assert result == ["http://example.com/data/hash_value/image1.jpg", "http://example.com/data/hash_value/image2.jpg"]
    mock_request_with_retry.assert_called_with("http://example.com/chapter")


def test_mdx_get_chapter_url(chapter_entity):
    result = chapter_entity.get_chapter_url()
    assert result == f"https://api.{Urls.MDX}/at-home/server/chapter_id"
