import pytest
import requests_mock  # pylint: disable=unused-import

from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.enums import Urls
from cbz_tagger.entities.chapter_entity import ChapterEntity
from cbz_tagger.entities.chapter_plugins.mse import ChapterPluginMSE


@pytest.fixture
def chapter_entity(requests_mock):
    requests_mock.get(
        f"https://{Urls.MSE}/rss/example_manga.xml",
        text="""<rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
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
    """,
    )
    requests_mock.get(
        "http://mse.example.com/chapter",
        text="""vm.CurChapter = {"Chapter":"100010","Type":"Chapter","Page":"2","Directory":"","Date":"2024-10-08 23:16:39","ChapterName":null};
        vm.CurPathName = "scans.filelocation.us";
        vm.IndexName = "series_name";
        vm.SeriesName = "Some Name";
    """,
    )

    return ChapterEntity(
        {
            "id": "chapter_id",
            "attributes": {
                "chapter": "1",
                "translatedLanguage": "en",
                "pages": 2,
                "url": "http://mse.example.com/chapter",
            },
            "relationships": [{"type": "scanlation_group", "id": "group_id"}],
            "type": Plugins.MSE,
        },
    )


def test_get_chapter_url(chapter_entity):
    result = chapter_entity.get_chapter_url()
    assert result == "http://mse.example.com/chapter"


def test_from_server_url_no_plugin_id(chapter_entity):
    with pytest.raises(EnvironmentError, match="plugin_id not provided"):
        chapter_entity.from_server_url({"ids[]": ["example_manga"]}, plugin_type=Plugins.MSE)


def test_from_server_url(chapter_entity):
    result = chapter_entity.from_server_url(
        {"ids[]": ["example_manga"]}, plugin_type=Plugins.MSE, plugin_id="example_manga"
    )

    assert len(result) == 3
    assert result[0].entity_id == "example_manga-chapter-2"
    assert result[0].get_chapter_url() == "https://url.com/series-name-chapter-2-page-1.html"
    assert result[1].entity_id == "example_manga-chapter-1.5"
    assert result[1].get_chapter_url() == "https://url.com/series-name-chapter-1.5-page-1.html"
    assert result[2].entity_id == "example_manga-chapter-1"
    assert result[2].get_chapter_url() == "https://url.com/series-name-chapter-1-page-1.html"


def test_parse_info_feed(chapter_entity):
    _ = chapter_entity
    result = ChapterPluginMSE.parse_info_feed("example_manga")

    assert result == [
        {
            "id": "example_manga-chapter-2",
            "type": "mse",
            "attributes": {
                "title": "Chapter 2",
                "updatedAt": "Tue, 08 Oct 2024 23:16:39 +0000",
                "url": "https://url.com/series-name-chapter-2-page-1.html",
                "chapter": "2",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
            },
        },
        {
            "id": "example_manga-chapter-1.5",
            "type": "mse",
            "attributes": {
                "title": "Chapter 1.5",
                "updatedAt": "Tue, 01 Oct 2024 22:09:02 +0000",
                "url": "https://url.com/series-name-chapter-1.5-page-1.html",
                "chapter": "1.5",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
            },
        },
        {
            "id": "example_manga-chapter-1",
            "type": "mse",
            "attributes": {
                "title": "Chapter 1",
                "updatedAt": "Tue, 01 Oct 2024 22:09:02 +0000",
                "url": "https://url.com/series-name-chapter-1-page-1.html",
                "chapter": "1",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": -1,
            },
        },
    ]


def test_parse_chapter_download_links(chapter_entity):
    result = chapter_entity.parse_chapter_download_links("http://mse.example.com/chapter")

    assert result == [
        "https://scans.filelocation.us/manga/series_name/0001-001.png",
        "https://scans.filelocation.us/manga/series_name/0001-002.png",
    ]
