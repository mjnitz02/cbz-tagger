import os
from io import BytesIO
from unittest.mock import patch

import pytest
from PIL import Image
from PIL import ImageFile
from PIL import UnidentifiedImageError

from cbz_tagger.entities.chapter_entity import ChapterEntity
from cbz_tagger.entities.plugins.plugin_entity import ChapterPluginEntity

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures")


@pytest.fixture
def damaged_page():
    """Real page served by MangaDex (Needless ch.15 p.15, captured 2026-11-15). Its bytes match the
    SHA-256 in MangaDex's filename, so the file is damaged at the source: the pixel data is 80 bytes
    short and both the PNG CRC and the zlib checksum are wrong."""
    with open(os.path.join(FIXTURES, "mdx_damaged_page.png"), "rb") as f:
        return f.read()


@pytest.fixture
def good_page():
    with open(os.path.join(FIXTURES, "page.jpg"), "rb") as f:
        return f.read()


def test_damaged_page_fails_a_strict_decode(damaged_page):
    # Guards the fixture: if Pillow ever decodes this strictly, the tolerant path is no longer exercised
    with pytest.raises(OSError, match="broken data stream"):
        Image.open(BytesIO(damaged_page)).load()


def test_decode_image_salvages_damaged_page(damaged_page, caplog):
    image = ChapterPluginEntity.decode_image(damaged_page, "chapter c1 page 15")

    assert image.size == (956, 1400)
    image.convert("RGB")  # must not raise, the download path converts PNGs
    assert "Damaged image for chapter c1 page 15" in caplog.text


def test_decode_image_restores_global_truncation_flag(damaged_page):
    ChapterPluginEntity.decode_image(damaged_page, "page")
    assert ImageFile.LOAD_TRUNCATED_IMAGES is False


def test_decode_image_good_page_takes_strict_path(good_page, caplog):
    image = ChapterPluginEntity.decode_image(good_page, "page")
    assert image.format == "JPEG"
    assert "Damaged image" not in caplog.text


def test_decode_image_still_rejects_non_images():
    with pytest.raises(UnidentifiedImageError):
        ChapterPluginEntity.decode_image(b"<html>502 Bad Gateway</html>", "page")


@patch("cbz_tagger.entities.chapter_entity.ChapterEntity.download_file")
@patch("cbz_tagger.entities.plugins.mdx.ChapterPluginMDX.parse_chapter_download_links")
def test_download_chapter_saves_every_page_when_one_is_damaged(
    mock_links, mock_download_file, damaged_page, good_page, tmp_path
):
    chapter = ChapterEntity({"id": "c1", "type": "chapter", "attributes": {"chapter": "15", "pages": 3}})
    mock_links.return_value = ["p1", "p2", "p3"]
    mock_download_file.side_effect = [good_page, damaged_page, good_page]

    saved = chapter.download_chapter(str(tmp_path))

    assert len(saved) == 3
    for path in saved:
        assert Image.open(path).format == "JPEG"
