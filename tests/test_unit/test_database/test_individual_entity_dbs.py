from unittest import mock

from cbz_tagger.database.author_entity_db import AuthorEntityDB
from cbz_tagger.database.base_db import BaseEntityDB
from cbz_tagger.database.cover_entity_db import CoverEntityDB
from cbz_tagger.database.metadata_entity_db import MetadataEntityDB
from cbz_tagger.database.volume_entity_db import VolumeEntityDB
from cbz_tagger.entities.author_entity import AuthorEntity
from cbz_tagger.entities.cover_entity import CoverEntity
from cbz_tagger.entities.metadata_entity import MetadataEntity
from cbz_tagger.entities.volume_entity import VolumeEntity


def test_base_entity_db():
    entity_db = BaseEntityDB()
    assert entity_db.query_param_field == "ids[]"
    assert entity_db.version == 2
    assert entity_db.database == {}


def test_metadata_entity_db(manga_request_content, manga_request_id):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(content=manga_request_content)]
        entity_db = MetadataEntityDB()

        assert entity_db.to_hash(manga_request_id) == "0"  # Initially, the entity should not exist

        entity_db.update(manga_request_id)
        mock_from_server_url.assert_called_once_with(query_params={"ids[]": [manga_request_id]})

        assert len(entity_db) == 1
        assert entity_db[manga_request_id].content == manga_request_content
        assert entity_db.to_hash(manga_request_id) == "ef16c069d3edb809e80412fd584294576c169cb1"

        # Assert that a second call does not re-add
        entity_db.update(manga_request_id, skip_on_exist=True)
        mock_from_server_url.assert_called_once()
        assert len(entity_db) == 1
        assert entity_db.to_hash(manga_request_id) == "ef16c069d3edb809e80412fd584294576c169cb1"


def test_metadata_entity_db_batch_response(manga_request_content, manga_request_id):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        # Create a second metadata content with different ID
        second_manga_content = manga_request_content.copy()
        second_manga_content["id"] = "different-manga-id-12345"

        # Return two different MetadataEntity objects
        mock_from_server_url.return_value = [
            MetadataEntity(content=manga_request_content),
            MetadataEntity(content=second_manga_content),
        ]

        entity_db = MetadataEntityDB()

        # Initially, entities should not exist
        assert entity_db.to_hash(manga_request_id) == "0"
        assert entity_db.to_hash("different-manga-id-12345") == "0"

        # Update with batch response
        entity_db.update([manga_request_id, "different-manga-id-12345"], batch_response=True)
        mock_from_server_url.assert_called_once_with(
            query_params={"ids[]": [[manga_request_id, "different-manga-id-12345"]]}
        )

        # Verify both entities were added
        assert len(entity_db) == 2
        assert entity_db[manga_request_id].content == manga_request_content
        assert entity_db["different-manga-id-12345"].content == second_manga_content

        # Check hash values
        assert entity_db.to_hash(manga_request_id) == "ef16c069d3edb809e80412fd584294576c169cb1"
        assert entity_db.to_hash("different-manga-id-12345") == "b83c37e946d451bcd1c27b06e6d4bed1bfeed8e4"

        # Assert that a second call does not re-add when skip_on_exist is True
        entity_db.update([manga_request_id, "different-manga-id-12345"], skip_on_exist=True, batch_response=True)
        assert len(entity_db) == 2


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
    with mock.patch.object(AuthorEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [AuthorEntity(content=author_request_content)]
        entity_db = AuthorEntityDB()
        entity_db.update(author_request_id)
        mock_from_server_url.assert_called_once_with(query_params={"ids[]": [author_request_id]})

        assert len(entity_db) == 1
        assert entity_db[author_request_id].content == author_request_content


def test_author_entity_db_can_store_and_load(author_request_content, author_request_id):
    with mock.patch.object(AuthorEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [AuthorEntity(content=author_request_content)]
        entity_db = AuthorEntityDB()
        entity_db.update(author_request_id)

        json_str = entity_db.to_json()
        new_entity_db = AuthorEntityDB.from_json(json_str)
        assert entity_db[author_request_id].content == new_entity_db[author_request_id].content

        new_json_str = new_entity_db.to_json()
        assert json_str == new_json_str


def test_volume_entity_db(volume_request_response, manga_request_id):
    with mock.patch.object(VolumeEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [VolumeEntity(content=volume_request_response)]
        entity_db = VolumeEntityDB()
        entity_db.update(manga_request_id)
        mock_from_server_url.assert_called_once_with(query_params={"ids[]": [manga_request_id]})

        assert len(entity_db) == 1
        assert entity_db[manga_request_id].content == volume_request_response


def test_volume_entity_db_can_store_and_load(volume_request_response, manga_request_id):
    with mock.patch.object(VolumeEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [VolumeEntity(content=volume_request_response)]
        entity_db = VolumeEntityDB()
        entity_db.update(manga_request_id)

        json_str = entity_db.to_json()
        new_entity_db = VolumeEntityDB.from_json(json_str)
        assert entity_db[manga_request_id].content == new_entity_db[manga_request_id].content

        new_json_str = new_entity_db.to_json()
        assert json_str == new_json_str


def test_cover_entity_db(cover_request_response, manga_request_id):
    with mock.patch.object(CoverEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [CoverEntity(data) for data in cover_request_response["data"]]
        entity_db = CoverEntityDB()
        entity_db.update(manga_request_id)
        mock_from_server_url.assert_called_once_with(query_params={"manga[]": [manga_request_id]})

        assert len(entity_db) == 1
        assert isinstance(entity_db[manga_request_id], list)
        # The 5th cover entity is a different language and should be ignored
        assert len(entity_db[manga_request_id]) == 4
        for i in range(len(entity_db)):
            assert entity_db[manga_request_id][i].content == cover_request_response["data"][i]


def test_cover_entity_db_return_list_if_only_one_cover(cover_request_response, manga_request_id):
    with mock.patch.object(CoverEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [CoverEntity(cover_request_response["data"][0])]
        entity_db = CoverEntityDB()
        entity_db.update(manga_request_id)

        assert len(entity_db) == 1
        assert isinstance(entity_db[manga_request_id], list)
        assert entity_db[manga_request_id][0].content == cover_request_response["data"][0]


def test_cover_entity_db_can_store_and_load(cover_request_response, manga_request_id):
    with mock.patch.object(CoverEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [CoverEntity(data) for data in cover_request_response["data"]]
        entity_db = CoverEntityDB()
        entity_db.update(manga_request_id)
        assert isinstance(entity_db[manga_request_id], list)

        json_str = entity_db.to_json()
        new_entity_db = CoverEntityDB.from_json(json_str)
        assert isinstance(new_entity_db[manga_request_id], list)
        assert entity_db[manga_request_id][0].content == new_entity_db[manga_request_id][0].content

        new_json_str = new_entity_db.to_json()
        assert json_str == new_json_str
