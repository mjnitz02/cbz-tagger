from cbz_tagger.entities.chapter_plugins.mangasee import ChapterEntityMangaSee


def test_mangasee_rss(integration_scanner):
    query_params = {"ids[]": ["Tonikaku-Kawaii"]}
    chapters = ChapterEntityMangaSee.from_server_url(query_params)
    # for chapter in chapters:
    #     chapter.download_chapter(integration_scanner.storage_path)
    assert chapters
