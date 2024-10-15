from unittest import mock

import pytest

from cbz_tagger.entities.chapter_plugins import plugins


@pytest.fixture
def end_to_end_manga_name():
    return None


def test_end_to_end_disabled_on_commits(end_to_end_manga_name):
    assert end_to_end_manga_name is None


@mock.patch("cbz_tagger.database.entity_db.get_input")
@mock.patch("cbz_tagger.database.entity_db.get_raw_input")
def test_end_to_end_live(
    mock_get_raw_input, mock_get_input, integration_scanner, end_to_end_manga_name, capture_input_fixture
):
    """This test is designed for triggering a live test in a local environment"""
    if end_to_end_manga_name is None:
        return

    mock_get_input.side_effect = capture_input_fixture(end_to_end_manga_name)
    mock_get_raw_input.side_effect = capture_input_fixture(end_to_end_manga_name)

    # Assert we can add a "tracked" entity to the database, and we're marking everything as completed
    integration_scanner.add_tracked_entity()

    # Refresh the database to run all downloads, nothing should be downloaded since the actual request
    # to the server is mocked above. We will run everything else though against real APIs.
    integration_scanner.refresh()


def test_end_to_end_live_rss(integration_scanner, end_to_end_manga_name):
    """This test is designed for triggering a live test in a local environment"""
    if end_to_end_manga_name is None:
        return

    query_params = {"ids[]": [end_to_end_manga_name]}
    chapters = plugins["mse"].from_server_url(query_params)
    for idx, chapter in enumerate(chapters):
        if idx > 0:
            break
        chapter.download_chapter(integration_scanner.storage_path)
    assert chapters
