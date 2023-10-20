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


def test_entity_db_to_xml_str_chapter_1(mock_entity_db, manga_name, expected_chapter_1_xml):
    actual = mock_entity_db.to_xml_string(manga_name, "1")
    assert expected_chapter_1_xml == actual


def test_entity_db_to_xml_str_chapter_10(mock_entity_db, manga_name, expected_chapter_10_xml):
    actual = mock_entity_db.to_xml_string(manga_name, "10")
    assert expected_chapter_10_xml == actual


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


# def test_entity_db_update_existing_entity_id(manga_name, manga_request_id, manga_request_response):
#     with mock.patch.object(CoverEntityDB, "download") as mock_download:
#         # Simulate an entity database with 1 entry
#         entity_db = EntityDB()
#         entity_db.entity_map = {'Kanojyo to Himitsu to Koimoyou': manga_request_id}
#         entity_db.entity_names = {'Kanojyo to Himitsu to Koimoyou': "Oshimai"}
#
#         entity_db.update_manga_entity(manga_name, "image_path")
#
#         # Assert the entity maps are populated
#         assert entity_db.entity_map == {'Kanojyo to Himitsu to Koimoyou': manga_request_id}
#         assert entity_db.entity_names == {'Kanojyo to Himitsu to Koimoyou': "Oshimai"}
#
#         # Assert the individual entity databases have not been updated during the add operation
#         assert len(entity_db.authors) == 0
#         assert len(entity_db.covers) == 0
#         assert len(entity_db.metadata) == 0
#         assert len(entity_db.volumes) == 0
