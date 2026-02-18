import os
import re
from datetime import datetime
from datetime import timedelta
from unittest.mock import patch

import pytest

from cbz_tagger.entities.chapter_entity import ChapterEntity
from cbz_tagger.entities.plugins.kal import ChapterPluginKAL


@pytest.mark.parametrize(
    "input_str, min_delta, max_delta",
    [
        ("5 years ago", timedelta(days=365 * 5), timedelta(days=365 * 5 + 1)),
        ("1 year ago", timedelta(days=365), timedelta(days=366)),
        ("9 months ago", timedelta(days=30 * 9), timedelta(days=30 * 9 + 1)),
        ("2 months ago", timedelta(days=60), timedelta(days=61)),
        ("18 minutes ago", timedelta(minutes=18), timedelta(minutes=19)),
        ("2 days ago", timedelta(days=2), timedelta(days=3)),
        ("1 day ago", timedelta(days=1), timedelta(days=2)),
    ],
)
def test_get_approximate_date_valid(input_str, min_delta, max_delta):
    result = ChapterPluginKAL.get_approximate_date(input_str)
    assert result is not None
    # Check ISO 8601 format
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*", result)
    # Check that the date is within expected range
    dt = datetime.fromisoformat(result)
    now = datetime.now().astimezone()
    delta = now - dt
    assert min_delta <= delta <= max_delta


@pytest.mark.parametrize(
    "input_str",
    [
        "invalid string",
        "ago",
        "",
        "5 centuries ago",
        "2 weeks ago",
    ],
)
def test_get_approximate_date_invalid(input_str):
    result = ChapterPluginKAL.get_approximate_date(input_str)
    assert result is None


@pytest.fixture
def kal_series_response(tests_fixtures_path):
    with open(os.path.join(tests_fixtures_path, "kal_series.txt"), encoding="utf-8") as file:
        return file.read()


@pytest.fixture
def kal_chapter_response(tests_fixtures_path):
    with open(os.path.join(tests_fixtures_path, "kal_chapter.txt"), encoding="utf-8") as file:
        return file.read()


@pytest.fixture
def chapter_entity(requests_mock, kal_series_response, kal_chapter_response):
    requests_mock.get(
        f"https://{ChapterPluginKAL.BASE_URL}/manga/example_manga",
        text=kal_series_response,
    )
    requests_mock.get(
        "http://kal.example.com/chapter",
        text=kal_chapter_response,
    )

    return ChapterEntity(
        {
            "id": "chapter_id",
            "attributes": {
                "chapter": "1",
                "translatedLanguage": "en",
                "pages": 3,
                "url": "http://kal.example.com/chapter",
            },
            "relationships": [{"type": "scanlation_group", "id": "group_id"}],
            "type": ChapterPluginKAL.PLUGIN_TYPE,
        },
    )


def test_get_chapter_url(chapter_entity):
    result = chapter_entity.get_chapter_url()
    assert result == "http://kal.example.com/chapter"


def test_from_server_url_no_plugin_id(chapter_entity):
    with pytest.raises(EnvironmentError, match="plugin_id not provided"):
        chapter_entity.from_server_url({"ids[]": ["example_manga"]}, plugin_type=ChapterPluginKAL.PLUGIN_TYPE)


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_from_server_url(mock_sleep, mock_random, chapter_entity):
    result = chapter_entity.from_server_url(
        {"ids[]": ["example_manga"]}, plugin_type=ChapterPluginKAL.PLUGIN_TYPE, plugin_id="example_manga"
    )

    assert len(result) == 3
    assert result[0].entity_id == "example_manga-example-chapter-5"
    assert result[0].get_chapter_url() == f"https://{ChapterPluginKAL.BASE_URL}/manga/example/chapter-5"
    assert result[1].entity_id == "example_manga-example-chapter-3.1"
    assert result[1].get_chapter_url() == f"https://{ChapterPluginKAL.BASE_URL}/manga/example/chapter-3.1"
    assert result[2].entity_id == "example_manga-example-chapter-1"
    assert result[2].get_chapter_url() == f"https://{ChapterPluginKAL.BASE_URL}/manga/example/chapter-1"


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_parse_info_feed(mock_sleep, mock_random, chapter_entity):
    _ = chapter_entity
    result = ChapterPluginKAL.parse_info_feed("example_manga")

    assert len(result) == 3
    for chapter, expected_id, expected_chapter, expected_url in zip(
        result,
        [
            "example_manga-example-chapter-5",
            "example_manga-example-chapter-3.1",
            "example_manga-example-chapter-1",
        ],
        ["5", "3.1", "1"],
        [
            f"https://{ChapterPluginKAL.BASE_URL}/manga/example/chapter-5",
            f"https://{ChapterPluginKAL.BASE_URL}/manga/example/chapter-3.1",
            f"https://{ChapterPluginKAL.BASE_URL}/manga/example/chapter-1",
        ],
        strict=True,
    ):
        assert chapter["id"] == expected_id
        assert chapter["type"] == "kal"
        attrs = chapter["attributes"]
        assert attrs["title"] == f"Chapter {expected_chapter}"
        assert attrs["url"] == expected_url
        assert attrs["chapter"] == expected_chapter
        assert attrs["translatedLanguage"] == "en"
        assert attrs["pages"] == -1
        assert attrs["volume"] is None
        # Accept None or any non-empty string for createdAt/updatedAt
        for key in ("createdAt", "updatedAt"):
            val = attrs[key]
            assert val is None or (isinstance(val, str) and val)
        assert chapter["relationships"] == [{"type": "scanlation_group", "id": None}]


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_parse_chapter_download_links(mock_sleep, mock_random, chapter_entity):
    result = chapter_entity.parse_chapter_download_links("http://kal.example.com/chapter")

    assert result == [
        "https://site.com/chapter-5/6841338_720_4030_548075.webp",
        "https://site.com/chapter-5/6841339_720_4030_437011.webp",
        "https://site.com/chapter-5/6841340_720_1242_156219.webp",
    ]
