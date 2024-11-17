import os

import pytest
import requests_mock  # pylint: disable=unused-import

from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.enums import Urls
from cbz_tagger.entities.chapter_entity import ChapterEntity
from cbz_tagger.entities.chapter_plugins.wbc import ChapterPluginWBC


@pytest.fixture
def wbc_series_response(tests_fixtures_path):
    with open(os.path.join(tests_fixtures_path, "wbc_series.txt"), encoding="utf-8") as file:
        return file.read()


@pytest.fixture
def wbc_chapter_response(tests_fixtures_path):
    with open(os.path.join(tests_fixtures_path, "wbc_chapter.txt"), encoding="utf-8") as file:
        return file.read()


@pytest.fixture
def chapter_entity(requests_mock, wbc_series_response, wbc_chapter_response):
    requests_mock.get(
        f"https://{Urls.WBC}/series/example_manga/full-chapter-list",
        text=wbc_series_response,
    )
    requests_mock.get(
        "http://wbc.example.com/chapter",
        text=wbc_chapter_response,
    )

    return ChapterEntity(
        {
            "id": "chapter_id",
            "attributes": {
                "chapter": "1",
                "translatedLanguage": "en",
                "pages": 3,
                "url": "http://wbc.example.com/chapter",
            },
            "relationships": [{"type": "scanlation_group", "id": "group_id"}],
            "type": Plugins.WBC,
        },
    )


def test_get_chapter_url(chapter_entity):
    result = chapter_entity.get_chapter_url()
    assert result == "http://wbc.example.com/chapter"


def test_from_server_url_no_plugin_id(chapter_entity):
    with pytest.raises(EnvironmentError, match="plugin_id not provided"):
        chapter_entity.from_server_url({"ids[]": ["example_manga"]}, plugin_type=Plugins.MSE)


def test_from_server_url(chapter_entity):
    result = chapter_entity.from_server_url(
        {"ids[]": ["example_manga"]}, plugin_type=Plugins.WBC, plugin_id="example_manga"
    )

    assert len(result) == 3
    assert result[0].entity_id == "example_manga-01jcvm87vk3jfdwj3hmk08y6sp"
    assert result[0].get_chapter_url() == "https://site.com/chapters/01JCVM87VK3JFDWJ3HMK08Y6SP"
    assert result[1].entity_id == "example_manga-01jbq5xgy6vgm1557epndzmv8j"
    assert result[1].get_chapter_url() == "https://site.com/chapters/01JBQ5XGY6VGM1557EPNDZMV8J"
    assert result[2].entity_id == "example_manga-01jam51v6hr5jra3c2ketzbb7g"
    assert result[2].get_chapter_url() == "https://site.com/chapters/01JAM51V6HR5JRA3C2KETZBB7G"


def test_parse_info_feed(chapter_entity):
    _ = chapter_entity
    result = ChapterPluginWBC.parse_info_feed("example_manga")

    assert result == [
        {
            "id": "example_manga-01jcvm87vk3jfdwj3hmk08y6sp",
            "type": "wbc",
            "attributes": {
                "title": "Chapter 2",
                "url": "https://site.com/chapters/01JCVM87VK3JFDWJ3HMK08Y6SP",
                "chapter": "2",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
                "updatedAt": "2024-11-16T23:17:11.672863Z",
            },
        },
        {
            "id": "example_manga-01jbq5xgy6vgm1557epndzmv8j",
            "type": "wbc",
            "attributes": {
                "title": "Chapter 1.5",
                "url": "https://site.com/chapters/01JBQ5XGY6VGM1557EPNDZMV8J",
                "chapter": "1.5",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
                "updatedAt": "2024-11-02T19:34:00.903012Z",
            },
        },
        {
            "id": "example_manga-01jam51v6hr5jra3c2ketzbb7g",
            "type": "wbc",
            "attributes": {
                "title": "Chapter 1",
                "url": "https://site.com/chapters/01JAM51V6HR5JRA3C2KETZBB7G",
                "chapter": "1",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
                "updatedAt": "2024-10-20T05:05:28.784849Z",
            },
        },
    ]


def test_parse_chapter_download_links(chapter_entity):
    result = chapter_entity.parse_chapter_download_links("http://wbc.example.com/chapter")

    assert result == [
        "https://site.us/manga/example_manga/0001-001.png",
        "https://site.us/manga/example_manga/0001-002.png",
        "https://site.us/manga/example_manga/0001-003.png",
    ]
