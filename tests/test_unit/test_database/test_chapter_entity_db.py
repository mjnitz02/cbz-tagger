from unittest import mock

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
