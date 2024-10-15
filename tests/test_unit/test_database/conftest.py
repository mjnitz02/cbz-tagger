import copy
import os
from typing import List
from typing import Union
from unittest import mock

import pytest

from cbz_tagger.common.enums import Urls
from cbz_tagger.database.author_entity_db import AuthorEntityDB
from cbz_tagger.database.chapter_entity_db import ChapterEntityDB
from cbz_tagger.database.entity_db import EntityDB
from cbz_tagger.database.metadata_entity_db import MetadataEntityDB
from cbz_tagger.database.volume_entity_db import VolumeEntityDB
from cbz_tagger.entities.author_entity import AuthorEntity
from cbz_tagger.entities.chapter_plugins.plugin_mdx import ChapterEntityMDX
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
def mock_chapter_db(chapter_request_response, manga_request_id):
    entities = [ChapterEntityMDX(data) for data in chapter_request_response["data"]]
    entity_db = ChapterEntityDB()
    entity_db.database[manga_request_id] = entities
    return entity_db


@pytest.fixture
def mock_entity_db_with_saving(
    temp_dir,
    manga_name,
    manga_request_id,
    mock_author_db,
    mock_cover_db,
    mock_metadata_db,
    mock_volume_db,
    mock_chapter_db,
):
    entity_db = EntityDB(temp_dir)
    entity_db.entity_map = {manga_name: manga_request_id}
    entity_db.entity_names = {manga_request_id: "Oshimai"}
    entity_db.authors = mock_author_db
    entity_db.covers = mock_cover_db
    entity_db.metadata = mock_metadata_db
    entity_db.volumes = mock_volume_db
    entity_db.chapters = mock_chapter_db
    return entity_db


@pytest.fixture
def mock_entity_db(
    mock_entity_db_with_saving,
):
    mock_entity_db_with_saving.save = mock.MagicMock()
    return mock_entity_db_with_saving


@pytest.fixture
def mock_entity_db_with_mock_updates(mock_entity_db, manga_request_id, manga_request_content):
    metadata_entity = MetadataEntity(content=manga_request_content)

    # Mock out the actual update calls so we don't have to mock all requests
    mock_entity_db.metadata.update = mock.MagicMock()
    mock_entity_db.authors.update = mock.MagicMock()
    mock_entity_db.covers.update = mock.MagicMock()
    mock_entity_db.covers.download = mock.MagicMock()
    mock_entity_db.volumes.update = mock.MagicMock()
    mock_entity_db.chapters.update = mock.MagicMock()
    mock_entity_db.metadata.database[manga_request_id] = metadata_entity
    return mock_entity_db


@pytest.fixture
def mock_entity_db_with_metadata_update(mock_entity_db, manga_request_content):
    class MockMetadataEntityDB(MetadataEntityDB):
        def update(self, entity_ids: Union[List[str], str], skip_on_exist=False):
            if not isinstance(entity_ids, list):
                entity_ids = [entity_ids]

            self.database[entity_ids[0]] = MetadataEntity(content=manga_request_content)

    mock_entity_db.metadata = MockMetadataEntityDB()
    mock_entity_db.authors.update = mock.MagicMock()
    mock_entity_db.covers.update = mock.MagicMock()
    mock_entity_db.covers.download = mock.MagicMock()
    mock_entity_db.volumes.update = mock.MagicMock()
    mock_entity_db.chapters.update = mock.MagicMock()

    return mock_entity_db


@pytest.fixture
def mock_entity_db_with_mock_updates_out_of_date(
    mock_entity_db_with_metadata_update, manga_request_id, manga_request_content
):
    out_of_date_content = copy.deepcopy(manga_request_content)
    out_of_date_content["attributes"]["updatedAt"] = out_of_date_content["attributes"]["createdAt"]
    entity = MetadataEntity(content=out_of_date_content)
    mock_entity_db_with_metadata_update.metadata.database[manga_request_id] = entity
    return mock_entity_db_with_metadata_update


@pytest.fixture
def mock_chapter_1_xml(tests_fixtures_path):
    fixture_name = os.path.join(tests_fixtures_path, "expected_chapter_1.xml")
    with open(fixture_name, "r", encoding="UTF-8") as read_file:
        content = read_file.read()
    content = content.replace("example.com", Urls.MDX)
    return content


@pytest.fixture
def mock_chapter_10_xml(tests_fixtures_path):
    fixture_name = os.path.join(tests_fixtures_path, "expected_chapter_10.xml")
    with open(fixture_name, "r", encoding="UTF-8") as read_file:
        content = read_file.read()
    content = content.replace("example.com", Urls.MDX)
    return content
