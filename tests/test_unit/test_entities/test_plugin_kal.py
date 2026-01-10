import os

from unittest.mock import patch

import pytest

from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.enums import Urls
from cbz_tagger.entities.chapter_entity import ChapterEntity
from cbz_tagger.entities.chapter_plugins.kal import ChapterPluginKAL


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
        f"https://{Urls.KAL}/manga/example_manga",
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
            "type": Plugins.KAL,
        },
    )


def test_get_chapter_url(chapter_entity):
    result = chapter_entity.get_chapter_url()
    assert result == "http://kal.example.com/chapter"


def test_from_server_url_no_plugin_id(chapter_entity):
    with pytest.raises(EnvironmentError, match="plugin_id not provided"):
        chapter_entity.from_server_url({"ids[]": ["example_manga"]}, plugin_type=Plugins.CMK)


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_from_server_url(mock_sleep, mock_random, chapter_entity):
    result = chapter_entity.from_server_url(
        {"ids[]": ["example_manga"]}, plugin_type=Plugins.KAL, plugin_id="example_manga"
    )

    assert len(result) == 3
    assert result[0].entity_id == "example_manga-example-chapter-5"
    assert result[0].get_chapter_url() == f"https://{Urls.KAL}/manga/example/chapter-5"
    assert result[1].entity_id == "example_manga-example-chapter-3.1"
    assert result[1].get_chapter_url() == f"https://{Urls.KAL}/manga/example/chapter-3.1"
    assert result[2].entity_id == "example_manga-example-chapter-1"
    assert result[2].get_chapter_url() == f"https://{Urls.KAL}/manga/example/chapter-1"


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_parse_info_feed(mock_sleep, mock_random, chapter_entity):
    _ = chapter_entity
    result = ChapterPluginKAL.parse_info_feed("example_manga")

    assert result == [
        {
            "id": "example_manga-example-chapter-5",
            "type": "kal",
            "attributes": {
                "title": "Chapter 5",
                "url": f"https://{Urls.KAL}/manga/example/chapter-5",
                "chapter": "5",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
                "updatedAt": None,
            },
        },
        {
            "id": "example_manga-example-chapter-3.1",
            "type": "kal",
            "attributes": {
                "title": "Chapter 3.1",
                "url": f"https://{Urls.KAL}/manga/example/chapter-3.1",
                "chapter": "3.1",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
                "updatedAt": None,
            },
        },
        {
            "id": "example_manga-example-chapter-1",
            "type": "kal",
            "attributes": {
                "title": "Chapter 1",
                "url": f"https://{Urls.KAL}/manga/example/chapter-1",
                "chapter": "1",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
                "updatedAt": None,
            },
        },
    ]


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_parse_chapter_download_links(mock_sleep, mock_random, chapter_entity):
    result = chapter_entity.parse_chapter_download_links("http://kal.example.com/chapter")

    assert result == [
        "https://site.com/chapter-5/6841338_720_4030_548075.webp",
        "https://site.com/chapter-5/6841339_720_4030_437011.webp",
        "https://site.com/chapter-5/6841340_720_1242_156219.webp",
    ]
