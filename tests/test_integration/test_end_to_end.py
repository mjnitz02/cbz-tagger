from unittest import mock

import pytest


@pytest.fixture
def end_to_end_manga_name():
    return None


@pytest.fixture
def end_to_end_chapter_name():
    return None


def test_end_to_end_disabled_on_commits(end_to_end_manga_name):
    assert end_to_end_manga_name is None


@pytest.mark.skip("Debugging only")
@mock.patch("cbz_tagger.common.input.get_input")
@mock.patch("cbz_tagger.common.input.get_raw_input")
def test_end_to_end_mdx(
    mock_get_raw_input, mock_get_input, integration_scanner, end_to_end_manga_name, capture_input_fixture
):
    """This test is designed for triggering a live test in a local environment"""
    if end_to_end_manga_name is None:
        return

    mock_get_input.side_effect = capture_input_fixture(end_to_end_manga_name, backend=1)
    mock_get_raw_input.side_effect = capture_input_fixture(end_to_end_manga_name, backend=1)

    # Assert we can add a "tracked" entity to the database, and we're marking everything as completed
    integration_scanner.add_tracked_entity()

    # Refresh the database to run all downloads, nothing should be downloaded since the actual request
    # to the server is mocked above. We will run everything else though against real APIs.
    integration_scanner.refresh()
    assert True


@pytest.mark.skip("Debugging only")
@mock.patch("cbz_tagger.common.input.get_input")
@mock.patch("cbz_tagger.common.input.get_raw_input")
def test_end_to_end_live_cmk(
    mock_get_raw_input,
    mock_get_input,
    capture_input_fixture,
    integration_scanner,
    end_to_end_manga_name,
    end_to_end_chapter_name,
):
    """This test is designed for triggering a live test in a local environment"""
    if end_to_end_manga_name is None:
        return

    mock_get_input.side_effect = capture_input_fixture(
        end_to_end_manga_name, backend=3, backend_id=end_to_end_chapter_name
    )
    mock_get_raw_input.side_effect = capture_input_fixture(
        end_to_end_manga_name, backend=3, backend_id=end_to_end_chapter_name
    )

    integration_scanner.add_tracked_entity()
    integration_scanner.refresh()
    assert True


@pytest.mark.skip("Debugging only")
@mock.patch("cbz_tagger.common.input.get_input")
@mock.patch("cbz_tagger.common.input.get_raw_input")
def test_end_to_end_live_wbc(
    mock_get_raw_input,
    mock_get_input,
    capture_input_fixture,
    integration_scanner,
    end_to_end_manga_name,
    end_to_end_chapter_name,
):
    """This test is designed for triggering a live test in a local environment"""
    if end_to_end_manga_name is None:
        return

    mock_get_input.side_effect = capture_input_fixture(
        end_to_end_manga_name, backend=4, backend_id=end_to_end_chapter_name
    )
    mock_get_raw_input.side_effect = capture_input_fixture(
        end_to_end_manga_name, backend=4, backend_id=end_to_end_chapter_name
    )

    integration_scanner.add_tracked_entity()
    integration_scanner.refresh()
    assert True
