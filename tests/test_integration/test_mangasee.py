from ast import parse

from cbz_tagger.entities.mangasee import MangaSeeChapterEntity


def test_mangasee_rss():
    parser = MangaSeeChapterEntity()
    chapters = parser.parse_rss_feed("Tonikaku-Kawaii")
    chapter_urls = parser.parse_mangasee_chapter_pages(chapters["Chapter 290"])
    assert True
