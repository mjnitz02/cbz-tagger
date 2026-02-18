import os
from unittest import mock

import pytest

from cbz_tagger.entities.cbz_entity import CbzEntity


@pytest.fixture
def mock_cbz_entity():
    return CbzEntity("series name/series name - chapter 1.cbz", "/config_path/", "/scan_path", "/storage_path")


def test_get_entity_read_path(mock_cbz_entity):
    actual = mock_cbz_entity.get_entity_read_path()
    assert actual == "/scan_path/series name/series name - chapter 1.cbz"


def test_get_entity_cover_image_path(mock_cbz_entity):
    actual = mock_cbz_entity.get_entity_cover_image_path("image_filename.jpg")
    assert actual == "/config_path/images/image_filename.jpg"


@mock.patch("os.chown")
@mock.patch("os.makedirs")
@mock.patch("os.path.exists")
def test_get_entity_write_path(mock_os_path_exists, mock_os_makedirs, mock_os_chown, mock_cbz_entity):
    target_dir = os.path.join("/storage_path", "series name")
    # Simulate the real-world case: the mounted storage path already exists,
    # only the new series subdirectory does not.
    mock_os_path_exists.side_effect = lambda path: path != target_dir

    actual = mock_cbz_entity.get_entity_write_path("series name", "1")
    assert actual == "/storage_path/series name/series name - Chapter 001.cbz"
    mock_os_makedirs.assert_called_once_with(target_dir, exist_ok=True)
    mock_os_chown.assert_called_once_with(target_dir, mock.ANY, mock.ANY)

    actual = mock_cbz_entity.get_entity_write_path("series name", "10")
    assert actual == "/storage_path/series name/series name - Chapter 010.cbz"

    actual = mock_cbz_entity.get_entity_write_path("series name", "1.1")
    assert actual == "/storage_path/series name/series name - Chapter 001.1.cbz"

    actual = mock_cbz_entity.get_entity_write_path("series name", "1.10")
    assert actual == "/storage_path/series name/series name - Chapter 001.10.cbz"

    actual = mock_cbz_entity.get_entity_write_path("series name", "10.1")
    assert actual == "/storage_path/series name/series name - Chapter 010.1.cbz"

    actual = mock_cbz_entity.get_entity_write_path("series name", "10.12")
    assert actual == "/storage_path/series name/series name - Chapter 010.12.cbz"

    actual = mock_cbz_entity.get_entity_write_path("series name", "100.1")
    assert actual == "/storage_path/series name/series name - Chapter 100.1.cbz"

    actual = mock_cbz_entity.get_entity_write_path("series name", "100.12")
    assert actual == "/storage_path/series name/series name - Chapter 100.12.cbz"

    # If there is trash we do the best we can to format the chapter
    actual = mock_cbz_entity.get_entity_write_path("series name", "1.1a")
    assert actual == "/storage_path/series name/series name - Chapter 01.1a.cbz"

    actual = mock_cbz_entity.get_entity_write_path("series name", "1.10b")
    assert actual == "/storage_path/series name/series name - Chapter 1.10b.cbz"


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("SimpleName/Simple name file.cbz", "SimpleName"),
        ("Simple Name/Simple name file.cbz", "Simple Name"),
        ("Simple Name?/Simple name file.cbz", "Simple Name?"),
        ("Simple Name - with hyphen/Simple name file.cbz", "Simple Name - with hyphen"),
        ("Simple Name : with colon/Simple name file.cbz", "Simple Name : with colon"),
        ("Simple Name: with colon/Simple name file.cbz", "Simple Name: with colon"),
        ("Simple Name: with colon @ comic/Simple name file.cbz", "Simple Name: with colon @ comic"),
        ("SOME×CONTENT/Simple name file.cbz", "SOME×CONTENT"),
    ],
)
def test_manga_name_parsing(filename, expected):
    entity = CbzEntity(filename)
    assert entity.manga_name == expected


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("SimpleName/Simple name file.cbz", "Simple name file.cbz"),
        ("Simple Name/Simple name file.cbz", "Simple name file.cbz"),
        ("Simple Name?/Simple name file.cbz", "Simple name file.cbz"),
        ("Simple Name/Simple name - 1.cbz", "Simple name - 1.cbz"),
        ("Simple Name/Simple name - 1.1.cbz", "Simple name - 1.1.cbz"),
        ("Simple Name/Simple name - 1.2.cbz", "Simple name - 1.2.cbz"),
        ("Simple Name/Simple name - 001.cbz", "Simple name - 001.cbz"),
        ("Simple Name/Simple name - 001.1.cbz", "Simple name - 001.1.cbz"),
        ("Simple Name/Simple name - 001.2.cbz", "Simple name - 001.2.cbz"),
        ("Simple Name/Simple name - Chapter 1.cbz", "Simple name - Chapter 1.cbz"),
        ("Simple Name/Simple name - Chapter 1.1.cbz", "Simple name - Chapter 1.1.cbz"),
        ("Simple Name/Simple name - Chapter 1.2.cbz", "Simple name - Chapter 1.2.cbz"),
        ("Simple Name/Simple name - Chapter 001.cbz", "Simple name - Chapter 001.cbz"),
        ("Simple Name/Simple name - Chapter 001.1.cbz", "Simple name - Chapter 001.1.cbz"),
        ("Simple Name/Simple name - Chapter 001.2.cbz", "Simple name - Chapter 001.2.cbz"),
        ("Simple Name/Simple name - Ch. 001.cbz", "Simple name - Ch. 001.cbz"),
        ("Simple Name/Simple name - Ch. 001.1.cbz", "Simple name - Ch. 001.1.cbz"),
        ("Simple Name/Simple name - Ch.001.cbz", "Simple name - Ch.001.cbz"),
        ("Simple Name/Simple name - Ch.001.1.cbz", "Simple name - Ch.001.1.cbz"),
        ("Simple Name/Simple name - Other 001.cbz", "Simple name - Other 001.cbz"),
        ("Simple Name/Simple name - Other 001.1.cbz", "Simple name - Other 001.1.cbz"),
        ("Simple Name/Simple name - Other.001.cbz", "Simple name - Other.001.cbz"),
        ("Simple Name/Simple name - Other.001.1.cbz", "Simple name - Other.001.1.cbz"),
        ("Simple Name/Simple name - extra part - Chapter 1.cbz", "Simple name - extra part - Chapter 1.cbz"),
        ("Simple Name/Simple name - extra part - Chapter 1.1.cbz", "Simple name - extra part - Chapter 1.1.cbz"),
        ("Simple Name/Simple name - extra part - Chapter 1.2.cbz", "Simple name - extra part - Chapter 1.2.cbz"),
        ("Simple Name/Simple name - extra part - Chapter 001.cbz", "Simple name - extra part - Chapter 001.cbz"),
        ("Simple Name/Simple name - extra part - Chapter 001.1.cbz", "Simple name - extra part - Chapter 001.1.cbz"),
        ("Simple Name/Simple name - extra part - Chapter 001.2.cbz", "Simple name - extra part - Chapter 001.2.cbz"),
    ],
)
def test_chapter_name_parsing(filename, expected):
    entity = CbzEntity(filename)
    assert entity.chapter_name == expected


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("Simple Name/Simple name - 1.cbz", False),
        ("Simple Name/Simple name - 1.1.cbz", False),
        ("Simple Name/Simple name - 1.2.cbz", False),
        ("Simple Name/Simple name - 001.cbz", False),
        ("Simple Name/Simple name - Chapter 1.cbz", False),
        ("Simple Name/Simple name - Chapter 1.1.cbz", False),
        ("Simple Name/Simple name - Chapter 1.2.cbz", False),
        ("Simple Name/Simple name - Chapter 001.cbz", False),
        ("Simple Name/Simple name - Volume 1 - Chapter 1.cbz", False),
        ("Simple Name/Simple name - Volume 01 - Chapter 1.cbz", False),
        ("Simple Name/Simple name - Volume 001 - Chapter 1.cbz", False),
        ("Simple Name/Simple name - Volume 10 - Chapter 1.cbz", False),
        ("Simple Name/Simple name - Volume 12 - Chapter 1.cbz", False),
        ("Simple Name/Simple name - Volume 101 - Chapter 1.cbz", False),
        ("Simple Name/Simple name - Volume 1.cbz", True),
        ("Simple Name/Simple name - Volume 01.cbz", True),
        ("Simple Name/Simple name - Volume 001.cbz", True),
        ("Simple Name/Simple name - Volume 10.cbz", True),
        ("Simple Name/Simple name - Volume 12.cbz", True),
        ("Simple Name/Simple name - Volume 101.cbz", True),
    ],
)
def test_chapter_is_volume_parsing(filename, expected):
    entity = CbzEntity(filename)
    assert entity.chapter_is_volume == expected


@pytest.mark.parametrize(
    "filename,expected",
    [
        # Test chapter number normalization with various formats
        ("Simple name/Simple name - Chapter 1.cbz", "1"),
        ("Simple name/Simple name - Chapter 1.1.cbz", "1.1"),
        ("Simple name/Simple name - Chapter 01.cbz", "1"),
        ("Simple name/Simple name - Chapter 01.1.cbz", "1.1"),
        ("Simple name/Simple name - Chapter 001.cbz", "1"),
        ("Simple name/Simple name - Chapter 001.1.cbz", "1.1"),
        ("Simple name/Simple name - Chapter 0.1.cbz", "0.1"),
        # Test various delimiters
        ("Simple name/Simple name - Chapter 1.cbz", "1"),
        ("Simple name/Simple name : Chapter 1.cbz", "1"),
        ("Simple name/Simple name-Chapter 1.cbz", "1"),
        ("Simple name/Simple name:Chapter 1.cbz", "1"),
        # Test various chapter prefixes
        ("Simple name/Simple name - Ch. 1.cbz", "1"),
        ("Simple name/Simple name - Ch.1.cbz", "1"),
        ("Simple name/Simple name - Other 1.cbz", "1"),
        ("Simple name/Simple name - Other.1.cbz", "1"),
        # Test various suffixes
        ("Simple name/Simple name - Chapter 1 (1).cbz", "1"),
        ("Simple name/Simple name - Chapter 1 - some random words.cbz", "1"),
        ("Simple name/Simple name - Chapter 1 - Volume 1 Extras.cbz", "1"),
        ("Simple name/Simple name - Chapter 1.1 - some title (3).cbz", "1.1"),
        # Test complex series names
        ("Simple name - with hyphen/Simple name - with hyphen - Chapter 1.cbz", "1"),
        ("Simple name : with colon/Simple name : with colon - Chapter 1.cbz", "1"),
        ("Simple name . with period/Simple name . with period - Chapter 1.cbz", "1"),
        ("Simple name 123/Simple name 123 - Chapter 1.cbz", "1"),
        ("Simple name #1/Simple name #1 - Chapter 1.cbz", "1"),
        ("Simple name - Volume 1/Simple name - Volume 1 - Chapter 1.cbz", "1"),
        # Test combinations of complex features
        ("Simple name #1/Simple name #1 : Ch.001.1 - Volume 12 Extras.cbz", "1.1"),
        ("Simple name 123/Simple name 123-Other.01.2 (6).cbz", "1.2"),
        # Test backslash paths
        ("Simple name\\Simple name - Chapter 1.cbz", "1"),
        ("Simple name\\Simple name - Chapter 001.1.cbz", "1.1"),
    ],
)
def test_chapter_number_parsing(filename, expected):
    entity = CbzEntity(filename)
    assert entity.chapter_number == expected
    assert not entity.chapter_is_volume


@pytest.mark.parametrize(
    "template_name, expected_chapter",
    [
        ("TITLE - Vol. 01 Ch. 008 -  some naming 2", "8"),
        ("TITLE - Vol. 02 Ch. 008 - some (other word) Part 2", "8"),
    ],
)
def test_one_off_chapter_number_parsing(template_name, expected_chapter):
    # Test / pathing
    entity = CbzEntity(template_name)
    assert entity.chapter_number == expected_chapter


def test_get_name_and_chapter():
    entity = CbzEntity("Simple Name/Simple name - 001.cbz")
    assert entity.get_name_and_chapter() == ("Simple Name", "1")
