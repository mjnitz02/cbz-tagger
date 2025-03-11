from time import sleep

import pytest

from cbz_tagger.common.enums import Plugins
from cbz_tagger.entities.chapter_entity import ChapterEntity


def check_entity_download_links(entity, entity_link_count):
    check_url = entity.get_chapter_url()
    download_links = entity.parse_chapter_download_links(check_url)
    assert len(download_links) == entity_link_count
    response = entity.request_with_retry(download_links[0])
    assert response.status_code == 200


# These are random selections of cancelled free web comics for testing the API connections
@pytest.mark.parametrize(
    "entity_id,plugin_type,plugin_id,entity_count,first_entity_count,second_entity_count",
    [
        ("11afa5c2-41dc-4cf3-8451-f306a3caf1ab", Plugins.MDX, "", 132, 7, 7),
        ("example_manga", Plugins.CMK, "itadaki", 5, 21, 20),
        # ("example_manga", Plugins.WBC, "01J76XY9B20J1KHJ1FWVZ8N1PK", 5, 21, 20),
        # Disabled because the plugin is not working in tests consistently
    ],
)
def test_chapter_plugins_api_connection_test(
    entity_id, plugin_type, plugin_id, entity_count, first_entity_count, second_entity_count
):
    """This is a smoke test to make sure that chapter plugins can connect to their respective APIs"""
    # Check that some entities can be retrieved and don't flake
    chapter_entities = ChapterEntity.from_server_url(
        {"ids[]": [entity_id]}, plugin_type=plugin_type, plugin_id=plugin_id
    )
    assert len(chapter_entities) == entity_count

    # Check the first entity has content
    check_entity_download_links(chapter_entities[0], first_entity_count)

    # Check the last entity has content
    check_entity_download_links(chapter_entities[-1], second_entity_count)
