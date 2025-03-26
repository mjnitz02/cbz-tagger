import os

import pytest
import requests_mock

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
def chapter_entity(wbc_series_response, wbc_chapter_response):
    with requests_mock.Mocker() as rm:
        rm.get(
            f"https://{Urls.WBC}/series/example_manga/full-chapter-list",
            text=wbc_series_response,
        )
        rm.get(
            "http://wbc.example.com/chapter",
            text=wbc_chapter_response,
        )

        yield ChapterEntity(
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
        chapter_entity.from_server_url({"ids[]": ["example_manga"]}, plugin_type=Plugins.CMK)


def test_from_server_url(chapter_entity):
    result = chapter_entity.from_server_url(
        {"ids[]": ["example_manga"]}, plugin_type=Plugins.WBC, plugin_id="example_manga"
    )

    assert len(result) == 5
    assert result[2].entity_id == "example_manga-01j76xz09ng81kb3c8x2v3p74y"
    assert result[2].get_chapter_url() == "https://site.com/chapters/01J76XZ09NG81KB3C8X2V3P74Y"
    assert result[3].entity_id == "example_manga-01j76xz09n6jydfdpwr4r85y03"
    assert result[3].get_chapter_url() == "https://site.com/chapters/01J76XZ09N6JYDFDPWR4R85Y03"
    assert result[4].entity_id == "example_manga-01j76xz09nhvbhpczrq0ytw7gs"
    assert result[4].get_chapter_url() == "https://site.com/chapters/01J76XZ09NHVBHPCZRQ0YTW7GS"


def test_parse_info_feed(chapter_entity):
    _ = chapter_entity
    result = ChapterPluginWBC.parse_info_feed("example_manga")

    assert result == [
        {
            "id": "example_manga-01j76xz09nwpn7pmb237qvjyp2",
            "type": "wbc",
            "attributes": {
                "title": "Chapter 3.1",
                "url": "https://site.com/chapters/01J76XZ09NWPN7PMB237QVJYP2",
                "chapter": "3.1",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
                "updatedAt": "2024-09-07T17:04:15.717343Z",
            },
        },
        {
            "id": "example_manga-01j76xz09ndfnrrgap5tb15jea",
            "type": "wbc",
            "attributes": {
                "title": "Chapter 3",
                "url": "https://site.com/chapters/01J76XZ09NDFNRRGAP5TB15JEA",
                "chapter": "3",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
                "updatedAt": "2024-09-07T17:04:15.717343Z",
            },
        },
        {
            "id": "example_manga-01j76xz09ng81kb3c8x2v3p74y",
            "type": "wbc",
            "attributes": {
                "title": "Chapter 2.5",
                "url": "https://site.com/chapters/01J76XZ09NG81KB3C8X2V3P74Y",
                "chapter": "2.5",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
                "updatedAt": "2024-09-07T17:04:15.717343Z",
            },
        },
        {
            "id": "example_manga-01j76xz09n6jydfdpwr4r85y03",
            "type": "wbc",
            "attributes": {
                "title": "Chapter 2",
                "url": "https://site.com/chapters/01J76XZ09N6JYDFDPWR4R85Y03",
                "chapter": "2",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
                "updatedAt": "2024-09-07T17:04:15.717343Z",
            },
        },
        {
            "id": "example_manga-01j76xz09nhvbhpczrq0ytw7gs",
            "type": "wbc",
            "attributes": {
                "title": "Chapter 1",
                "url": "https://site.com/chapters/01J76XZ09NHVBHPCZRQ0YTW7GS",
                "chapter": "1",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
                "updatedAt": "2024-09-07T17:04:15.717343Z",
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
