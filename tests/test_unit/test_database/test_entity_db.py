from unittest import mock

import pytest

from cbz_tagger.database.entities.metadata_entity import MetadataEntity
from cbz_tagger.database.entity_db import EntityDB


def test_entity_db_can_store_and_load(mock_entity_db, manga_request_id):
    assert mock_entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
    assert mock_entity_db.entity_names == {"Kanojyo to Himitsu to Koimoyou": "Oshimai"}
    assert len(mock_entity_db.authors) == 1
    assert len(mock_entity_db.covers) == 1
    assert len(mock_entity_db.metadata) == 1
    assert len(mock_entity_db.volumes) == 1

    json_str = mock_entity_db.to_json()
    new_mock_entity_db = EntityDB.from_json(json_str)
    assert new_mock_entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
    assert new_mock_entity_db.entity_names == {"Kanojyo to Himitsu to Koimoyou": "Oshimai"}
    assert len(new_mock_entity_db.authors) == 1
    assert len(new_mock_entity_db.covers) == 1
    assert len(new_mock_entity_db.metadata) == 1
    assert len(new_mock_entity_db.volumes) == 1

    new_json_str = new_mock_entity_db.to_json()
    assert json_str == new_json_str


def test_entity_db_to_entity_name(mock_entity_db, manga_name):
    actual = mock_entity_db.to_entity_name(manga_name)
    assert "Oshimai" == actual


@pytest.mark.parametrize(
    "entity_name,expected",
    [
        ("SimpleName", "SimpleName"),
        ("Simple Name", "Simple Name"),
        ("Simple Name?", "Simple Name"),
        (" Simple Name?", "Simple Name"),
        ("Simple Name - with hyphen", "Simple Name with hyphen"),
        ("Simple Name : with colon", "Simple Name with colon"),
        ("Simple Name: with colon", "Simple Name with colon"),
        ("Simple Name: with colon @ comic", "Simple Name with colon comic"),
        ("SOME×CONTENT", "SOME CONTENT"),
    ],
)
def test_entity_db_to_entity_name_cleaning(mock_entity_db, entity_name, expected):
    mock_entity_db.entity_names = {"manga_name": entity_name}
    actual = mock_entity_db.to_entity_name("manga_name")
    assert expected == actual


def test_entity_db_to_entity_with_missing(mock_entity_db):
    mock_entity_db.entity_names = {"manga_name": "something"}
    actual = mock_entity_db.to_entity_name("missing")
    assert actual is None


@pytest.mark.parametrize(
    "chapter_number,expected_filename",
    [
        ("1", "1d387431-eb38-40e9-bc6e-97e4ea4092dc.jpg"),
        ("2", "39194a9c-719b-4a27-b8ef-99a3d6fa0997.jpg"),
        ("3", "a2b7bbe2-3a79-46a4-8960-e0e65a666194.jpg"),
        ("20", "87ad56cd-780b-48bc-82b1-fa425836f9a4.jpg"),
    ],
)
def test_entity_db_to_local_image_file(mock_entity_db, manga_name, chapter_number, expected_filename):
    actual = mock_entity_db.to_local_image_file(manga_name, chapter_number)
    assert expected_filename == actual


def test_entity_db_to_xml_str_chapter_1(mock_entity_db, manga_name, mock_chapter_1_xml):
    actual = mock_entity_db.to_xml_string(manga_name, "1")
    assert mock_chapter_1_xml == actual


def test_entity_db_to_xml_str_chapter_10(mock_entity_db, manga_name, mock_chapter_10_xml):
    actual = mock_entity_db.to_xml_string(manga_name, "10")
    assert mock_chapter_10_xml == actual


@mock.patch("cbz_tagger.database.entity_db.get_input")
def test_entity_db_add_new_manga(mock_get_input, manga_name, manga_request_id, manga_request_response):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(data) for data in manga_request_response["data"]]

        # Simulate user selecting 1 for each input
        mock_get_input.return_value = 1

        entity_db = EntityDB()
        entity_db.add(manga_name)

        # Assert the entity maps are populated
        assert entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
        assert entity_db.entity_names == {"Kanojyo to Himitsu to Koimoyou": "Oshimai"}

        # Assert the individual entity databases have not been updated during the add operation
        assert len(entity_db.authors) == 0
        assert len(entity_db.covers) == 0
        assert len(entity_db.metadata) == 0
        assert len(entity_db.volumes) == 0


def test_entity_db_update_calls_each_entity(mock_entity_db_with_mock_updates, manga_name, manga_request_id):
    metadata_entity = mock_entity_db_with_mock_updates.metadata[manga_request_id]

    mock_entity_db_with_mock_updates.update_manga_entity(manga_name, "filepath")
    mock_entity_db_with_mock_updates.authors.update.assert_called_once_with(metadata_entity.author_entities)
    mock_entity_db_with_mock_updates.covers.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_mock_updates.metadata.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_mock_updates.volumes.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_mock_updates.covers.download.assert_called_once()


def test_entity_db_update_calls_each_entity_but_no_download(
    mock_entity_db_with_mock_updates, manga_name, manga_request_id
):
    metadata_entity = mock_entity_db_with_mock_updates.metadata[manga_request_id]

    mock_entity_db_with_mock_updates.update_manga_entity(manga_name)
    mock_entity_db_with_mock_updates.authors.update.assert_called_once_with(metadata_entity.author_entities)
    mock_entity_db_with_mock_updates.covers.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_mock_updates.metadata.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_mock_updates.volumes.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_mock_updates.covers.download.assert_not_called()


def test_entity_db_update_does_nothing_with_unknown():
    entity_db = EntityDB()
    entity_db.update_manga_entity("unknown")
    assert entity_db.entity_map == {}
    assert entity_db.entity_names == {}
    assert len(entity_db.authors) == 0
    assert len(entity_db.covers) == 0
    assert len(entity_db.metadata) == 0
    assert len(entity_db.volumes) == 0
