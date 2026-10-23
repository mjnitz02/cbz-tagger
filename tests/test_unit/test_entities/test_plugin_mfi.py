import json
import os
from unittest.mock import patch

import pytest

from cbz_tagger.entities.chapter_entity import ChapterEntity
from cbz_tagger.entities.plugins.mfi import ChapterPluginMFI

CHAPTERS_URL = f"{ChapterPluginMFI.api_url}/titles/1n9qw/chapters"
CHAPTER_URL = f"{ChapterPluginMFI.api_url}/chapters/7683844"


@pytest.fixture
def mfi_fixture(tests_fixtures_path):
    def load(name):
        with open(os.path.join(tests_fixtures_path, name), encoding="utf-8") as file:
            return json.load(file)

    return load


@pytest.fixture
def chapter_entity(requests_mock, mfi_fixture):
    requests_mock.get(f"{CHAPTERS_URL}?page=1", json=mfi_fixture("mfi_chapters_page_1.json"))
    requests_mock.get(f"{CHAPTERS_URL}?page=2", json=mfi_fixture("mfi_chapters_page_2.json"))
    requests_mock.get(CHAPTER_URL, json=mfi_fixture("mfi_chapter.json"))

    return ChapterEntity(
        {
            "id": "1n9qw-7683844",
            "attributes": {
                "chapter": "108",
                "translatedLanguage": "en",
                "pages": -1,
                "url": CHAPTER_URL,
            },
            "relationships": [{"type": "scanlation_group", "id": "official"}],
            "type": ChapterPluginMFI.PLUGIN_TYPE,
        },
    )


@pytest.mark.parametrize(
    "path,params,expected",
    [
        # Each signature was accepted by the live API on 2026-10-23 (unsigned requests return 403)
        ("/titles/1n9qw", None, "8sK3xtqdFdtXclMFgA"),
        ("/chapters/7683844", None, "8vPRXa1JjvVTxulRJOMAEU0"),
        (
            "/titles/1n9qw/chapters",
            {"sort": "number", "order": "desc", "page": 1, "limit": 200},
            "8sK3xtqdFdtXclMFgJlLgbpRBHlveVSokd5o8J1Hi73prAnxRwrlqO9rmrr6fITg7zfZhv0BnsCyF_fWr_g",
        ),
        # The server signs decoded values: URL-encoding the space ("+" or "%20") before signing gets a 403
        (
            "/titles",
            {"keyword": "yo kai sangokushi", "page": 1, "limit": 10},
            "8sK3xtqdFZfetBhus6bRAiKdv3daBrk4MMoiitqew19skwF2kWrjNa0D3yUnA33Opg",
        ),
    ],
)
def test_compute_vrf(path, params, expected):
    assert ChapterPluginMFI.compute_vrf(path, params) == expected


def test_compute_vrf_ignores_param_order():
    params = {"sort": "number", "order": "desc", "page": 1, "limit": 200}
    reordered = dict(reversed(list(params.items())))
    assert ChapterPluginMFI.compute_vrf("/x", params) == ChapterPluginMFI.compute_vrf("/x", reordered)


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_parse_info_feed(mock_sleep, mock_random, requests_mock, chapter_entity):
    _ = chapter_entity
    result = ChapterPluginMFI.parse_info_feed("1n9qw")

    # Paginates until hasNext is false, and every request is signed
    chapter_requests = [r for r in requests_mock.request_history if r.path.endswith("/chapters")]
    assert [r.qs["page"] for r in chapter_requests] == [["1"], ["2"]]
    assert all("vrf" in r.qs for r in requests_mock.request_history)

    # Non-English releases are dropped; official and unofficial releases of the same number are both kept
    assert [(c["id"], c["attributes"]["chapter"], c["relationships"][0]["id"]) for c in result] == [
        ("1n9qw-7683844", "108", "official"),
        ("1n9qw-3806990", "108", "unofficial"),
        ("1n9qw-7683843", "107", "official"),
        ("1n9qw-2451117", "107", "unofficial"),
        ("1n9qw-5434355", "105.6", "unofficial"),
    ]
    assert result[0] == {
        "id": "1n9qw-7683844",
        "type": ChapterPluginMFI.PLUGIN_TYPE,
        "attributes": {
            "title": "Chapter 108: Example Chapter Name",
            "url": CHAPTER_URL,
            "chapter": "108",
            "translatedLanguage": "en",
            "pages": -1,
            "volume": None,
            "createdAt": "2026-07-06T02:32:25+00:00",
            "updatedAt": "2026-07-06T02:32:25+00:00",
        },
        "relationships": [{"type": "scanlation_group", "id": "official"}],
    }
    assert result[1]["attributes"]["title"] == "Chapter 108"


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_parse_info_feed_accepts_slugged_id(mock_sleep, mock_random, chapter_entity):
    _ = chapter_entity
    result = ChapterPluginMFI.parse_info_feed("1n9qw-manga-name")
    assert result[0]["id"] == "1n9qw-7683844"


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_from_server_url(mock_sleep, mock_random, chapter_entity):
    result = chapter_entity.from_server_url(
        {"ids[]": ["example_manga"]}, plugin_type=ChapterPluginMFI.PLUGIN_TYPE, plugin_id="1n9qw"
    )
    assert len(result) == 5
    assert result[0].chapter_number == 108.0
    assert result[4].chapter_number == 105.6
    assert result[0].scanlation_group == "official"
    assert result[0].get_chapter_url() == CHAPTER_URL


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_parse_chapter_download_links(mock_sleep, mock_random, requests_mock, chapter_entity):
    result = chapter_entity.parse_chapter_download_links(CHAPTER_URL)

    assert requests_mock.last_request.qs["vrf"] == [ChapterPluginMFI.compute_vrf("/chapters/7683844").lower()]
    assert len(result) == 3
    assert all(url.startswith("https://") and url.endswith(".jpg") for url in result)


@patch("cbz_tagger.entities.plugins.plugin_entity.Image.open")
@patch("cbz_tagger.entities.plugins.plugin_entity.os.path.exists", return_value=False)
@patch("cbz_tagger.entities.chapter_entity.ChapterEntity.download_file", return_value=b"image data")
@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_download_chapter_sends_referer(
    mock_sleep, mock_random, mock_download_file, mock_path_exists, mock_image_open, chapter_entity
):
    mock_image_open.return_value.format = "JPEG"
    # Goes through the ChapterEntity wrapper, like the real download flow, so the plugin's headers must carry over
    chapter_entity.download_chapter("/tmp/chapter")

    assert mock_download_file.call_count == 3
    for call in mock_download_file.call_args_list:
        assert call.kwargs["headers"] == {"Referer": f"https://{ChapterPluginMFI.BASE_URL}/"}
