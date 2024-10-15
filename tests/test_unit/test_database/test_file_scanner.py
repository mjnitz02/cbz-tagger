from unittest import mock
from unittest.mock import patch

import pytest

from cbz_tagger.database.file_scanner import FileScanner
from cbz_tagger.entities.cbz_entity import CbzEntity


@pytest.fixture
def scanner(mock_entity_db):
    obj = FileScanner("/config_path/", "/scan_path", "/storage_path")
    obj.entity_database = mock_entity_db
    obj.entity_database.update_manga_entity_name = mock.MagicMock()
    obj.entity_database.update_manga_entity_id = mock.MagicMock()
    return obj


@pytest.fixture
def mock_get_paths():
    return [
        (
            "/root/path/to/files/series name",
            [
                "series name - chapter 1.cbz",
                "series name - chapter 2.cbz",
                "series name - chapter 3.cbz",
            ],
        ),
        (
            "/root/path/to/files/series name 2",
            [
                "series name 2 - chapter 1.cbz",
                "series name 2 - chapter 2.cbz",
                "series name 2 - chapter 3.cbz",
            ],
        ),
        ("/root/path/to/files/series name 3", ["series name 3 - chapter 1.cbz"]),
        ("/root/path/to/files/junk", ["something.txt"]),
    ]


def test_run_without_tracked_entities(scanner):
    scanner.run_scan = mock.MagicMock()
    scanner.entity_database.refresh = mock.MagicMock()
    with patch("cbz_tagger.database.entity_db.EntityDB.load", return_value=scanner.entity_database) as mock_load:
        scanner.run()

    mock_load.assert_called_once()
    scanner.run_scan.assert_called_once()
    scanner.entity_database.refresh.assert_not_called()


def test_run_with_tracked_entities(scanner):
    scanner.run_scan = mock.MagicMock()
    scanner.entity_database.refresh = mock.MagicMock()
    scanner.entity_database.entity_tracked.add("series name")
    with patch("cbz_tagger.database.entity_db.EntityDB.load", return_value=scanner.entity_database) as mock_load:
        scanner.run()

    mock_load.assert_called_once()
    scanner.run_scan.assert_called_once()
    scanner.entity_database.refresh.assert_called_once_with(scanner.storage_path)


def test_run_scan(scanner):
    with (
        patch.object(scanner, "scan", side_effect=[False, True]) as mock_scan,
        patch("cbz_tagger.database.entity_db.EntityDB.load", return_value=scanner.entity_database),
        patch("time.sleep") as mock_sleep,
    ):
        scanner.run_scan()

        assert mock_scan.call_count == 2
        mock_sleep.assert_called_once_with(120)


def test_get_cbz_files(scanner, mock_get_paths):
    scanner.scan_path = "/root/path/to/files"
    scanner.get_files = mock.MagicMock(return_value=mock_get_paths)
    actual = scanner.get_cbz_files()
    assert actual == [
        "series name 2/series name 2 - chapter 1.cbz",
        "series name 2/series name 2 - chapter 2.cbz",
        "series name 2/series name 2 - chapter 3.cbz",
        "series name 3/series name 3 - chapter 1.cbz",
        "series name/series name - chapter 1.cbz",
        "series name/series name - chapter 2.cbz",
        "series name/series name - chapter 3.cbz",
    ]


def test_file_scanner_can_get_metadata_for_present_series(scanner, mock_chapter_1_xml):
    scanner.entity_database.add = mock.MagicMock()
    cbz_entity = CbzEntity(
        "Kanojyo to Himitsu to Koimoyou/Kanojyo to Himitsu to Koimoyou - 1.cbz",
        scanner.config_path,
        scanner.scan_path,
        scanner.storage_path,
    )
    entity_name, entity_xml, entity_image_path = scanner.get_cbz_comicinfo_and_image(cbz_entity)

    assert entity_name == "Oshimai"
    assert entity_image_path == "1d387431-eb38-40e9-bc6e-97e4ea4092dc.jpg"
    assert entity_xml == mock_chapter_1_xml
    scanner.entity_database.add.assert_not_called()
    scanner.entity_database.update_manga_entity_name.assert_called_once()


def test_file_scanner_can_add_missing_on_get_metadata_not_found(scanner):
    scanner.entity_database.add = mock.MagicMock()
    scanner.entity_database.get_comicinfo_and_image = mock.MagicMock(return_value=(None, None, None))
    cbz_entity = CbzEntity("Unknown/Unknown - 1.cbz", scanner.config_path, scanner.scan_path, scanner.storage_path)
    scanner.get_cbz_comicinfo_and_image(cbz_entity)

    scanner.entity_database.add.assert_called_once()
    scanner.entity_database.update_manga_entity_name.assert_called_once()
    scanner.entity_database.get_comicinfo_and_image.assert_called_once()


def test_file_scanner_can_raises_error_on_missing_if_add_new_disabled(scanner):
    scanner.add_missing = False
    scanner.entity_database.add = mock.MagicMock()
    scanner.entity_database.get_comicinfo_and_image = mock.MagicMock()
    cbz_entity = CbzEntity("Unknown/Unknown - 1.cbz", scanner.config_path, scanner.scan_path, scanner.storage_path)

    scanner.get_cbz_comicinfo_and_image(cbz_entity)
    # Assert nothing happened when add_missing is False and series is not found
    scanner.entity_database.add.assert_not_called()
    scanner.entity_database.update_manga_entity_name.assert_not_called()
    scanner.entity_database.get_comicinfo_and_image.assert_not_called()
