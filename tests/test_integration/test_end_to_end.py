from unittest import mock

import pytest

from cbz_tagger.common.enums import Plugins
from cbz_tagger.entities.chapter_entity import ChapterEntity
from cbz_tagger.entities.cover_entity import CoverEntity
from cbz_tagger.entities.metadata_entity import MetadataEntity
from cbz_tagger.entities.volume_entity import VolumeEntity


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


@pytest.mark.skip("Debugging only")
@pytest.mark.parametrize(
    "entity_id,plugin_type,plugin_id",
    [("", Plugins.WBC, "")],
)
def test_entity_retrievals(
    entity_id,
    plugin_type,
    plugin_id,
):
    if entity_id is None:
        return

    """This is a smoke test to make sure that chapter plugins can connect to their respective APIs"""
    # Check that some entities can be retrieved and don't flake
    metadata_entity = MetadataEntity.from_server_url(query_params={"ids[]": [entity_id]})[0]
    assert metadata_entity
    volume_entity = VolumeEntity.from_server_url(query_params={"ids[]": [entity_id]})[0]
    assert volume_entity
    cover_entities = CoverEntity.from_server_url(query_params={"manga[]": [entity_id]})
    assert cover_entities
    chapter_entities = ChapterEntity.from_server_url(
        {"ids[]": [entity_id]}, plugin_type=plugin_type, plugin_id=plugin_id
    )
    assert chapter_entities
