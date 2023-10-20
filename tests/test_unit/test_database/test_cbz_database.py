import os
from unittest import mock

import pytest

from cbz_tagger.database.cbz_database import CbzDatabase


@pytest.fixture
def mock_cbz_database(temp_dir, mock_entity_db):
    cbz_database = CbzDatabase(root_path=temp_dir)
    cbz_database.entity_database = mock_entity_db
    return cbz_database


def test_cbz_database_entity_db_path(mock_cbz_database, temp_folder_path):
    expected = os.path.join(temp_folder_path, "entity_db.json")
    assert expected == mock_cbz_database.entity_db_path


def test_cbz_database_image_db_path(mock_cbz_database, temp_folder_path):
    expected = os.path.join(temp_folder_path, "images")
    assert expected == mock_cbz_database.image_db_path


def test_cbz_database_creates_new_database_with_none_present(temp_folder_path):
    cbz_database = CbzDatabase(temp_folder_path)
    assert cbz_database.entity_database.entity_map == {}


def test_cbz_database_can_save_and_load(mock_cbz_database, temp_dir):
    mock_cbz_database.save()
    new_cbz_database = CbzDatabase(root_path=temp_dir)

    # Restored database will likely match, but check the json dumps to ensure they are the same
    assert mock_cbz_database.entity_database.to_json() == new_cbz_database.entity_database.to_json()


def test_cbz_database_can_get_metadata_for_present_series(mock_cbz_database, manga_name, mock_chapter_1_xml):
    mock_cbz_database.entity_database.add = mock.MagicMock()
    entity_name, entity_xml, entity_image_path = mock_cbz_database.get_metadata(manga_name, "1")

    assert entity_name == "Oshimai"
    assert entity_image_path == "1d387431-eb38-40e9-bc6e-97e4ea4092dc.jpg"
    assert entity_xml == mock_chapter_1_xml
    mock_cbz_database.entity_database.add.assert_not_called()


def test_cbz_database_can_add_missing_on_get_metadata_not_found(mock_cbz_database):
    mock_cbz_database.entity_database.add = mock.MagicMock()
    mock_cbz_database.entity_database.update_manga_entity = mock.MagicMock()
    mock_cbz_database.entity_database.to_xml_string = mock.MagicMock()
    mock_cbz_database.entity_database.to_local_image_file = mock.MagicMock()

    mock_cbz_database.save = mock.MagicMock()
    mock_cbz_database.get_metadata("unknown manga", "1")
    mock_cbz_database.entity_database.add.assert_called_once()
    mock_cbz_database.entity_database.update_manga_entity.assert_called_once()
    mock_cbz_database.entity_database.to_xml_string.assert_called_once()
    mock_cbz_database.entity_database.to_local_image_file.assert_called_once()


def test_cbz_database_can_raises_error_on_missing_if_add_new_disabled(mock_cbz_database):
    mock_cbz_database.add_missing = False

    msg = "Manual mode must be enabled for adding missing manga to the database."
    with pytest.raises(RuntimeError, match=msg):
        mock_cbz_database.get_metadata("unknown manga", "1")


def test_cbz_database_update_calls_entity_database_update(mock_cbz_database, manga_name):
    mock_cbz_database.entity_database.update_manga_entity = mock.MagicMock()
    mock_cbz_database.update_metadata(manga_name)
    mock_cbz_database.entity_database.update_manga_entity.assert_called_once_with(
        manga_name, mock_cbz_database.image_db_path
    )
