from unittest import mock

import pytest

from cbz_tagger.entities.volume_entity import VolumeEntity


def test_volume_entity(volume_request_response):
    entity = VolumeEntity(content=volume_request_response)

    # Volume entities are very simple and have little metadata
    assert entity.entity_id is None
    assert entity.entity_type is None
    assert entity.attributes == {}
    assert entity.relationships == {}

    assert entity.chapter_count == 22
    assert sorted(entity.chapters) == [
        "1",
        "10",
        "100",
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
        "none": ["100"],
        "4": ["21", "20", "16", "13"],
        "3": ["3"],
        "2": ["19", "18", "17", "16", "15", "14", "13", "12", "11", "10", "9", "8", "7", "6", "5", "4", "3", "2"],
        "1": ["19", "18", "17", "16", "15", "14", "13", "12", "11", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1"],
    }
    assert entity.volume_map == [("1", 1.0, 2.0), ("2", 2.0, 3.0), ("3", 3.0, 13.0), ("4", 13.0, 999999)]


def test_volume_entity_with_broken_chapters(volume_request_response):
    entity = VolumeEntity(content=volume_request_response)

    # Add partial chapter and none chapter to records
    entity.content["volumes"]["3"]["chapters"]["3.1"] = (
        {"chapter": "3.1", "id": "d139dfa2-fcb7-40e4-b567-ce772aa739e2", "others": [], "count": 1},
    )
    entity.content["volumes"]["3"]["chapters"]["none"] = (
        {"chapter": "none", "id": "d139dfa2-fcb7-40e4-b567-ce772aa739e3", "others": [], "count": 1},
    )
    entity.content["volumes"]["0"] = {
        "volume": 0,
        "count": 0,
        "chapters": [
            {"chapter": "0", "id": "d139dfa2-fcb7-40e4-b567-ce772aa739e3", "others": [], "count": 1},
        ],
    }
    assert entity.volumes == {
        "none": ["100"],
        "4": ["21", "20", "16", "13"],
        "3": ["3", "3.1"],
        "2": ["19", "18", "17", "16", "15", "14", "13", "12", "11", "10", "9", "8", "7", "6", "5", "4", "3", "2"],
        "1": ["19", "18", "17", "16", "15", "14", "13", "12", "11", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1"],
    }
    assert "3.1" in entity.chapters
    assert entity.get_volume("3.1") == "3"


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
            "4",
        ),
        (
            "3",
            "3",
        ),
        (
            "20",
            "4",
        ),
        ("30", "4"),
        ("0", "-1"),
        ("100", "4"),
        ("2.5", "2"),
        ("3.5", "3"),
    ],
)
def test_volume_entity_get_volume_for_chapter(volume_request_response, chapter, expected_volume):
    entity = VolumeEntity(content=volume_request_response)
    assert expected_volume == entity.get_volume(chapter)


def test_volume_entity_from_url(volume_request_response):
    with mock.patch("cbz_tagger.entities.volume_entity.requests") as mock_request:
        mock_request.get.return_value = mock.Mock(json=mock.MagicMock(return_value=volume_request_response))
        entities = VolumeEntity.from_server_url(query_params={"ids[]": ["831b12b8-2d0e-4397-8719-1efee4c32f40"]})
        assert len(entities) == 1
        assert entities[0].chapter_count == 22


def test_volume_entity_can_store_and_load(volume_request_response, check_entity_for_save_and_load):
    entity = VolumeEntity(content=volume_request_response)
    check_entity_for_save_and_load(entity)
