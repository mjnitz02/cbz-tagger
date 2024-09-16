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


@mock.patch("os.makedirs")
def test_get_entity_write_path(mock_os_makedirs, mock_cbz_entity):
    actual = mock_cbz_entity.get_entity_write_path("series name", "1")
    assert actual == "/storage_path/series name/series name - Chapter 001.cbz"
    mock_os_makedirs.assert_called_once_with(os.path.join("/storage_path", "series name"), exist_ok=True)

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
    "chapter_prefix",
    [
        "Simple name",
        "Simple name - with hyphen",
        "Simple name : with colon",
        "Simple name . with period",
        "Simple name 1",
        "Simple name 123",
        "Simple name #1",
        "Simple name .01",
    ],
)
@pytest.mark.parametrize(
    "chapter_delimiter",
    [
        " - ",
        " : ",
        "-",
        ":",
    ],
)
@pytest.mark.parametrize(
    "chapter_number_prefix",
    [
        "Chapter ",
        "Chapter ",
        "Ch. ",
        "Ch.",
        "Other ",
        "Other.",
    ],
)
@pytest.mark.parametrize(
    "chapter_suffix",
    [
        "(1)",
        " (6)",
        " - some random words",
        " - some random title with a paren (3)",
        " - Volume 1 Extras",
        " - Volume 12 Extras",
        " - periods.....",
        " - one period.",
    ],
)
@pytest.mark.parametrize(
    "chapter_number,expected",
    [
        ("1", "1"),
        ("1.1", "1.1"),
        ("1.2", "1.2"),
        ("01", "1"),
        ("01.1", "1.1"),
        ("01.2", "1.2"),
        ("001", "1"),
        ("001.1", "1.1"),
        ("001.2", "1.2"),
        ("0.1", "0.1"),
        ("0.2", "0.2"),
    ],
)
def test_chapter_number_parsing(
    chapter_prefix, chapter_delimiter, chapter_number_prefix, chapter_suffix, chapter_number, expected
):
    # Test / pathing
    filename = f"{chapter_prefix}/{chapter_prefix}{chapter_delimiter}{chapter_number_prefix}{chapter_number}{chapter_suffix}.cbz"
    entity = CbzEntity(filename)
    assert entity.chapter_number == expected

    # Test \\ pathing
    filename = f"{chapter_prefix}\\{chapter_prefix}{chapter_delimiter}{chapter_number_prefix}{chapter_number}{chapter_suffix}.cbz"
    entity = CbzEntity(filename)
    assert entity.chapter_number == expected


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
