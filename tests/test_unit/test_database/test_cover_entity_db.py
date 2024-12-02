import os
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PIL.Image import Image

from cbz_tagger.database.cover_entity_db import CoverEntityDB
from cbz_tagger.entities.cover_entity import CoverEntity


@pytest.fixture
def cover_entity_db():
    test_db = CoverEntityDB()
    test_db.database = {
        "entity1": [MagicMock(local_filename="cover1.jpg"), MagicMock(local_filename="cover2.jpg")],
        "entity2": [MagicMock(local_filename="cover3.jpg")],
    }
    return test_db


def test_get_indexed_covers(cover_entity_db):
    covers = cover_entity_db.get_indexed_covers()
    expected_covers = [("entity1", "cover1.jpg"), ("entity1", "cover2.jpg"), ("entity2", "cover3.jpg")]
    assert covers == expected_covers


@patch("os.listdir")
def test_get_local_covers(mock_listdir):
    mock_listdir.return_value = ["cover1.jpg", "cover2.jpg", "cover3.jpg"]
    local_covers = CoverEntityDB.get_local_covers("mock_path")
    assert local_covers == ["cover1.jpg", "cover2.jpg", "cover3.jpg"]


def test_get_orphaned_covers(cover_entity_db):
    with patch(
        "cbz_tagger.database.cover_entity_db.CoverEntityDB.get_local_covers",
        return_value=["cover1.jpg", "cover3.jpg", "cover4.jpg"],
    ):
        orphaned_covers = cover_entity_db.get_orphaned_covers("mock_path")
        assert orphaned_covers == ["cover4.jpg"]


@patch("os.remove")
def test_remove_orphaned_covers(mock_remove, cover_entity_db):
    with patch("cbz_tagger.database.cover_entity_db.CoverEntityDB.get_orphaned_covers", return_value=["cover4.jpg"]):
        cover_entity_db.remove_orphaned_covers("mock_path")
        mock_remove.assert_called_once_with(os.path.join("mock_path", "cover4.jpg"))


def test_get_missing_covers(cover_entity_db):
    with patch("cbz_tagger.database.cover_entity_db.CoverEntityDB.get_local_covers", return_value=["cover1.jpg"]):
        missing_covers = cover_entity_db.get_missing_covers("mock_path")
        assert missing_covers == {"entity1", "entity2"}


@patch("cbz_tagger.database.cover_entity_db.CoverEntityDB.download")
def test_download_missing_covers(mock_download, cover_entity_db):
    with patch("cbz_tagger.database.cover_entity_db.CoverEntityDB.get_missing_covers", return_value={"entity1"}):
        cover_entity_db.download_missing_covers("mock_path")
        mock_download.assert_called_once_with("entity1", "mock_path")


@pytest.mark.parametrize(
    "content, expected_locale",
    [
        ([MagicMock(attributes={"locale": "ja"})], "ja"),
        ([MagicMock(attributes={"locale": "en"})], "en"),
        ([MagicMock(attributes={"locale": "ko"})], "ko"),
        ([MagicMock(attributes={"locale": "zh"})], "zh"),
        ([MagicMock(attributes={"locale": "fr"})], "fr"),
    ],
)
def test_format_content_for_entity(content, expected_locale):
    test_db = CoverEntityDB()
    result = test_db.format_content_for_entity(content)
    assert len(result) == 1
    assert result[0].attributes["locale"] == expected_locale


@patch("cbz_tagger.database.cover_entity_db.os.makedirs")
@patch("cbz_tagger.database.cover_entity_db.path.exists")
@patch("cbz_tagger.database.cover_entity_db.Image.open")
@patch("cbz_tagger.database.cover_entity_db.BytesIO")
def test_download(mock_bytes_io, mock_image_open, mock_path_exists, mock_os_makedirs):
    mock_cover = MagicMock(spec=CoverEntity)
    mock_cover.local_filename = "cover1.jpg"
    mock_cover.cover_url = "http://example.com/cover1.jpg"
    mock_cover.download_file.return_value = b"image_data"

    mock_image = MagicMock(spec=Image)
    mock_image.format = "JPEG"
    mock_image_open.return_value = mock_image

    test_db = CoverEntityDB()
    test_db.database = {"entity1": [mock_cover]}

    mock_path_exists.side_effect = lambda x: x != "mock_path/cover1.jpg"

    test_db.download("entity1", "mock_path")

    mock_os_makedirs.assert_called_once_with("mock_path", exist_ok=True)
    mock_cover.download_file.assert_called_once_with("http://example.com/cover1.jpg")
    mock_bytes_io.assert_called_once_with(b"image_data")
    mock_image_open.assert_called_once_with(mock_bytes_io())
    mock_image.save.assert_called_once_with("mock_path/cover1.jpg", quality=95, optimize=True)
