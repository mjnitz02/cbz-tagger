import json

from unittest.mock import patch

import pytest

from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.enums import Urls
from cbz_tagger.entities.chapter_entity import ChapterEntity
from cbz_tagger.entities.chapter_plugins.cmk import ChapterPluginCMK


@pytest.fixture
def chapter_entity(requests_mock):
    requests_mock.get(
        f"https://{Urls.CMK}/comic/example_manga",
        text=json.dumps(
            {
                "comic": {
                    "hid": "ACprvUWn",
                },
            }
        ),
    )
    requests_mock.get(
        f"https://{Urls.CMK}/comic/ACprvUWn/chapters?lang=en&page=1",
        text=json.dumps(
            {
                "chapters": [
                    {
                        "id": 3562092,
                        "chap": "2",
                        "title": "Chapter 2",
                        "vol": None,
                        "lang": "en",
                        "group_name": None,
                        "hid": "Ce82S7St",
                        "created_at": "2024-10-15T20:55:38+02:00",
                        "updated_at": "2024-10-22T11:05:35+02:00",
                    },
                    {
                        "id": 2562092,
                        "chap": "1.5",
                        "title": "Chapter 1.5",
                        "vol": None,
                        "lang": "en",
                        "group_name": [],
                        "hid": "Be82S7St",
                        "created_at": "2024-10-14T20:55:38+02:00",
                        "updated_at": "2024-10-21T11:05:35+02:00",
                    },
                    {
                        "id": 1562092,
                        "chap": "1",
                        "title": "Chapter 1",
                        "vol": None,
                        "lang": "en",
                        "group_name": ["Official"],
                        "hid": "Ae82S7St",
                        "created_at": "2024-10-13T20:55:38+02:00",
                        "updated_at": "2024-10-20T11:05:35+02:00",
                    },
                ],
                "total": 3,
                "limit": 50,
            }
        ),
    )
    requests_mock.get(
        "http://cmk.example.com/chapter",
        text=json.dumps(
            {
                "chapter": {
                    "hid": "A7OdAIOC",
                    "images": [
                        {"url": "https://scans.filelocation.pictures/0-Axe_rj3bWy3Dt.jpg", "w": 1081, "h": 1538},
                        {"url": "https://scans.filelocation.pictures/1-ANdtdpkSY9VXV.jpg", "w": 1080, "h": 1538},
                        {"url": "https://scans.filelocation.pictures/2-AXHawoARnAdAQ.jpg", "w": 2160, "h": 1538},
                        {"url": "https://scans.filelocation.pictures/3-AWqMYpy8Nkxsp.jpg", "w": 1080, "h": 1538},
                    ],
                },
            }
        ),
    )

    return ChapterEntity(
        {
            "id": "chapter_id",
            "attributes": {
                "chapter": "1",
                "translatedLanguage": "en",
                "pages": 2,
                "url": "http://cmk.example.com/chapter",
            },
            "relationships": [{"type": "scanlation_group", "id": "group_id"}],
            "type": Plugins.CMK,
        },
    )


def test_get_chapter_url(chapter_entity):
    result = chapter_entity.get_chapter_url()
    assert result == "http://cmk.example.com/chapter"


def test_from_server_url_no_plugin_id(chapter_entity):
    with pytest.raises(EnvironmentError, match="plugin_id not provided"):
        chapter_entity.from_server_url({"ids[]": ["example_manga"]}, plugin_type=Plugins.CMK)


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_from_server_url(mock_sleep, mock_random, chapter_entity):
    result = chapter_entity.from_server_url(
        {"ids[]": ["example_manga"]}, plugin_type=Plugins.CMK, plugin_id="example_manga"
    )

    assert len(result) == 3
    assert result[0].entity_id == "ACprvUWn-Ce82S7St"
    assert result[0].get_chapter_url() == f"https://{Urls.CMK}/chapter/Ce82S7St?tachiyomi=true"
    assert result[1].entity_id == "ACprvUWn-Be82S7St"
    assert result[1].get_chapter_url() == f"https://{Urls.CMK}/chapter/Be82S7St?tachiyomi=true"
    assert result[2].entity_id == "ACprvUWn-Ae82S7St"
    assert result[2].get_chapter_url() == f"https://{Urls.CMK}/chapter/Ae82S7St?tachiyomi=true"


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_parse_info_feed(mock_sleep, mock_random, chapter_entity):
    _ = chapter_entity
    result = ChapterPluginCMK.parse_info_feed("example_manga")

    assert result == [
        {
            "id": "ACprvUWn-Ce82S7St",
            "type": "cmk",
            "attributes": {
                "title": "Chapter 2",
                "url": f"https://{Urls.CMK}/chapter/Ce82S7St?tachiyomi=true",
                "chapter": "2",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": None,
                "createdAt": "2024-10-15T20:55:38+02:00",
                "updatedAt": "2024-10-15T20:55:38+02:00",
            },
            "relationships": [{"type": "scanlation_group", "id": None}],
        },
        {
            "id": "ACprvUWn-Be82S7St",
            "type": "cmk",
            "attributes": {
                "title": "Chapter 1.5",
                "url": f"https://{Urls.CMK}/chapter/Be82S7St?tachiyomi=true",
                "chapter": "1.5",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": None,
                "createdAt": "2024-10-14T20:55:38+02:00",
                "updatedAt": "2024-10-14T20:55:38+02:00",
            },
            "relationships": [{"type": "scanlation_group", "id": None}],
        },
        {
            "id": "ACprvUWn-Ae82S7St",
            "type": "cmk",
            "attributes": {
                "title": "Chapter 1",
                "url": f"https://{Urls.CMK}/chapter/Ae82S7St?tachiyomi=true",
                "chapter": "1",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": None,
                "createdAt": "2024-10-13T20:55:38+02:00",
                "updatedAt": "2024-10-13T20:55:38+02:00",
            },
            "relationships": [{"type": "scanlation_group", "id": "Official"}],
        },
    ]


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_parse_chapter_download_links(mock_sleep, mock_random, chapter_entity):
    result = chapter_entity.parse_chapter_download_links("http://cmk.example.com/chapter")

    assert result == [
        "https://scans.filelocation.pictures/0-Axe_rj3bWy3Dt.jpg",
        "https://scans.filelocation.pictures/1-ANdtdpkSY9VXV.jpg",
        "https://scans.filelocation.pictures/2-AXHawoARnAdAQ.jpg",
        "https://scans.filelocation.pictures/3-AWqMYpy8Nkxsp.jpg",
    ]
