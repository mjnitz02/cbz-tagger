import os
from unittest import mock

import pytest

from cbz_tagger.database.entity_db import EntityDB
from cbz_tagger.entities.metadata_entity import MetadataEntity


def test_entity_db_can_store_and_load(mock_entity_db, manga_request_id):
    assert mock_entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
    assert mock_entity_db.entity_names == {manga_request_id: "Oshimai"}
    assert len(mock_entity_db.authors) == 1
    assert len(mock_entity_db.covers) == 1
    assert len(mock_entity_db.metadata) == 1
    assert len(mock_entity_db.volumes) == 1

    json_str = mock_entity_db.to_json()
    new_mock_entity_db = EntityDB.from_json("mock", json_str)
    assert new_mock_entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
    assert new_mock_entity_db.entity_names == {manga_request_id: "Oshimai"}
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
    actual = mock_entity_db.clean_entity_name(entity_name)
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
def test_entity_db_search(mock_get_input, manga_name, manga_request_id, manga_request_response):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(data) for data in manga_request_response["data"]]

        # Simulate user selecting 1 for each input
        mock_get_input.return_value = 1

        entity_db = EntityDB("mock")
        entity_id, entity_name = entity_db.search(manga_name)

        assert entity_id == manga_request_id
        assert entity_name == "Oshimai"


def test_entity_db_add_new_manga_without_update(manga_name, manga_request_id, manga_request_response):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(data) for data in manga_request_response["data"]]

        entity_db = EntityDB("mock")
        entity_db.search = mock.MagicMock(return_value=(manga_request_id, "Oshimai"))
        entity_db.update_manga_entity_id = mock.MagicMock()
        entity_db.add(manga_name)

        # Assert the entity maps are populated
        assert entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
        assert entity_db.entity_names == {manga_request_id: "Oshimai"}

        # Assert the individual entity databases have not been updated during the add operation
        assert len(entity_db.authors) == 0
        assert len(entity_db.covers) == 0
        assert len(entity_db.metadata) == 0
        assert len(entity_db.volumes) == 0
        assert len(entity_db.chapters) == 0

        entity_db.update_manga_entity_id.assert_not_called()


def test_entity_db_add_new_manga_with_update(manga_name, manga_request_id, manga_request_response):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(data) for data in manga_request_response["data"]]

        entity_db = EntityDB("mock")
        entity_db.search = mock.MagicMock(return_value=(manga_request_id, "Oshimai"))
        entity_db.update_manga_entity_id = mock.MagicMock()
        entity_db.add(manga_name, update=True)

        # Assert the entity maps are populated
        assert entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
        assert entity_db.entity_names == {manga_request_id: "Oshimai"}

        entity_db.update_manga_entity_id.assert_called_once_with(manga_request_id)


@mock.patch("cbz_tagger.database.entity_db.get_input")
def test_entity_db_add_new_manga_with_tracking_and_mark_all_downloaded(
    mock_get_input, mock_chapter_db, manga_name, manga_request_id, manga_request_response
):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(data) for data in manga_request_response["data"]]

        # Simulate user selecting 1 for each input
        mock_get_input.return_value = 1

        entity_db = EntityDB("mock")
        entity_db.search = mock.MagicMock(return_value=(manga_request_id, "Oshimai"))
        entity_db.chapters = mock_chapter_db
        entity_db.add(manga_name, track=True)

        # Assert the entity maps are populated
        assert entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
        assert entity_db.entity_names == {manga_request_id: "Oshimai"}
        assert entity_db.entity_tracked == {"831b12b8-2d0e-4397-8719-1efee4c32f40"}
        assert entity_db.entity_downloads == {
            ("831b12b8-2d0e-4397-8719-1efee4c32f40", "01c86808-46fb-4108-aa5d-4e87aee8b2f1"),
            ("831b12b8-2d0e-4397-8719-1efee4c32f40", "057c0bce-fd18-44ea-ad64-cefa92378d49"),
            ("831b12b8-2d0e-4397-8719-1efee4c32f40", "1361d404-d03c-4fd9-97b4-2c297914b098"),
            ("831b12b8-2d0e-4397-8719-1efee4c32f40", "19020b28-67b1-48a2-82a6-9b7ad18a5c37"),
        }


@mock.patch("cbz_tagger.database.entity_db.get_input")
def test_entity_db_add_new_manga_with_tracking(
    mock_get_input, mock_chapter_db, manga_name, manga_request_id, manga_request_response
):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(data) for data in manga_request_response["data"]]

        # Simulate user selecting 1 for each input
        mock_get_input.return_value = 0

        entity_db = EntityDB("mock")
        entity_db.search = mock.MagicMock(return_value=(manga_request_id, "Oshimai"))
        entity_db.chapters = mock_chapter_db
        entity_db.add(manga_name, track=True)

        # Assert the entity maps are populated
        assert entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
        assert entity_db.entity_names == {manga_request_id: "Oshimai"}
        assert entity_db.entity_tracked == {"831b12b8-2d0e-4397-8719-1efee4c32f40"}
        assert entity_db.entity_downloads == set()


def test_entity_db_update_calls_update_manga_entity_id_from_update_name(
    mock_entity_db_with_mock_updates, manga_name, manga_request_id
):
    mock_entity_db_with_mock_updates.update_manga_entity_id = mock.MagicMock()
    mock_entity_db_with_mock_updates.update_manga_entity_name(manga_name)
    mock_entity_db_with_mock_updates.update_manga_entity_id.assert_called_once_with(manga_request_id)


def test_entity_db_update_calls_only_metadata_if_no_updates(mock_entity_db_with_mock_updates, manga_request_id):
    mock_entity_db_with_mock_updates.update_manga_entity_id(manga_request_id)

    mock_entity_db_with_mock_updates.metadata.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_mock_updates.authors.update.assert_not_called()
    mock_entity_db_with_mock_updates.covers.update.assert_not_called()
    mock_entity_db_with_mock_updates.volumes.update.assert_not_called()
    mock_entity_db_with_mock_updates.chapters.update.assert_not_called()
    mock_entity_db_with_mock_updates.covers.download.assert_not_called()


def test_entity_db_update_calls_each_entity_when_updates_available(
    mock_entity_db_with_mock_updates_out_of_date, manga_request_id
):
    metadata_entity = mock_entity_db_with_mock_updates_out_of_date.metadata[manga_request_id]

    mock_entity_db_with_mock_updates_out_of_date.update_manga_entity_id(manga_request_id)
    mock_entity_db_with_mock_updates_out_of_date.authors.update.assert_called_once_with(metadata_entity.author_entities)
    mock_entity_db_with_mock_updates_out_of_date.covers.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_mock_updates_out_of_date.volumes.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_mock_updates_out_of_date.chapters.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_mock_updates_out_of_date.covers.download.assert_called_once()


def test_entity_db_update_calls_each_entity_when_no_existing_metadata(
    mock_entity_db_with_metadata_update, manga_request_id, manga_request_content
):
    mock_entity_db_with_metadata_update.update_manga_entity_id(manga_request_id)
    mock_entity_db_with_metadata_update.authors.update.assert_called_once_with(
        MetadataEntity(content=manga_request_content).author_entities
    )
    mock_entity_db_with_metadata_update.covers.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_metadata_update.volumes.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_metadata_update.chapters.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_metadata_update.covers.download.assert_called_once()


def test_entity_db_refresh_calls_all_entities(mock_entity_db_with_mock_updates, manga_request_id):
    mock_entity_db_with_mock_updates.update_manga_entity_id = mock.MagicMock()
    mock_entity_db_with_mock_updates.covers.remove_orphaned_covers = mock.MagicMock()
    mock_entity_db_with_mock_updates.refresh()

    mock_entity_db_with_mock_updates.update_manga_entity_id.assert_called_once_with(manga_request_id)
    mock_entity_db_with_mock_updates.covers.remove_orphaned_covers.assert_called_once()


def test_entity_db_update_does_nothing_with_unknown():
    entity_db = EntityDB("mock")
    entity_db.update_manga_entity_name("unknown")
    assert entity_db.entity_map == {}
    assert entity_db.entity_names == {}
    assert len(entity_db.authors) == 0
    assert len(entity_db.covers) == 0
    assert len(entity_db.metadata) == 0
    assert len(entity_db.volumes) == 0


def test_entity_database_image_db_path(mock_entity_db, temp_folder_path):
    expected = os.path.join(temp_folder_path, "images")
    assert expected == mock_entity_db.image_db_path


def test_entity_database_creates_new_database_with_none_present(temp_folder_path):
    entity_database = EntityDB(temp_folder_path)
    assert entity_database.entity_map == {}


def test_entity_database_can_save_and_load(mock_entity_db_with_saving, temp_dir):
    mock_entity_db_with_saving.save()
    entity_database = EntityDB.load(root_path=temp_dir)

    # Restored database will likely match, but check the json dumps to ensure they are the same
    assert mock_entity_db_with_saving.to_json() == entity_database.to_json()


def test_entity_database_no_missing_chapters_with_no_tracked_entities(mock_entity_db):
    missing_chapters = mock_entity_db.get_missing_chapters()
    assert missing_chapters == []


def test_entity_database_has_missing_chapters_with_tracked_entities(mock_entity_db, manga_request_id):
    mock_entity_db.entity_tracked.add(manga_request_id)
    missing_chapters = mock_entity_db.get_missing_chapters()
    assert [chapter_id for (chapter_id, _) in missing_chapters] == [
        "831b12b8-2d0e-4397-8719-1efee4c32f40",
        "831b12b8-2d0e-4397-8719-1efee4c32f40",
        "831b12b8-2d0e-4397-8719-1efee4c32f40",
        "831b12b8-2d0e-4397-8719-1efee4c32f40",
    ]


def test_entity_database_calls_downloads_for_missing_chapters(mock_entity_db, manga_request_id):
    mock_entity_db.entity_tracked.add(manga_request_id)
    mock_entity_db.download_chapter = mock.MagicMock()
    mock_entity_db.download_missing_chapters("storage_path")
    assert mock_entity_db.download_chapter.call_count == 4
