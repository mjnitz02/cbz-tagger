import json
import os
from datetime import datetime
from datetime import timezone
from unittest import mock

import pytest

from cbz_tagger.common.enums import Urls
from cbz_tagger.common.input import InputEntity
from cbz_tagger.database.entity_db import EntityDB
from cbz_tagger.entities.cover_entity import CoverEntity
from cbz_tagger.entities.metadata_entity import MetadataEntity


@pytest.fixture
def simple_mock_entity_db():
    entity_db = EntityDB("mock")
    entity_db.save = mock.MagicMock()
    return entity_db


def test_entity_db_can_store_and_load(mock_entity_db, manga_request_id):
    assert mock_entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
    assert mock_entity_db.entity_names == {manga_request_id: "Oshimai"}
    assert len(mock_entity_db.authors) == 1
    assert len(mock_entity_db.covers) == 1
    assert len(mock_entity_db.metadata) == 1
    assert len(mock_entity_db.volumes) == 1
    assert len(mock_entity_db.chapters) == 1

    json_str = mock_entity_db.to_json()
    new_mock_entity_db = EntityDB.from_json("mock", json_str)
    assert new_mock_entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
    assert new_mock_entity_db.entity_names == {manga_request_id: "Oshimai"}
    assert len(new_mock_entity_db.authors) == 1
    assert len(new_mock_entity_db.covers) == 1
    assert len(new_mock_entity_db.metadata) == 1
    assert len(new_mock_entity_db.volumes) == 1
    assert len(new_mock_entity_db.chapters) == 1

    new_json_str = new_mock_entity_db.to_json()
    assert json_str == new_json_str


def test_entity_db_can_load_backwards_compatible(mock_entity_db, manga_request_id):
    assert mock_entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
    assert mock_entity_db.entity_names == {manga_request_id: "Oshimai"}
    assert len(mock_entity_db.authors) == 1
    assert len(mock_entity_db.covers) == 1
    assert len(mock_entity_db.metadata) == 1
    assert len(mock_entity_db.volumes) == 1
    assert len(mock_entity_db.chapters) == 1

    legacy_json_dump = {
        "entity_map": mock_entity_db.entity_map,
        "entity_names": mock_entity_db.entity_names,
        "metadata": mock_entity_db.metadata.to_json(),
        "covers": mock_entity_db.covers.to_json(),
        "authors": mock_entity_db.authors.to_json(),
        "volumes": mock_entity_db.volumes.to_json(),
    }
    legacy_json_dump = json.dumps(legacy_json_dump)
    new_mock_entity_db = EntityDB.from_json("mock", legacy_json_dump)
    assert new_mock_entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
    assert new_mock_entity_db.entity_names == {manga_request_id: "Oshimai"}
    assert len(new_mock_entity_db.authors) == 1
    assert len(new_mock_entity_db.covers) == 1
    assert len(new_mock_entity_db.metadata) == 1
    assert len(new_mock_entity_db.volumes) == 1
    assert len(new_mock_entity_db.chapters) == 0
    assert len(new_mock_entity_db.entity_downloads) == 0
    assert len(new_mock_entity_db.entity_tracked) == 0


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
        ("Simple Name Apostrophe'", "Simple Name Apostrophe'"),
        ("Simple Name's Apostrophe", "Simple Name's Apostrophe"),
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
        ("100", "87ad56cd-780b-48bc-82b1-fa425836f9a4.jpg"),
    ],
    ids=[
        "chapter 1",
        "chapter 2",
        "chapter 3",
        "chapter 20",
        "chapter 100 - use the default cover id",
    ],
)
def test_entity_db_to_local_image_file(mock_entity_db, manga_name, chapter_number, expected_filename):
    """Test behaviour when all covers have a volume present"""
    actual = mock_entity_db.to_local_image_file(manga_name, chapter_number)
    assert expected_filename == actual


@pytest.mark.parametrize(
    "chapter_number,expected_filename",
    [
        ("1", "1d387431-eb38-40e9-bc6e-97e4ea4092dc.jpg"),
        ("2", "39194a9c-719b-4a27-b8ef-99a3d6fa0997.jpg"),
        ("3", "a2b7bbe2-3a79-46a4-8960-e0e65a666194.jpg"),
        ("20", "87ad56cd-780b-48bc-82b1-fa425836f9a4.jpg"),
        ("22", "99ad56cd-780b-48bc-82b1-fa425836f9a4.jpg"),
        ("30", "99ad56cd-780b-48bc-82b1-fa425836f9a4.jpg"),
        ("40", "87ad56cd-780b-48bc-82b1-fa425836f9a4.jpg"),
        ("100", "87ad56cd-780b-48bc-82b1-fa425836f9a4.jpg"),
    ],
    ids=[
        "chapter 1",
        "chapter 2",
        "chapter 3",
        "chapter 20",
        "chapter 22 - synthetic volume on limit of range",
        "chapter 30 - synthetic volume inside of range",
        "chapter 40 - synthetic volume outside of range, use default cover id",
        "chapter 100 - synthetic volume way outside of range, use default cover id",
    ],
)
def test_entity_db_to_local_image_file_with_un_volumed_covers(
    mock_entity_db, manga_name, manga_request_id, chapter_number, expected_filename
):
    """Test behaviour if there are covers for volumes not tracked. This uses the synthetic volume processing to
    try and associate the volume with the cover"""
    mock_entity_db.covers[manga_request_id].append(
        CoverEntity(
            {
                "attributes": {
                    "createdAt": "2021-05-24T18:04:01+00:00",
                    "description": "",
                    "fileName": "99ad56cd-780b-48bc-82b1-fa425836f9a4.jpg",
                    "locale": "en",
                    "updatedAt": "2021-11-09T20:59:36+00:00",
                    "version": 4,
                    "volume": "5",
                },
                "id": "9d64b6fb-0cac-4fa7-b3da-553fea602d2d",
                "relationships": [
                    {"id": manga_request_id, "type": "manga"},
                    {"id": "f8cc4f8a-e596-4618-ab05-ef6572980bbf", "type": "user"},
                ],
                "type": "cover_art",
            }
        )
    )
    actual = mock_entity_db.to_local_image_file(manga_name, chapter_number)
    assert expected_filename == actual


def test_entity_db_to_local_image_file_if_not_found(mock_entity_db, manga_request_id, manga_name):
    # Artificially remove the volume 2 cover
    mock_entity_db.covers.database[manga_request_id].pop(1)
    # Artificially remove the fallback cover, volume 4
    mock_entity_db.covers.database[manga_request_id].pop(0)
    actual = mock_entity_db.to_local_image_file(manga_name, "4")
    # Fallback should end up as volume 3 cover
    assert "a2b7bbe2-3a79-46a4-8960-e0e65a666194.jpg" == actual


def test_entity_db_to_xml_str_chapter_1(mock_entity_db, manga_name, mock_chapter_1_xml):
    actual = mock_entity_db.to_xml_string(manga_name, "1")
    assert mock_chapter_1_xml == actual


def test_entity_db_to_xml_str_chapter_10(mock_entity_db, manga_name, mock_chapter_10_xml):
    actual = mock_entity_db.to_xml_string(manga_name, "10")
    assert mock_chapter_10_xml == actual


def test_entity_db_to_xml_str_chapter_1_with_ended_and_no_last_chapter(
    mock_entity_db, manga_request_id, manga_name, mock_chapter_1_xml
):
    mock_entity_db.metadata.database[manga_request_id].content["attributes"]["status"] = "completed"
    actual = mock_entity_db.to_xml_string(manga_name, "1")
    assert mock_chapter_1_xml == actual


def test_entity_db_to_xml_str_chapter_1_with_ended_and_last_chapter(
    mock_entity_db, manga_request_id, manga_name, mock_chapter_1_xml_with_count_3
):
    mock_entity_db.metadata.database[manga_request_id].content["attributes"]["status"] = "completed"
    mock_entity_db.metadata.database[manga_request_id].content["attributes"]["lastChapter"] = "3"
    actual = mock_entity_db.to_xml_string(manga_name, "1")
    assert mock_chapter_1_xml_with_count_3 == actual


def test_entity_db_to_mylar_json_with_continuing(mock_entity_db, manga_name):
    actual = mock_entity_db.to_mylar_series_json(manga_name)
    assert actual == (
        "{\n"
        '    "version": "1.0.2",\n'
        '    "metadata": {\n'
        '        "type": "comicSeries",\n'
        '        "publisher": "",\n'
        '        "imprint": null,\n'
        '        "name": "Oshimai",\n'
        '        "comicid": 0,\n'
        '        "year": 2020,\n'
        '        "description_text": "A collection of twitter published manga by '
        'Kawasaki Tadataka...",\n'
        '        "description_formatted": null,\n'
        '        "volume": null,\n'
        '        "booktype": "Print",\n'
        '        "collects": null,\n'
        '        "comic_image": "",\n'
        '        "total_issues": -1,\n'
        '        "publication_run": "",\n'
        '        "status": "Continuing"\n'
        "    }\n"
        "}"
    )


def test_entity_db_to_mylar_json_with_ended(mock_entity_db, manga_request_id, manga_name):
    mock_entity_db.metadata.database[manga_request_id].content["attributes"]["status"] = "completed"
    mock_entity_db.metadata.database[manga_request_id].content["attributes"]["lastChapter"] = "3"
    actual = mock_entity_db.to_mylar_series_json(manga_name)
    assert actual == (
        "{\n"
        '    "version": "1.0.2",\n'
        '    "metadata": {\n'
        '        "type": "comicSeries",\n'
        '        "publisher": "",\n'
        '        "imprint": null,\n'
        '        "name": "Oshimai",\n'
        '        "comicid": 0,\n'
        '        "year": 2020,\n'
        '        "description_text": "A collection of twitter published manga by '
        'Kawasaki Tadataka...",\n'
        '        "description_formatted": null,\n'
        '        "volume": null,\n'
        '        "booktype": "Print",\n'
        '        "collects": null,\n'
        '        "comic_image": "",\n'
        '        "total_issues": 3,\n'
        '        "publication_run": "",\n'
        '        "status": "Ended"\n'
        "    }\n"
        "}"
    )


@mock.patch("cbz_tagger.common.input.get_input")
def test_entity_db_search(mock_get_input, simple_mock_entity_db, manga_name, manga_request_id, manga_request_response):
    _ = simple_mock_entity_db
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(data) for data in manga_request_response["data"]]

        # Simulate user selecting 1 for each input
        mock_get_input.return_value = 1

        entity_id, entity_name = InputEntity.search(manga_name)

        assert entity_id == manga_request_id
        assert entity_name == "Oshimai"


def test_entity_db_add_new_manga_without_update(
    simple_mock_entity_db, manga_name, manga_request_id, manga_request_response
):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(data) for data in manga_request_response["data"]]

        simple_mock_entity_db.search = mock.MagicMock(return_value=(manga_request_id, "Oshimai"))
        simple_mock_entity_db.update_manga_entity_id = mock.MagicMock()
        simple_mock_entity_db.add(manga_name, update=False)

        # Assert the entity maps are populated
        assert simple_mock_entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
        assert simple_mock_entity_db.entity_names == {manga_request_id: "Oshimai"}

        # Assert the individual entity databases have not been updated during the add operation
        assert len(simple_mock_entity_db.authors) == 0
        assert len(simple_mock_entity_db.covers) == 0
        assert len(simple_mock_entity_db.metadata) == 0
        assert len(simple_mock_entity_db.volumes) == 0
        assert len(simple_mock_entity_db.chapters) == 0

        simple_mock_entity_db.update_manga_entity_id.assert_not_called()


def test_entity_db_add_new_manga_with_update(
    simple_mock_entity_db, manga_name, manga_request_id, manga_request_response
):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(data) for data in manga_request_response["data"]]

        simple_mock_entity_db.search = mock.MagicMock(return_value=(manga_request_id, "Oshimai"))
        simple_mock_entity_db.update_manga_entity_id = mock.MagicMock()
        simple_mock_entity_db.add(manga_name, update=True)

        # Assert the entity maps are populated
        assert simple_mock_entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
        assert simple_mock_entity_db.entity_names == {manga_request_id: "Oshimai"}

        simple_mock_entity_db.update_manga_entity_id.assert_called_once_with(manga_request_id)


@mock.patch("cbz_tagger.common.input.get_raw_input")
@mock.patch("cbz_tagger.common.input.get_input")
def test_entity_db_add_new_manga_with_tracking_and_mark_all_downloaded(
    mock_get_input,
    mock_get_raw_input,
    simple_mock_entity_db,
    mock_chapter_db,
    manga_name,
    manga_request_id,
    manga_request_response,
):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(data) for data in manga_request_response["data"]]

        mock_get_input.return_value = 0
        # Simulate user selecting 1 for each input
        mock_get_raw_input.return_value = "y"

        simple_mock_entity_db.search = mock.MagicMock(return_value=(manga_request_id, "Oshimai"))
        simple_mock_entity_db.update_manga_entity_id = mock.MagicMock()
        simple_mock_entity_db.chapters = mock_chapter_db
        simple_mock_entity_db.add(manga_name, track=True)

        # Assert the entity maps are populated
        assert simple_mock_entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
        assert simple_mock_entity_db.entity_names == {manga_request_id: "Oshimai"}
        assert simple_mock_entity_db.entity_tracked == {"831b12b8-2d0e-4397-8719-1efee4c32f40"}
        assert simple_mock_entity_db.entity_downloads == {
            ("831b12b8-2d0e-4397-8719-1efee4c32f40", "01c86808-46fb-4108-aa5d-4e87aee8b2f1"),
            ("831b12b8-2d0e-4397-8719-1efee4c32f40", "057c0bce-fd18-44ea-ad64-cefa92378d49"),
            ("831b12b8-2d0e-4397-8719-1efee4c32f40", "1361d404-d03c-4fd9-97b4-2c297914b098"),
            ("831b12b8-2d0e-4397-8719-1efee4c32f40", "19020b28-67b1-48a2-82a6-9b7ad18a5c37"),
        }


@mock.patch("cbz_tagger.common.input.get_raw_input")
@mock.patch("cbz_tagger.common.input.get_input")
def test_entity_db_add_new_manga_with_tracking(
    mock_get_input,
    mock_get_raw_input,
    simple_mock_entity_db,
    mock_chapter_db,
    manga_name,
    manga_request_id,
    manga_request_response,
):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(data) for data in manga_request_response["data"]]

        mock_get_input.return_value = 0
        # Simulate user selecting 1 for each input
        mock_get_raw_input.return_value = 0

        simple_mock_entity_db.search = mock.MagicMock(return_value=(manga_request_id, "Oshimai"))
        simple_mock_entity_db.update_manga_entity_id = mock.MagicMock()
        simple_mock_entity_db.chapters = mock_chapter_db
        simple_mock_entity_db.add(manga_name, track=True)

        # Assert the entity maps are populated
        assert simple_mock_entity_db.entity_map == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
        assert simple_mock_entity_db.entity_names == {manga_request_id: "Oshimai"}
        assert simple_mock_entity_db.entity_tracked == {"831b12b8-2d0e-4397-8719-1efee4c32f40"}
        assert simple_mock_entity_db.entity_downloads == set()


@mock.patch("cbz_tagger.common.input.get_raw_input")
@mock.patch("cbz_tagger.common.input.get_input")
def test_entity_db_remove_manga_from_tracking(
    mock_get_input,
    mock_get_raw_input,
    simple_mock_entity_db,
    mock_chapter_db,
    manga_name,
    manga_request_id,
    manga_request_response,
):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(data) for data in manga_request_response["data"]]

        mock_get_input.return_value = 0
        # Simulate user selecting 1 for each input
        mock_get_raw_input.return_value = 0

        simple_mock_entity_db.search = mock.MagicMock(return_value=(manga_request_id, "Oshimai"))
        simple_mock_entity_db.update_manga_entity_id = mock.MagicMock()
        simple_mock_entity_db.chapters = mock_chapter_db
        simple_mock_entity_db.add(manga_name, track=True)
        assert simple_mock_entity_db.entity_tracked == {"831b12b8-2d0e-4397-8719-1efee4c32f40"}
        assert simple_mock_entity_db.entity_downloads == set()
        simple_mock_entity_db.entity_downloads.add(
            ("831b12b8-2d0e-4397-8719-1efee4c32f40", "01c86808-46fb-4108-aa5d-4e87aee8b2f1")
        )

        mock_get_input.return_value = 1
        simple_mock_entity_db.remove()

        # Assert the entity maps are populated
        assert simple_mock_entity_db.entity_tracked == set()
        assert simple_mock_entity_db.entity_downloads == set()


@mock.patch("cbz_tagger.common.input.get_raw_input")
@mock.patch("cbz_tagger.common.input.get_input")
def test_entity_db_delete_manga(
    mock_get_input,
    mock_get_raw_input,
    simple_mock_entity_db,
    mock_chapter_db,
    manga_name,
    manga_request_id,
    manga_request_response,
):
    with mock.patch.object(MetadataEntity, "from_server_url") as mock_from_server_url:
        mock_from_server_url.return_value = [MetadataEntity(data) for data in manga_request_response["data"]]

        mock_get_input.return_value = 0
        # Simulate user selecting 0 for each input
        mock_get_raw_input.return_value = 0

        simple_mock_entity_db.search = mock.MagicMock(return_value=(manga_request_id, "Oshimai"))
        simple_mock_entity_db.update_manga_entity_id = mock.MagicMock()
        simple_mock_entity_db.chapters = mock_chapter_db
        simple_mock_entity_db.add(manga_name, track=True)
        assert simple_mock_entity_db.entity_tracked == {"831b12b8-2d0e-4397-8719-1efee4c32f40"}
        assert simple_mock_entity_db.entity_downloads == set()
        simple_mock_entity_db.entity_downloads.add(
            ("831b12b8-2d0e-4397-8719-1efee4c32f40", "01c86808-46fb-4108-aa5d-4e87aee8b2f1")
        )

        mock_get_input.return_value = 1
        simple_mock_entity_db.delete()

        # Assert the entity maps are populated
        assert simple_mock_entity_db.entity_map == {}
        assert simple_mock_entity_db.entity_names == {}
        assert simple_mock_entity_db.entity_tracked == set()
        assert simple_mock_entity_db.entity_downloads == set()


def test_entity_db_remove_entity_id_from_tracking(simple_mock_entity_db, manga_request_id):
    """Test remove_entity_id_from_tracking function individually"""
    # Setup entity in tracking
    simple_mock_entity_db.entity_tracked.add(manga_request_id)
    simple_mock_entity_db.entity_chapter_plugin[manga_request_id] = {
        "plugin_type": "mdx",
        "plugin_id": manga_request_id,
    }
    simple_mock_entity_db.entity_downloads.add((manga_request_id, "chapter1"))
    simple_mock_entity_db.entity_downloads.add((manga_request_id, "chapter2"))
    simple_mock_entity_db.entity_downloads.add(("other_entity", "chapter3"))

    # Verify initial state
    assert manga_request_id in simple_mock_entity_db.entity_tracked
    assert manga_request_id in simple_mock_entity_db.entity_chapter_plugin
    assert len(simple_mock_entity_db.entity_downloads) == 3

    # Call the function
    simple_mock_entity_db.remove_entity_id_from_tracking(manga_request_id)

    # Verify entity is removed from tracking
    assert manga_request_id not in simple_mock_entity_db.entity_tracked
    assert manga_request_id not in simple_mock_entity_db.entity_chapter_plugin

    # Verify only chapters for this entity are removed from downloads
    assert len(simple_mock_entity_db.entity_downloads) == 1
    assert ("other_entity", "chapter3") in simple_mock_entity_db.entity_downloads

    # Verify save was called
    simple_mock_entity_db.save.assert_called()


def test_entity_db_remove_entity_id_from_tracking_not_tracked(simple_mock_entity_db, manga_request_id):
    """Test remove_entity_id_from_tracking with entity not in tracking"""
    # Setup entity not in tracking but with downloads
    simple_mock_entity_db.entity_downloads.add((manga_request_id, "chapter1"))
    simple_mock_entity_db.entity_downloads.add(("other_entity", "chapter2"))

    # Verify initial state
    assert manga_request_id not in simple_mock_entity_db.entity_tracked
    assert len(simple_mock_entity_db.entity_downloads) == 2

    # Call the function
    simple_mock_entity_db.remove_entity_id_from_tracking(manga_request_id)

    # Verify entity still not in tracking (no change)
    assert manga_request_id not in simple_mock_entity_db.entity_tracked

    # Verify downloads for this entity are still removed
    assert len(simple_mock_entity_db.entity_downloads) == 1
    assert ("other_entity", "chapter2") in simple_mock_entity_db.entity_downloads

    # Verify save was called
    simple_mock_entity_db.save.assert_called()


def test_entity_db_delete_entity_id(simple_mock_entity_db, manga_request_id):
    """Test delete_entity_id function individually"""
    manga_name = "Test Manga"

    # Setup entity in all databases
    simple_mock_entity_db.entity_map[manga_name] = manga_request_id
    simple_mock_entity_db.entity_names[manga_request_id] = "Clean Test Manga"
    simple_mock_entity_db.entity_tracked.add(manga_request_id)
    simple_mock_entity_db.entity_chapter_plugin[manga_request_id] = {
        "plugin_type": "mdx",
        "plugin_id": manga_request_id,
    }
    simple_mock_entity_db.entity_downloads.add((manga_request_id, "chapter1"))

    # Mock the individual databases
    simple_mock_entity_db.metadata.database = {manga_request_id: mock.MagicMock()}
    simple_mock_entity_db.covers.database = {manga_request_id: mock.MagicMock()}
    simple_mock_entity_db.volumes.database = {manga_request_id: mock.MagicMock()}
    simple_mock_entity_db.chapters.database = {manga_request_id: mock.MagicMock()}

    # Verify initial state
    assert manga_name in simple_mock_entity_db.entity_map
    assert manga_request_id in simple_mock_entity_db.entity_names
    assert manga_request_id in simple_mock_entity_db.entity_tracked
    assert manga_request_id in simple_mock_entity_db.entity_chapter_plugin
    assert len(simple_mock_entity_db.entity_downloads) == 1
    assert manga_request_id in simple_mock_entity_db.metadata.database
    assert manga_request_id in simple_mock_entity_db.covers.database
    assert manga_request_id in simple_mock_entity_db.volumes.database
    assert manga_request_id in simple_mock_entity_db.chapters.database

    # Call the function
    simple_mock_entity_db.delete_entity_id(manga_request_id, manga_name)

    # Verify entity is completely removed
    assert manga_name not in simple_mock_entity_db.entity_map
    assert manga_request_id not in simple_mock_entity_db.entity_names
    assert manga_request_id not in simple_mock_entity_db.entity_tracked
    assert manga_request_id not in simple_mock_entity_db.entity_chapter_plugin
    assert len(simple_mock_entity_db.entity_downloads) == 0
    assert manga_request_id not in simple_mock_entity_db.metadata.database
    assert manga_request_id not in simple_mock_entity_db.covers.database
    assert manga_request_id not in simple_mock_entity_db.volumes.database
    assert manga_request_id not in simple_mock_entity_db.chapters.database

    # Verify save was called
    simple_mock_entity_db.save.assert_called()


def test_entity_db_delete_entity_id_missing_from_some_databases(simple_mock_entity_db, manga_request_id):
    """Test delete_entity_id when entity is missing from some databases"""
    manga_name = "Test Manga"

    # Setup entity in only some databases (simulating partial data)
    simple_mock_entity_db.entity_map[manga_name] = manga_request_id
    simple_mock_entity_db.entity_names[manga_request_id] = "Clean Test Manga"
    simple_mock_entity_db.entity_tracked.add(manga_request_id)

    # Only add to metadata database, not others
    simple_mock_entity_db.metadata.database = {manga_request_id: mock.MagicMock()}
    simple_mock_entity_db.covers.database = {}
    simple_mock_entity_db.volumes.database = {}
    simple_mock_entity_db.chapters.database = {}

    # Call the function - should not raise any errors
    simple_mock_entity_db.delete_entity_id(manga_request_id, manga_name)

    # Verify entity is removed from all maps
    assert manga_name not in simple_mock_entity_db.entity_map
    assert manga_request_id not in simple_mock_entity_db.entity_names
    assert manga_request_id not in simple_mock_entity_db.entity_tracked
    assert manga_request_id not in simple_mock_entity_db.metadata.database

    # Verify save was called
    simple_mock_entity_db.save.assert_called()


def test_entity_db_update_calls_update_manga_entity_id_from_update_name(
    mock_entity_db_with_mock_updates, manga_name, manga_request_id
):
    mock_entity_db_with_mock_updates.update_manga_entity_id = mock.MagicMock()
    mock_entity_db_with_mock_updates.update_manga_entity_name(manga_name)
    mock_entity_db_with_mock_updates.update_manga_entity_id.assert_called_once_with(manga_request_id)


def test_entity_db_update_calls_metadata_and_chapter_on_request(mock_entity_db_with_mock_updates, manga_request_id):
    mock_entity_db_with_mock_updates.update_manga_entity_id(manga_request_id, update_metadata=True)

    mock_entity_db_with_mock_updates.metadata.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_mock_updates.chapters.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_mock_updates.authors.update.assert_called_once()
    mock_entity_db_with_mock_updates.covers.update.assert_called_once()
    mock_entity_db_with_mock_updates.volumes.update.assert_called_once()
    mock_entity_db_with_mock_updates.covers.download.assert_called_once()


def test_entity_db_update_does_not_call_metadata_and_chapter_on_request(
    mock_entity_db_with_mock_updates, manga_request_id
):
    mock_entity_db_with_mock_updates.update_manga_entity_id(manga_request_id, update_metadata=False)

    mock_entity_db_with_mock_updates.metadata.update.assert_not_called()
    mock_entity_db_with_mock_updates.chapters.update.assert_not_called()
    mock_entity_db_with_mock_updates.authors.update.assert_called_once()
    mock_entity_db_with_mock_updates.covers.update.assert_called_once()
    mock_entity_db_with_mock_updates.volumes.update.assert_called_once()
    mock_entity_db_with_mock_updates.covers.download.assert_called_once()


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


def test_entity_db_update_chapter_only_when_no_updates_but_not_latest_chapter(
    mock_entity_db_with_mock_updates_out_of_date_chapter, manga_request_id
):
    mock_entity_db_with_mock_updates_out_of_date_chapter.update_manga_entity_id(manga_request_id)

    mock_entity_db_with_mock_updates_out_of_date_chapter.chapters.update.assert_called_once_with(manga_request_id)
    mock_entity_db_with_mock_updates_out_of_date_chapter.authors.update.assert_called_once()
    mock_entity_db_with_mock_updates_out_of_date_chapter.covers.update.assert_called_once()
    mock_entity_db_with_mock_updates_out_of_date_chapter.volumes.update.assert_called_once()
    mock_entity_db_with_mock_updates_out_of_date_chapter.covers.download.assert_called_once()


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
    mock_entity_db_with_mock_updates.update_manga_entity_id_metadata_and_find_updated_ids = mock.MagicMock(
        return_value=list(mock_entity_db_with_mock_updates.entity_names.keys())
    )
    mock_entity_db_with_mock_updates.update_manga_entity_id = mock.MagicMock()
    mock_entity_db_with_mock_updates.covers.remove_orphaned_covers = mock.MagicMock()
    mock_entity_db_with_mock_updates.refresh("storage")

    mock_entity_db_with_mock_updates.update_manga_entity_id.assert_called_once_with(
        manga_request_id, update_metadata=False
    )
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


def test_entity_database_to_state(mock_entity_db, manga_name):
    state = mock_entity_db.to_state()
    assert state == [
        {
            "entity_id": "831b12b8-2d0e-4397-8719-1efee4c32f40",
            "entity_name": {
                "link": f"https://{Urls.MDX}/title/831b12b8-2d0e-4397-8719-1efee4c32f40",
                "name": manga_name,
            },
            "latest_chapter": 11.0,
            "latest_chapter_date": datetime(2021, 7, 13, 8, 28, 1, tzinfo=timezone.utc),
            "plugin": {"link": f"https://{Urls.MDX}/title/831b12b8-2d0e-4397-8719-1efee4c32f40", "name": "mdx"},
            "status": "🟢",
            "tracked": "🟤",
            "updated": "2022-12-31T11:57:41+00:00",
        }
    ]


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


@mock.patch("cbz_tagger.database.entity_db.EntityDB.update_manga_entity_id_metadata_and_find_updated_ids")
@mock.patch("cbz_tagger.database.entity_db.EntityDB.update_manga_entity_id")
@mock.patch("cbz_tagger.database.entity_db.EntityDB.download_missing_covers")
@mock.patch("cbz_tagger.database.entity_db.EntityDB.remove_orphaned_covers")
@mock.patch("cbz_tagger.database.entity_db.EntityDB.download_missing_chapters")
def test_refresh(
    mock_download_missing_chapters,
    mock_remove_orphaned_covers,
    mock_download_missing_covers,
    mock_update_manga_entity_id,
    mock_update_manga_entity_id_metadata_and_find_updated_ids,
):
    mock_metadata = mock.MagicMock()
    mock_metadata.keys.return_value = ["entity1", "entity2"]
    mock_update_manga_entity_id_metadata_and_find_updated_ids.return_value = ["entity1", "entity2"]

    entity_db = EntityDB(root_path="mock_path")
    entity_db.metadata = mock_metadata

    storage_path = "mock_storage_path"
    entity_db.refresh(storage_path)

    mock_update_manga_entity_id_metadata_and_find_updated_ids.assert_called_once_with(["entity1", "entity2"])
    mock_update_manga_entity_id.assert_any_call("entity1", update_metadata=False)
    mock_update_manga_entity_id.assert_any_call("entity2", update_metadata=False)
    mock_download_missing_covers.assert_called_once()
    mock_remove_orphaned_covers.assert_called_once()
    mock_download_missing_chapters.assert_called_once_with(storage_path)


def test_update_manga_entity_id_metadata_and_find_updated_ids_with_updated_metadata(
    simple_mock_entity_db, manga_request_id
):
    """Test that entities with updated metadata are returned in the list of updated entity IDs."""
    # Setup metadata with a mock that will return different hash values before and after update
    mock_metadata = mock.MagicMock()

    # Need 3 calls: initial, after metadata update (for comparison), final (for result check)
    mock_metadata.to_hash = mock.MagicMock(side_effect=["initial_hash", "updated_hash", "updated_hash"])
    mock_metadata.update = mock.MagicMock()
    mock_metadata.__getitem__ = mock.MagicMock(return_value=mock.MagicMock())

    # Setup chapters with no changes
    mock_chapters = mock.MagicMock()
    mock_chapters.to_hash = mock.MagicMock(return_value="chapter_hash")
    mock_chapters.update = mock.MagicMock()

    simple_mock_entity_db.metadata = mock_metadata
    simple_mock_entity_db.chapters = mock_chapters
    simple_mock_entity_db.entity_chapter_plugin = {}

    # Call the method being tested
    updated_ids = simple_mock_entity_db.update_manga_entity_id_metadata_and_find_updated_ids([manga_request_id])

    # Verify the metadata was updated and the entity ID was returned
    mock_metadata.update.assert_called_once_with([manga_request_id], batch_response=True)
    # Now expect chapters.update to be called since metadata changed
    mock_chapters.update.assert_called_once_with(manga_request_id)
    assert updated_ids == [manga_request_id]


def test_update_manga_entity_id_metadata_and_find_updated_ids_with_updated_chapters(
    simple_mock_entity_db, manga_request_id
):
    """Test that entities with chapter plugins are always returned in the list of updated entity IDs."""
    # Setup metadata with no changes (same hash before and after update)
    mock_metadata = mock.MagicMock()

    mock_metadata.to_hash = mock.MagicMock(return_value="metadata_hash")
    mock_metadata.__getitem__ = mock.MagicMock(return_value=mock.MagicMock())
    mock_metadata.update = mock.MagicMock()

    # Setup chapters
    mock_chapters = mock.MagicMock()
    mock_chapters.to_hash = mock.MagicMock(side_effect=["initial_hash", "updated_hash"])
    mock_chapters.update = mock.MagicMock()

    simple_mock_entity_db.metadata = mock_metadata
    simple_mock_entity_db.chapters = mock_chapters
    simple_mock_entity_db.entity_chapter_plugin = {
        manga_request_id: {"plugin_type": "mdx", "plugin_id": manga_request_id}
    }

    # Call the method being tested
    updated_ids = simple_mock_entity_db.update_manga_entity_id_metadata_and_find_updated_ids([manga_request_id])

    # Verify the metadata and chapters were updated and the entity ID was returned
    mock_metadata.update.assert_called_once_with([manga_request_id], batch_response=True)
    mock_chapters.update.assert_called_once_with(manga_request_id, plugin_type="mdx", plugin_id=manga_request_id)
    assert updated_ids == [manga_request_id]


def test_update_manga_entity_id_metadata_and_find_updated_ids_with_no_updates(simple_mock_entity_db, manga_request_id):
    """Test that entities with no changes in metadata and no chapter plugins are not returned."""
    # Setup metadata with no changes (same hash before and after update)
    mock_metadata = mock.MagicMock()

    mock_metadata.to_hash = mock.MagicMock(return_value="metadata_hash")
    mock_metadata.__getitem__ = mock.MagicMock(return_value=mock.MagicMock())
    mock_metadata.update = mock.MagicMock()

    # Setup chapters
    mock_chapters = mock.MagicMock()
    mock_chapters.to_hash = mock.MagicMock(return_value="chapter_hash")
    mock_chapters.update = mock.MagicMock()

    simple_mock_entity_db.metadata = mock_metadata
    simple_mock_entity_db.chapters = mock_chapters
    simple_mock_entity_db.entity_chapter_plugin = {}

    # Call the method being tested
    updated_ids = simple_mock_entity_db.update_manga_entity_id_metadata_and_find_updated_ids([manga_request_id])

    # Verify the metadata was updated but the entity ID was not returned
    mock_metadata.update.assert_called_once_with([manga_request_id], batch_response=True)
    mock_chapters.update.assert_not_called()
    assert updated_ids == []


def test_update_manga_entity_id_metadata_and_find_updated_ids_with_multiple_entities(simple_mock_entity_db):
    """Test handling multiple entity IDs with some having updates and others not."""
    entity_id1 = "entity1"
    entity_id2 = "entity2"
    entity_id3 = "entity3"
    entity_id4 = "entity4"

    # Setup metadata with varying hash values
    mock_metadata = mock.MagicMock()

    # Need to account for all to_hash calls:
    # - 4 initial calls (one per entity)
    # - 4 calls after metadata update for comparison
    # - 4 final calls for result checking
    mock_metadata.to_hash = mock.MagicMock(
        side_effect=[
            # Initial hashes (4 calls)
            "initial_hash",  # entity1
            "initial_hash",  # entity2
            "initial_hash",  # entity3
            "initial_hash",  # entity4
            # After metadata update hashes (4 calls)
            "initial_hash",  # entity1 - no change
            "updated_hash",  # entity2 - metadata changed
            "initial_hash",  # entity3 - no metadata change
            "initial_hash",  # entity4 - no metadata change
            # Final hashes for result checking (4 calls)
            "initial_hash",  # entity1 - no change
            "updated_hash",  # entity2 - metadata changed
            "initial_hash",  # entity3 - no metadata change
            "initial_hash",  # entity4 - no metadata change
        ]
    )
    mock_metadata.__getitem__ = mock.MagicMock(return_value=mock.MagicMock())
    mock_metadata.update = mock.MagicMock()

    # Setup chapters
    mock_chapters = mock.MagicMock()
    mock_chapters.to_hash = mock.MagicMock(
        side_effect=[
            # Initial hashes (4 calls)
            "initial_hash",  # entity1
            "initial_hash",  # entity2
            "initial_hash",  # entity3
            "initial_hash",  # entity4
            # Final hashes for result checking (4 calls)
            "initial_hash",  # entity1 - no change
            "initial_hash",  # entity2 - no change
            "updated_hash",  # entity3 - chapter changed due to plugin
            "initial_hash",  # entity4 - no change
        ]
    )
    mock_chapters.update = mock.MagicMock()

    simple_mock_entity_db.metadata = mock_metadata
    simple_mock_entity_db.chapters = mock_chapters
    # Entity3 and entity4 have chapter plugins
    simple_mock_entity_db.entity_chapter_plugin = {
        entity_id3: {"plugin_type": "cmk", "plugin_id": entity_id3},
        entity_id4: {"plugin_type": "cmk", "plugin_id": entity_id4},
    }
    simple_mock_entity_db.entity_names = {
        entity_id1: "Entity 1",
        entity_id2: "Entity 2",
        entity_id3: "Entity 3",
        entity_id4: "Entity 4",
    }

    # Call the method being tested with batch_size=2 to test batch processing
    updated_ids = simple_mock_entity_db.update_manga_entity_id_metadata_and_find_updated_ids(
        [entity_id1, entity_id2, entity_id3, entity_id4], batch_size=2
    )

    # Verify the correct calls were made
    assert mock_metadata.update.call_count == 2  # Two batches: [entity1, entity2] and [entity3, entity4]
    # Expect 3 chapters.update calls: entity2 (metadata changed), entity3 (plugin), entity4 (plugin)
    assert mock_chapters.update.call_count == 3

    # Verify the specific calls
    expected_calls = [
        mock.call(entity_id2),  # metadata changed
        mock.call(entity_id3, plugin_type="cmk", plugin_id=entity_id3),  # plugin
        mock.call(entity_id4, plugin_type="cmk", plugin_id=entity_id4),  # plugin
    ]
    mock_chapters.update.assert_has_calls(expected_calls, any_order=False)

    # Entity2 has metadata changes, Entity3 has a chapter plugin (and chapter changes)
    assert sorted(updated_ids) == sorted([entity_id2, entity_id3])


def test_entity_db_delete_chapter_entity_id_from_downloaded_chapters(simple_mock_entity_db, manga_request_id):
    """Test delete_chapter_entity_id_from_downloaded_chapters function when chapter exists"""
    chapter_id = "chapter-123"
    other_chapter_id = "chapter-456"
    other_entity_id = "other-entity-789"

    # Setup entity downloads with multiple chapters
    simple_mock_entity_db.entity_downloads.add((manga_request_id, chapter_id))
    simple_mock_entity_db.entity_downloads.add((manga_request_id, other_chapter_id))
    simple_mock_entity_db.entity_downloads.add((other_entity_id, chapter_id))

    # Verify initial state
    assert len(simple_mock_entity_db.entity_downloads) == 3
    assert (manga_request_id, chapter_id) in simple_mock_entity_db.entity_downloads
    assert (manga_request_id, other_chapter_id) in simple_mock_entity_db.entity_downloads
    assert (other_entity_id, chapter_id) in simple_mock_entity_db.entity_downloads

    # Call the function
    simple_mock_entity_db.delete_chapter_entity_id_from_downloaded_chapters(manga_request_id, chapter_id)

    # Verify only the specific chapter was removed
    assert len(simple_mock_entity_db.entity_downloads) == 2
    assert (manga_request_id, chapter_id) not in simple_mock_entity_db.entity_downloads
    assert (manga_request_id, other_chapter_id) in simple_mock_entity_db.entity_downloads
    assert (other_entity_id, chapter_id) in simple_mock_entity_db.entity_downloads

    # Verify save was called
    simple_mock_entity_db.save.assert_called()


def test_entity_db_delete_chapter_entity_id_from_downloaded_chapters_not_found(simple_mock_entity_db, manga_request_id):
    """Test delete_chapter_entity_id_from_downloaded_chapters function when chapter doesn't exist"""
    chapter_id = "non-existent-chapter"
    existing_chapter_id = "existing-chapter"

    # Setup entity downloads with only one chapter
    simple_mock_entity_db.entity_downloads.add((manga_request_id, existing_chapter_id))

    # Verify initial state
    assert len(simple_mock_entity_db.entity_downloads) == 1
    assert (manga_request_id, existing_chapter_id) in simple_mock_entity_db.entity_downloads
    assert (manga_request_id, chapter_id) not in simple_mock_entity_db.entity_downloads

    # Call the function with non-existent chapter
    simple_mock_entity_db.delete_chapter_entity_id_from_downloaded_chapters(manga_request_id, chapter_id)

    # Verify no changes were made
    assert len(simple_mock_entity_db.entity_downloads) == 1
    assert (manga_request_id, existing_chapter_id) in simple_mock_entity_db.entity_downloads

    # Verify save was not called since no changes were made
    simple_mock_entity_db.save.assert_not_called()


def test_entity_db_delete_chapter_entity_id_from_downloaded_chapters_empty_downloads(
    simple_mock_entity_db, manga_request_id
):
    """Test delete_chapter_entity_id_from_downloaded_chapters function when downloads set is empty"""
    chapter_id = "chapter-123"

    # Verify downloads set is empty
    assert len(simple_mock_entity_db.entity_downloads) == 0

    # Call the function
    simple_mock_entity_db.delete_chapter_entity_id_from_downloaded_chapters(manga_request_id, chapter_id)

    # Verify downloads set remains empty
    assert len(simple_mock_entity_db.entity_downloads) == 0

    # Verify save was not called since no changes were made
    simple_mock_entity_db.save.assert_not_called()


def test_entity_db_delete_chapter_entity_id_from_downloaded_chapters_multiple_same_chapter(simple_mock_entity_db):
    """Test delete_chapter_entity_id_from_downloaded_chapters function with same chapter ID for different entities"""
    entity_id_1 = "entity-1"
    entity_id_2 = "entity-2"
    chapter_id = "shared-chapter-id"

    # Setup downloads with same chapter ID for different entities
    simple_mock_entity_db.entity_downloads.add((entity_id_1, chapter_id))
    simple_mock_entity_db.entity_downloads.add((entity_id_2, chapter_id))

    # Verify initial state
    assert len(simple_mock_entity_db.entity_downloads) == 2
    assert (entity_id_1, chapter_id) in simple_mock_entity_db.entity_downloads
    assert (entity_id_2, chapter_id) in simple_mock_entity_db.entity_downloads

    # Call the function for entity_1 only
    simple_mock_entity_db.delete_chapter_entity_id_from_downloaded_chapters(entity_id_1, chapter_id)

    # Verify only entity_1's chapter was removed
    assert len(simple_mock_entity_db.entity_downloads) == 1
    assert (entity_id_1, chapter_id) not in simple_mock_entity_db.entity_downloads
    assert (entity_id_2, chapter_id) in simple_mock_entity_db.entity_downloads

    # Verify save was called
    simple_mock_entity_db.save.assert_called()


@mock.patch("cbz_tagger.database.entity_db.EntityDB.update_manga_entity_id_metadata_and_find_updated_ids")
@mock.patch("cbz_tagger.database.entity_db.EntityDB.update_manga_entity_id")
@mock.patch("cbz_tagger.database.entity_db.EntityDB.download_missing_covers")
@mock.patch("cbz_tagger.database.entity_db.EntityDB.remove_orphaned_covers")
@mock.patch("cbz_tagger.database.entity_db.EntityDB.download_missing_chapters")
def test_refresh(
    mock_download_missing_chapters,
    mock_remove_orphaned_covers,
    mock_download_missing_covers,
    mock_update_manga_entity_id,
    mock_update_manga_entity_id_metadata_and_find_updated_ids,
):
    mock_metadata = mock.MagicMock()
    mock_metadata.keys.return_value = ["entity1", "entity2"]
    mock_update_manga_entity_id_metadata_and_find_updated_ids.return_value = ["entity1", "entity2"]

    entity_db = EntityDB(root_path="mock_path")
    entity_db.metadata = mock_metadata

    storage_path = "mock_storage_path"
    entity_db.refresh(storage_path)

    mock_update_manga_entity_id_metadata_and_find_updated_ids.assert_called_once_with(["entity1", "entity2"])
    mock_update_manga_entity_id.assert_any_call("entity1", update_metadata=False)
    mock_update_manga_entity_id.assert_any_call("entity2", update_metadata=False)
    mock_download_missing_covers.assert_called_once()
    mock_remove_orphaned_covers.assert_called_once()
    mock_download_missing_chapters.assert_called_once_with(storage_path)
