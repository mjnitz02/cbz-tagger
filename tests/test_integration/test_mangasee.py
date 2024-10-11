from cbz_tagger.entities.chapter_entity import MangaSeeChapterEntity


def test_mangasee_rss(integration_scanner):
    query_params = {"ids[]": ["Tonikaku-Kawaii"]}
    chapters = MangaSeeChapterEntity.from_server_url(query_params)
    for chapter in chapters:
        chapter.download_chapter(integration_scanner.storage_path)
    assert chapters
