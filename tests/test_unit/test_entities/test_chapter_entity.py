from unittest import mock

from cbz_tagger.entities.base_entity import BaseEntity
from cbz_tagger.entities.chapter_entity import ChapterEntity
from cbz_tagger.entities.cover_entity import CoverEntity


def test_chapter_entity(chapter_request_content):
    entity = ChapterEntity(content=chapter_request_content)
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
    entity = ChapterEntity(content=chapter_request_content)
    assert entity.entity_id == "1361d404-d03c-4fd9-97b4-2c297914b098"
    assert entity.entity_type == "chapter"

    assert entity.volume_number == 1.0
    assert entity.chapter_number == 5.5
    assert entity.chapter_string == "5.5"
    assert entity.padded_chapter_string == "005.5"
    assert entity.quality == "data"
    assert entity.translated_language == "en"


def test_chapter_from_url(chapter_request_response):
    with mock.patch("cbz_tagger.entities.chapter_entity.unpaginate_request") as mock_request:
        mock_request.return_value = chapter_request_response["data"]
        entities = ChapterEntity.from_server_url(query_params={"ids[]": ["1361d404-d03c-4fd9-97b4-2c297914b098"]})
        # This test will see the english cover
        assert len(entities) == 4
        assert entities[0].entity_id == "1361d404-d03c-4fd9-97b4-2c297914b098"
        assert entities[1].entity_id == "057c0bce-fd18-44ea-ad64-cefa92378d49"
        assert entities[2].entity_id == "01c86808-46fb-4108-aa5d-4e87aee8b2f1"
        assert entities[3].entity_id == "19020b28-67b1-48a2-82a6-9b7ad18a5c37"
        mock_request.assert_called_once_with(f"{BaseEntity.base_url}/manga/1361d404-d03c-4fd9-97b4-2c297914b098/feed")


def test_cover_entity_can_store_and_load(cover_request_content, check_entity_for_save_and_load):
    entity = CoverEntity(content=cover_request_content)
    check_entity_for_save_and_load(entity)
