from unittest import mock

import pytest

from cbz_tagger.database.entities.base_entity import BaseEntity
from cbz_tagger.database.entities.volume_entity import VolumeEntity


def test_volume_entity(volume_request_response):
    entity = VolumeEntity(content=volume_request_response)

    # Volume entities are very simple and have little metadata
    assert entity.entity_id is None
    assert entity.entity_type is None
    assert entity.attributes == {}
    assert entity.relationships == {}

    assert entity.chapter_count == 21
    assert sorted(entity.chapters) == [
        "1",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "2",
        "20",
        "21",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
    ]
    assert entity.volumes == {
        "none": ["none"],
        "4": ["21", "20", "16", "13"],
        "3": ["3"],
        "2": ["19", "18", "17", "16", "15", "14", "13", "12", "11", "10", "9", "8", "7", "6", "5", "4", "3", "2"],
        "1": ["19", "18", "17", "16", "15", "14", "13", "12", "11", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1"],
    }


@pytest.mark.parametrize(
    "chapter,expected_volume",
    [
        (
            "1",
            "1",
        ),
        (
            "2",
            "2",
        ),
        (
            "19",
            "2",
        ),
        (
            "3",
            "3",
        ),
        (
            "20",
            "4",
        ),
        ("30", "none"),
        ("0", "none"),
    ],
)
def test_volume_entity_get_volume_for_chapter(volume_request_response, chapter, expected_volume):
    entity = VolumeEntity(content=volume_request_response)
    assert expected_volume == entity.get_volume(chapter)


def test_volume_entity_from_url(volume_request_response):
    with mock.patch("cbz_tagger.database.entities.volume_entity.requests") as mock_request:
        mock_request.get.return_value = mock.Mock(json=mock.MagicMock(return_value=volume_request_response))
        entities = VolumeEntity.from_server_url(query_params={"ids[]": ["831b12b8-2d0e-4397-8719-1efee4c32f40"]})
        assert len(entities) == 1
        assert entities[0].chapter_count == 21


def test_volume_entity_can_store_and_load(volume_request_response):
    entity = VolumeEntity(content=volume_request_response)

    json_str = entity.to_json()
    new_entity = entity.from_json(json_str)
    assert entity.content == new_entity.content

    new_json_str = new_entity.to_json()
    assert json_str == new_json_str
