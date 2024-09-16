import os
from unittest import mock

import pytest

from cbz_tagger.database.entity_db import AuthorEntityDB
from cbz_tagger.database.entity_db import EntityDB
from cbz_tagger.database.entity_db import MetadataEntityDB
from cbz_tagger.database.entity_db import VolumeEntityDB
from cbz_tagger.entities.author_entity import AuthorEntity
from cbz_tagger.entities.cover_entity import CoverEntity
from cbz_tagger.entities.metadata_entity import MetadataEntity
from cbz_tagger.entities.volume_entity import VolumeEntity


@pytest.fixture
def mock_metadata_db(manga_request_content):
    entity = MetadataEntity(content=manga_request_content)
    entity_db = MetadataEntityDB()
    entity_db.database[entity.entity_id] = entity
    return entity_db


@pytest.fixture
def mock_author_db(author_request_content):
    entity = AuthorEntity(content=author_request_content)
    entity_db = AuthorEntityDB()
    entity_db.database[entity.entity_id] = entity
    return entity_db


@pytest.fixture
def mock_cover_db(cover_request_response, manga_request_id):
    entities = [CoverEntity(data) for data in cover_request_response["data"]]
    entity_db = VolumeEntityDB()
    entity_db.database[manga_request_id] = entities
    return entity_db


@pytest.fixture
def mock_volume_db(volume_request_response, manga_request_id):
    entity = VolumeEntity(content=volume_request_response)
    entity_db = VolumeEntityDB()
    entity_db.database[manga_request_id] = entity
    return entity_db


@pytest.fixture
def mock_entity_db(
    temp_dir, manga_name, manga_request_id, mock_author_db, mock_cover_db, mock_metadata_db, mock_volume_db
):
    entity_db = EntityDB(temp_dir)
    entity_db.entity_map = {manga_name: manga_request_id}
    entity_db.entity_names = {manga_name: "Oshimai"}
    entity_db.entity_tracked = {}
    entity_db.authors = mock_author_db
    entity_db.covers = mock_cover_db
    entity_db.metadata = mock_metadata_db
    entity_db.volumes = mock_volume_db
    return entity_db


@pytest.fixture
def mock_entity_db_with_mock_updates(mock_entity_db, manga_request_id, manga_request_content):
    metadata_entity = MetadataEntity(content=manga_request_content)

    # Mock out the actual update calls so we don't have to mock all requests
    mock_entity_db.authors.update = mock.MagicMock()
    mock_entity_db.covers.update = mock.MagicMock()
    mock_entity_db.covers.download = mock.MagicMock()
    mock_entity_db.metadata.update = mock.MagicMock()
    mock_entity_db.volumes.update = mock.MagicMock()
    mock_entity_db.metadata.database[manga_request_id] = metadata_entity
    return mock_entity_db


@pytest.fixture
def mock_chapter_1_xml(tests_fixtures_path):
    fixture_name = os.path.join(tests_fixtures_path, "expected_chapter_1.xml")
    with open(fixture_name, "r", encoding="UTF-8") as read_file:
        content = read_file.read()
    return content


@pytest.fixture
def mock_chapter_10_xml(tests_fixtures_path):
    fixture_name = os.path.join(tests_fixtures_path, "expected_chapter_10.xml")
    with open(fixture_name, "r", encoding="UTF-8") as read_file:
        content = read_file.read()
    return content
