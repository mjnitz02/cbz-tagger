from unittest.mock import patch

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
        "0": [],  # Volume 0 has no chapters
    }
    assert entity.volume_map == [("1", 0.0, 2.0), ("2", 2.0, 3.0), ("3", 3.0, 13.0), ("4", 13.0, 22.0)]


def test_volume_entity_with_no_data_available(volume_request_response_none_available):
    entity = VolumeEntity(content=volume_request_response_none_available)

    # Volume entities are very simple and have little metadata
    assert entity.entity_id is None
    assert entity.entity_type is None
    assert entity.attributes == {}
    assert entity.relationships == {}

    assert entity.chapter_count == 0
    assert sorted(entity.chapters) == []
    assert entity.volumes == {}
    assert entity.volume_map == [("-1", 0.0, 0.0)]


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
        ("1", "1"),
        ("2", "2"),
        ("2.5", "2"),
        ("3", "3"),
        ("3.5", "3"),
        ("19", "4"),
        ("20", "4"),
        ("21", "4"),
        ("21.5", "4"),
        ("22", "5"),
        ("30", "5"),
        ("30.5", "5"),
        ("40", "6"),
        ("50", "7"),
        ("100", "12"),
        ("0", "1"),
        ("-1", "-1"),
    ],
)
def test_volume_entity_get_volume_for_chapter(volume_request_response, chapter, expected_volume):
    entity = VolumeEntity(content=volume_request_response)
    assert expected_volume == entity.get_volume(chapter)


def test_volume_entity_get_volume_for_chapter_with_no_volume_map():
    entity = VolumeEntity(content={"result": "ok", "volumes": {}})
    assert "-1" == entity.get_volume("1")
    assert "-1" == entity.get_volume("10")


@patch("cbz_tagger.entities.base_entity.random.uniform", return_value=0.1)
@patch("cbz_tagger.entities.base_entity.time.sleep")
def test_volume_entity_from_url(mock_sleep, mock_random, requests_mock, volume_request_response):
    requests_mock.get(
        f"{VolumeEntity.base_url}/manga/831b12b8-2d0e-4397-8719-1efee4c32f40/aggregate",
        json=volume_request_response,
    )
    entities = VolumeEntity.from_server_url(query_params={"ids[]": ["831b12b8-2d0e-4397-8719-1efee4c32f40"]})
    assert len(entities) == 1
    assert entities[0].chapter_count == 22


def test_volume_entity_can_store_and_load(volume_request_response, check_entity_for_save_and_load):
    entity = VolumeEntity(content=volume_request_response)
    check_entity_for_save_and_load(entity)


def test_last_volume(volume_request_response):
    entity = VolumeEntity(content=volume_request_response)
    assert entity.last_volume == 4


def test_last_volume_with_only_integer_keys():
    content = {
        "result": "ok",
        "volumes": {
            "2": {
                "volume": "2",
                "count": 1,
                "chapters": {
                    "2": {},
                },
            },
            "1": {
                "volume": "1",
                "count": 1,
                "chapters": {
                    "1": {},
                },
            },
        },
    }
    entity = VolumeEntity(content)
    assert entity.last_volume == 2


def test_last_volume_with_only_integer_and_none_keys():
    content = {
        "result": "ok",
        "volumes": {
            "none": {
                "volume": "none",
                "count": 3,
                "chapters": {
                    "none": {},
                },
            },
            "2": {
                "volume": "2",
                "count": 1,
                "chapters": {
                    "2": {},
                },
            },
            "1": {
                "volume": "1",
                "count": 1,
                "chapters": {
                    "1": {},
                },
            },
        },
    }
    entity = VolumeEntity(content)
    assert entity.last_volume == 2


def test_last_volume_with_only_integer_and_decimal_keys():
    content = {
        "result": "ok",
        "volumes": {
            "3.5": {
                "volume": "3.5",
                "count": 1,
                "chapters": {
                    "none": {},
                },
            },
            "2": {
                "volume": "2",
                "count": 1,
                "chapters": {
                    "2": {},
                },
            },
            "1": {
                "volume": "1",
                "count": 1,
                "chapters": {
                    "1": {},
                },
            },
        },
    }
    entity = VolumeEntity(content)
    assert entity.last_volume == 3
