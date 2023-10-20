from unittest import mock

from cbz_tagger.database.base_db import BaseEntityDB
from cbz_tagger.database.entities.author_entity import AuthorEntity
from cbz_tagger.database.entities.metadata_entity import MetadataEntity
from cbz_tagger.database.entity_db import MetadataEntityDB


def test_base_entity_db():
    entity_db = BaseEntityDB()
    assert entity_db.query_param_field == "ids[]"
    assert entity_db.version == 2
    assert entity_db.database == {}


def test_metadata_entity_db(manga_request_content, manga_request_id):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(content=manga_request_content)]
        entity_db = MetadataEntityDB()
        entity_db.update(manga_request_id)
        mock_from_server_url.assert_called_once_with(query_params={"ids[]": [manga_request_id]})

        assert len(entity_db) == 1
        assert entity_db[manga_request_id].content == manga_request_content

        # Assert that a second call does not re-add
        entity_db.update(manga_request_id, skip_on_exist=True)
        mock_from_server_url.assert_called_once()
        assert len(entity_db) == 1


def test_metadata_entity_db_can_store_and_load(manga_request_content, manga_request_id):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(content=manga_request_content)]
        entity_db = MetadataEntityDB()
        entity_db.update(manga_request_id)

        json_str = entity_db.to_json()
        new_entity_db = MetadataEntityDB.from_json(json_str)
        assert entity_db[manga_request_id].content == new_entity_db[manga_request_id].content

        new_json_str = new_entity_db.to_json()
        assert json_str == new_json_str


def test_author_entity_db(author_request_content, author_request_id):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [AuthorEntity(content=author_request_content)]
        entity_db = MetadataEntityDB()
        entity_db.update(author_request_id)
        mock_from_server_url.assert_called_once_with(query_params={"ids[]": [author_request_id]})

        assert len(entity_db) == 1
        assert entity_db[author_request_id].content == author_request_content


def test_author_entity_db_can_store_and_load(author_request_content, author_request_id):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [AuthorEntity(content=author_request_content)]
        entity_db = MetadataEntityDB()
        entity_db.update(author_request_id)

        json_str = entity_db.to_json()
        new_entity_db = MetadataEntityDB.from_json(json_str)
        assert entity_db[author_request_id].content == new_entity_db[author_request_id].content

        new_json_str = new_entity_db.to_json()
        assert json_str == new_json_str
