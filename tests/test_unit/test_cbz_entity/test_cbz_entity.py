import pytest

from cbz_tagger.cbz_entity.cbz_entity import CbzEntity


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


def test_get_name_and_chapter():
    entity = CbzEntity("Simple Name/Simple name - 001.cbz")
    assert entity.get_name_and_chapter() == ("Simple Name", "1")
