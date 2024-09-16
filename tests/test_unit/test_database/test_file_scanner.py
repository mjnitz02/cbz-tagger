import os
from unittest import mock

import pytest

from cbz_tagger.container.file_scanner import FileScanner


@pytest.fixture
def scanner(mock_entity_db):
    obj = FileScanner("/config_path/", "/scan_path", "/storage_path")
    obj.entity_database = mock_entity_db
    return obj


@pytest.fixture
def mock_get_paths():
    return [
        (
            "/root/path/to/files/series name",
            ["series name - chapter 1.cbz", "series name - chapter 2.cbz", "series name - chapter 3.cbz"],
        ),
        (
            "/root/path/to/files/series name 2",
            ["series name 2 - chapter 1.cbz", "series name 2 - chapter 2.cbz", "series name 2 - chapter 3.cbz"],
        ),
        ("/root/path/to/files/series name 3", ["series name 3 - chapter 1.cbz"]),
        ("/root/path/to/files/junk", ["something.txt"]),
    ]


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


def test_get_entity_read_path(scanner):
    actual = scanner.get_entity_read_path("series name/series name - chapter 1.cbz")
    assert actual == "/scan_path/series name/series name - chapter 1.cbz"


def test_get_entity_cover_image_path(scanner):
    actual = scanner.get_entity_cover_image_path("image_filename.jpg")
    assert actual == "/config_path/images/image_filename.jpg"


@mock.patch("os.makedirs")
def test_get_entity_write_path(mock_os_makedirs, scanner):
    actual = scanner.get_entity_write_path("series name", "1")
    assert actual == "/storage_path/series name/series name - Chapter 001.cbz"
    mock_os_makedirs.assert_called_once_with(os.path.join("/storage_path", "series name"), exist_ok=True)

    actual = scanner.get_entity_write_path("series name", "10")
    assert actual == "/storage_path/series name/series name - Chapter 010.cbz"

    actual = scanner.get_entity_write_path("series name", "1.1")
    assert actual == "/storage_path/series name/series name - Chapter 001.1.cbz"

    actual = scanner.get_entity_write_path("series name", "1.10")
    assert actual == "/storage_path/series name/series name - Chapter 001.10.cbz"

    actual = scanner.get_entity_write_path("series name", "10.1")
    assert actual == "/storage_path/series name/series name - Chapter 010.1.cbz"

    actual = scanner.get_entity_write_path("series name", "10.12")
    assert actual == "/storage_path/series name/series name - Chapter 010.12.cbz"

    actual = scanner.get_entity_write_path("series name", "100.1")
    assert actual == "/storage_path/series name/series name - Chapter 100.1.cbz"

    actual = scanner.get_entity_write_path("series name", "100.12")
    assert actual == "/storage_path/series name/series name - Chapter 100.12.cbz"

    # If there is trash we do the best we can to format the chapter
    actual = scanner.get_entity_write_path("series name", "1.1a")
    assert actual == "/storage_path/series name/series name - Chapter 01.1a.cbz"

    actual = scanner.get_entity_write_path("series name", "1.10b")
    assert actual == "/storage_path/series name/series name - Chapter 1.10b.cbz"


def test_file_scanner_can_get_metadata_for_present_series(scanner, manga_name, mock_chapter_1_xml):
    scanner.entity_database.add = mock.MagicMock()
    entity_name, entity_xml, entity_image_path = scanner.get_metadata(manga_name, "1")

    assert entity_name == "Oshimai"
    assert entity_image_path == "1d387431-eb38-40e9-bc6e-97e4ea4092dc.jpg"
    assert entity_xml == mock_chapter_1_xml
    scanner.entity_database.add.assert_not_called()


def test_file_scanner_can_add_missing_on_get_metadata_not_found(scanner):
    scanner.entity_database.add_and_update = mock.MagicMock()
    scanner.entity_database.save = mock.MagicMock()
    scanner.entity_database.get_comicinfo_and_image = mock.MagicMock()

    scanner.get_metadata("unknown manga", "1")

    scanner.entity_database.add_and_update.assert_called_once()
    scanner.entity_database.save.assert_called_once()
    scanner.entity_database.get_comicinfo_and_image.assert_called_once()


def test_file_scanner_can_raises_error_on_missing_if_add_new_disabled(scanner):
    scanner.add_missing = False

    msg = "Manual mode must be enabled for adding missing manga to the database."
    with pytest.raises(RuntimeError, match=msg):
        scanner.get_metadata("unknown manga", "1")


def test_file_scanner_update_calls_entity_database_update(scanner, manga_name):
    scanner.entity_database.check_manga_missing = mock.MagicMock(return_value=False)
    scanner.entity_database.update_manga_entity = mock.MagicMock()
    scanner.update_metadata(manga_name)
    scanner.entity_database.update_manga_entity.assert_called_once_with(manga_name)
