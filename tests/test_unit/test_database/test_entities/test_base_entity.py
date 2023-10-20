import json
from unittest import mock

from cbz_tagger.database.entities.base_entity import BaseEntity


def test_base_entity(manga_request_content):
    entity = BaseEntity(content=manga_request_content)
    assert entity.entity_id == "831b12b8-2d0e-4397-8719-1efee4c32f40"
    assert entity.content["id"] == "831b12b8-2d0e-4397-8719-1efee4c32f40"
    assert entity.entity_type == "manga"
    assert entity.content["type"] == "manga"
    assert entity.content["attributes"] == entity.attributes
    assert entity.content["relationships"] == entity.relationships


def test_base_entity_from_json(manga_request_content):
    json_str = json.dumps(manga_request_content)
    entity_from_json = BaseEntity.from_json(json_str)
    assert entity_from_json.content == manga_request_content


def test_base_entity_to_json(manga_request_content):
    entity = BaseEntity(content=manga_request_content)
    entity_json = entity.to_json()
    json_str = json.dumps(manga_request_content)
    assert entity_json == json_str
