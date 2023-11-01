import os
from unittest import mock

import pytest

from cbz_tagger.cbz_entity.cbz_scanner import CbzScanner


@pytest.fixture
def scanner():
    return CbzScanner("/config_path/", "/scan_path", "/storage_path")


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
