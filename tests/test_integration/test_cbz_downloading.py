import os
from unittest import mock


@mock.patch("cbz_tagger.database.entity_db.get_input")
@mock.patch("cbz_tagger.database.entity_db.get_raw_input")
@mock.patch("cbz_tagger.entities.chapter_entity.ChapterEntity.download_file")
def test_download_cbz_files_with_mark_all_tracked(
    mock_download_file, mock_get_raw_input, mock_get_input, integration_scanner, manga_name, capture_input_fixture
):
    """This test will add a new entry and mark it as fully downloaded. It will then attempt a refresh
    to verify that no files are downloaded or attempted to be downloaded during the refresh."""

    def capture_download_file(url, path):
        _ = url, path
        assert True

    mock_get_input.side_effect = capture_input_fixture(manga_name, mark_all_chapters=True)
    mock_get_raw_input.side_effect = capture_input_fixture(manga_name, mark_all_chapters=True)
    mock_download_file.side_effect = capture_download_file

    # Assert we can add a "tracked" entity to the database, and we're marking everything as completed
    integration_scanner.add_tracked_entity()
    assert len(integration_scanner.entity_database.entity_downloads) > 40  # API sometimes misfires
    assert integration_scanner.entity_database.entity_map == {
        "Touto Sugite Yome na a a a a a a i 4P Short Stories": "ab468776-27a5-456d-8f58-e058059531c9"
    }
    assert integration_scanner.entity_database.entity_tracked == {"ab468776-27a5-456d-8f58-e058059531c9"}
    assert integration_scanner.entity_database.get_missing_chapters() == []

    # Mock download chapter to check it isn't doing anything
    integration_scanner.entity_database.download_chapter = mock.MagicMock()

    # Refresh the database to run all downloads, nothing should be downloaded
    integration_scanner.refresh()
    integration_scanner.entity_database.download_chapter.assert_not_called()
    assert len(os.listdir(os.path.join(integration_scanner.config_path, "images"))) == 2
    assert len(os.listdir(integration_scanner.scan_path)) == 0


@mock.patch("cbz_tagger.database.entity_db.get_input")
@mock.patch("cbz_tagger.database.entity_db.get_raw_input")
@mock.patch("cbz_tagger.entities.chapter_entity.ChapterEntity.download_file")
def test_download_cbz_files_without_mark_all_tracked(
    mock_download_file, mock_get_raw_input, mock_get_input, integration_scanner, manga_name, capture_input_fixture
):
    """This test will add a new entry and mark it as not downloaded. It will then attempt a refresh
    to verify that each chapter is acquired, cleaned, and processed into the correct filename. The
    actual retrieval of any real files is mocked, so no files are actually downloaded."""

    def capture_download_file(url, path):
        _ = url, path
        assert True

    mock_get_input.side_effect = capture_input_fixture(manga_name)
    mock_get_raw_input.side_effect = capture_input_fixture(manga_name)
    mock_download_file.side_effect = capture_download_file

    # Assert we can add a "tracked" entity to the database, and we're marking everything as completed
    integration_scanner.add_tracked_entity()
    assert len(integration_scanner.entity_database.entity_downloads) == 0
    assert integration_scanner.entity_database.entity_map == {
        "Touto Sugite Yome na a a a a a a i 4P Short Stories": "ab468776-27a5-456d-8f58-e058059531c9"
    }
    assert integration_scanner.entity_database.entity_tracked == {"ab468776-27a5-456d-8f58-e058059531c9"}
    missing_chapters = len(integration_scanner.entity_database.get_missing_chapters())
    assert missing_chapters > 40  # API sometimes misfires

    # Mock download chapter so we don't actually download files
    integration_scanner.entity_database.chapters.download = mock.MagicMock()

    # Refresh the database to run all downloads, nothing should be downloaded since the actual request
    # to the server is mocked above. We will run everything else though against real APIs.
    integration_scanner.refresh()
    assert len(os.listdir(os.path.join(integration_scanner.config_path, "images"))) == 2
    assert len(os.listdir(integration_scanner.scan_path)) == 0
    assert len(integration_scanner.entity_database.entity_downloads) == missing_chapters
    assert len(integration_scanner.entity_database.get_missing_chapters()) == 0
    storage_results = [
        os.path.relpath(str(os.path.join(root, name)), integration_scanner.storage_path)
        for root, dirs, files in os.walk(integration_scanner.storage_path)
        for name in files
    ]
    assert len(storage_results) == missing_chapters

    # Test tracking removal
    integration_scanner.remove_tracked_entity()
    assert integration_scanner.entity_database.entity_tracked == set()
    assert integration_scanner.entity_database.entity_downloads == set()

    # Test full deletion
    assert len(integration_scanner.entity_database.authors) >= 1
    assert len(integration_scanner.entity_database.chapters) >= 1
    assert len(integration_scanner.entity_database.covers) >= 1
    assert len(integration_scanner.entity_database.metadata) >= 1
    assert len(integration_scanner.entity_database.volumes) >= 1
    integration_scanner.delete_entity()
    assert len(integration_scanner.entity_database.authors) >= 1
    assert len(integration_scanner.entity_database.chapters) == 0
    assert len(integration_scanner.entity_database.covers) == 0
    assert len(integration_scanner.entity_database.metadata) == 0
    assert len(integration_scanner.entity_database.volumes) == 0
