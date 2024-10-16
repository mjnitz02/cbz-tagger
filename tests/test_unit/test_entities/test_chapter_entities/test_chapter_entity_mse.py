from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cbz_tagger.common.enums import Plugins
from cbz_tagger.entities.chapter_entity import ChapterEntity
from cbz_tagger.entities.chapter_plugins.mse import ChapterPluginMSE


@pytest.fixture
def chapter_entity():
    return ChapterEntity(
        {
            "id": "chapter_id",
            "attributes": {
                "chapter": "1",
                "translatedLanguage": "en",
                "pages": 2,
                "url": "http://example.com/chapter",
            },
            "relationships": [{"type": "scanlation_group", "id": "group_id"}],
            "type": Plugins.MSE,
        },
    )


def test_get_chapter_url(chapter_entity):
    result = chapter_entity.get_chapter_url()
    assert result == "http://example.com/chapter"


@patch("cbz_tagger.entities.chapter_plugins.mse.ChapterPluginMSE.request_with_retry")
def test_parse_info_feed(mock_request_with_retry):
    mock_response = MagicMock()
    mock_response.text = """
    <rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
    <channel>
    <atom:link href="https://url.com/rss/series-name.xml" rel="self" type="application/rss+xml"/>
    <title>Series Name</title>
    <link>https://url.com/manga/series-name</link>
    <lastBuildDate>Thu, 10 Oct 2024 18:45:45 +0000</lastBuildDate>
    <description>Series Name Chapters</description>
    <language>en-us</language>
    <category>entertainment</category>
    <image>
    <url>https://url.com/cover/series-name.jpg</url>
    <title>Series Name</title>
    <link>https://url.com/manga/series-name</link>
    </image>
    <item>
    <title>Series Name Chapter 2</title>
    <link>https://url.com/series-name-chapter-2-page-1.html</link>
    <pubDate>Tue, 08 Oct 2024 23:16:39 +0000</pubDate>
    <guid isPermaLink="false">Series-Name-2</guid>
    </item>
    <item>
    <title>Series Name Chapter 1.5</title>
    <link>https://url.com/series-name-chapter-1.5-page-1.html</link>
    <pubDate>Tue, 01 Oct 2024 22:09:02 +0000</pubDate>
    <guid isPermaLink="false">Series-Name-1.5</guid>
    </item>
    <item>
    <title>Series Name Chapter 1</title>
    <link>https://url.com/series-name-chapter-1-page-1.html</link>
    <pubDate>Tue, 01 Oct 2024 22:09:02 +0000</pubDate>
    <guid isPermaLink="false">Series-Name-1</guid>
    </item>
    </channel>
    </rss>
    """
    mock_request_with_retry.return_value = mock_response

    result = ChapterPluginMSE.parse_info_feed("example_manga")

    assert len(result) == 3
    assert result[0]["id"] == "example_manga-chapter-2"
    assert result[0]["type"] == Plugins.MSE
    assert result[0]["attributes"] == {
        "chapter": "2",
        "pages": -1,
        "title": "Chapter 2",
        "translatedLanguage": "en",
        "url": "https://url.com/series-name-chapter-2-page-1.html",
        "volume": -1,
    }
    assert result[1]["id"] == "example_manga-chapter-1.5"
    assert result[1]["type"] == Plugins.MSE
    assert result[1]["attributes"] == {
        "chapter": "1.5",
        "pages": -1,
        "title": "Chapter 1.5",
        "translatedLanguage": "en",
        "url": "https://url.com/series-name-chapter-1.5-page-1.html",
        "volume": -1,
    }
    assert result[2]["id"] == "example_manga-chapter-1"
    assert result[2]["type"] == Plugins.MSE
    assert result[2]["attributes"] == {
        "chapter": "1",
        "pages": -1,
        "title": "Chapter 1",
        "translatedLanguage": "en",
        "url": "https://url.com/series-name-chapter-1-page-1.html",
        "volume": -1,
    }


@patch("cbz_tagger.entities.chapter_plugins.mse.ChapterPluginMSE.parse_info_feed")
def test_from_server_url(mock_parse_info_feed):
    mock_parse_info_feed.return_value = [
        {
            "id": "example_manga-example-manga-chapter-1",
            "type": Plugins.MSE,
            "attributes": {
                "title": "Example Manga Chapter 1",
                "url": "http://example.com/chapter1",
                "chapter": "1",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
            },
        }
    ]

    result = ChapterEntity.from_server_url({"ids[]": ["example_manga"]}, plugin_type=Plugins.MSE)

    assert len(result) == 1
    assert result[0].entity_id == "example_manga-example-manga-chapter-1"
    assert result[0].get_chapter_url() == "http://example.com/chapter1"
    mock_parse_info_feed.assert_called_once_with("example_manga")


@patch("cbz_tagger.entities.chapter_plugins.mse.ChapterPluginMSE.request_with_retry")
def test_parse_chapter_download_links(mock_request_with_retry, chapter_entity):
    mock_response = MagicMock()
    mock_response.text = r"""
    vm.CurChapter = {"Chapter":"100010","Type":"Chapter","Page":"2","Directory":"","Date":"2024-10-08 23:16:39","ChapterName":null};
    vm.CurPathName = "scans.filelocation.us";
    vm.IndexName = "series_name";
    vm.SeriesName = "Some Name";
    """
    mock_request_with_retry.return_value = mock_response

    result = chapter_entity.parse_chapter_download_links("http://example.com/chapter")

    assert result == [
        "https://scans.filelocation.us/manga/series_name/0001-001.png",
        "https://scans.filelocation.us/manga/series_name/0001-002.png",
    ]
    mock_request_with_retry.assert_called_with("http://example.com/chapter")
