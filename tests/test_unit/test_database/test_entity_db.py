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
