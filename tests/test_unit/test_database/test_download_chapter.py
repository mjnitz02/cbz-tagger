import os
import shutil
from unittest import mock

import pytest

from cbz_tagger.entities.chapter_plugins.plugin_mdx import ChapterEntityMDX


@pytest.fixture
def storage_path():
    base_path = os.path.dirname(os.path.realpath(__file__))
    try:
        yield os.path.join(base_path, "storage")
    finally:
        shutil.rmtree(os.path.join(base_path, "storage"), ignore_errors=True)


@pytest.fixture
def mock_entity_db_downloader(mock_entity_db):
    mock_entity_db.build_chapter_metadata = mock.MagicMock()
    mock_entity_db.chapters.download = mock.MagicMock()
    mock_entity_db.build_chapter_cbz = mock.MagicMock()
    mock_entity_db.entity_downloads = mock.MagicMock()
    mock_entity_db.save = mock.MagicMock()

    yield mock_entity_db


def test_download_chapter_fails_with_page_download_failure(
    mock_entity_db_downloader, manga_request_id, chapter_request_response, storage_path
):
    chapter_item = [ChapterEntityMDX(data) for data in chapter_request_response["data"]][0]
    mock_entity_db_downloader.chapters.download = mock.MagicMock(side_effect=EnvironmentError)
    mock_entity_db_downloader.download_chapter(manga_request_id, chapter_item, storage_path)

    mock_entity_db_downloader.build_chapter_metadata.assert_called_once()
    mock_entity_db_downloader.chapters.download.assert_called_once()
    mock_entity_db_downloader.build_chapter_cbz.assert_not_called()
    mock_entity_db_downloader.entity_downloads.add.assert_not_called()
    mock_entity_db_downloader.entity_downloads.save.assert_not_called()

    manga_name = next(iter(name for name, id in mock_entity_db_downloader.entity_map.items() if id == manga_request_id))
    chapter_name = f"{manga_name} - Chapter {chapter_item.padded_chapter_string}"
    assert not os.path.exists(os.path.join(storage_path, manga_name, chapter_name))


def test_download_chapter_fails_with_missing_cbz_file_failure(
    mock_entity_db_downloader, manga_request_id, chapter_request_response, storage_path
):
    chapter_item = [ChapterEntityMDX(data) for data in chapter_request_response["data"]][0]
    mock_entity_db_downloader.build_chapter_cbz = mock.MagicMock(side_effect=EnvironmentError)
    mock_entity_db_downloader.download_chapter(manga_request_id, chapter_item, storage_path)

    mock_entity_db_downloader.build_chapter_metadata.assert_called_once()
    mock_entity_db_downloader.chapters.download.assert_called_once()
    mock_entity_db_downloader.build_chapter_cbz.assert_called_once()
    mock_entity_db_downloader.entity_downloads.add.assert_not_called()
    mock_entity_db_downloader.entity_downloads.save.assert_not_called()

    manga_name = next(iter(name for name, id in mock_entity_db_downloader.entity_map.items() if id == manga_request_id))
    chapter_name = f"{manga_name} - Chapter {chapter_item.padded_chapter_string}"
    assert not os.path.exists(os.path.join(storage_path, manga_name, chapter_name))
