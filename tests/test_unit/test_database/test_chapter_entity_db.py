from unittest import mock
from unittest.mock import MagicMock

import pytest

from cbz_tagger.database.chapter_entity_db import ChapterEntityDB
from cbz_tagger.entities.chapter_entity import ChapterEntity


def test_chapter_entity_db(chapter_request_response, manga_request_id):
    with mock.patch.object(ChapterEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [ChapterEntity(data) for data in chapter_request_response["data"]]
        entity_db = ChapterEntityDB()
        entity_db.update(manga_request_id)
        mock_from_server_url.assert_called_once_with(query_params={"ids[]": [manga_request_id]})

        assert len(entity_db) == 1
        assert isinstance(entity_db[manga_request_id], list)
        # 2 responses are not english. We should have only 2 real chapters.
        assert len(entity_db[manga_request_id]) == 2
        for i in range(len(entity_db)):
            assert entity_db[manga_request_id][i].content == chapter_request_response["data"][i]


def test_chapter_entity_db_return_list_if_only_one_chapter(chapter_request_response, manga_request_id):
    with mock.patch.object(ChapterEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [ChapterEntity(data) for data in chapter_request_response["data"]]
        entity_db = ChapterEntityDB()
        entity_db.update(manga_request_id)

        assert len(entity_db) == 1
        assert isinstance(entity_db[manga_request_id], list)
        assert entity_db[manga_request_id][0].content == chapter_request_response["data"][0]


def test_chapter_entity_db_can_store_and_load(chapter_request_response, manga_request_id):
    with mock.patch.object(ChapterEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [ChapterEntity(data) for data in chapter_request_response["data"]]
        entity_db = ChapterEntityDB()
        entity_db.update(manga_request_id)
        assert isinstance(entity_db[manga_request_id], list)

        json_str = entity_db.to_json()
        new_entity_db = ChapterEntityDB.from_json(json_str)
        assert isinstance(new_entity_db[manga_request_id], list)
        assert entity_db[manga_request_id][0].content == new_entity_db[manga_request_id][0].content

        new_json_str = new_entity_db.to_json()
        assert json_str == new_json_str


def test_group_chapters():
    chapter_a = ChapterEntity(
        content={
            "attributes": {
                "chapter": "1",
                "translatedLanguage": "en",
            },
            "relationships": [{"type": "scanlation_group", "id": "group1"}],
        }
    )
    chapter_b = ChapterEntity(
        content={
            "attributes": {"chapter": "2", "translatedLanguage": "en"},
            "relationships": [{"type": "scanlation_group", "id": "group2"}],
        }
    )
    chapter_c = ChapterEntity(
        content={
            "attributes": {"chapter": "3", "translatedLanguage": "en"},
            "relationships": [{"type": "scanlation_group", "id": "group3"}],
        }
    )
    grouped_chapters, scanlation_groups = ChapterEntityDB.group_chapters([chapter_a, chapter_b, chapter_c])
    assert grouped_chapters == {
        1.0: [chapter_a],
        2.0: [chapter_b],
        3.0: [chapter_c],
    }
    assert scanlation_groups == ["group1", "group2", "group3"]
