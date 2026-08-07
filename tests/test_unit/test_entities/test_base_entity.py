import json

from cbz_tagger.entities.base_entity import BaseEntity


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


def test_base_entity_to_hash(manga_request_content):
    # Create an entity from the content
    entity = BaseEntity(content=manga_request_content)
    hash_value = entity.to_hash()

    # Hash should be consistent for the same content
    assert entity.to_hash() == hash_value

    # Create a new entity with the same content
    # It should have the same hash
    entity2 = BaseEntity(content=manga_request_content.copy())
    assert entity2.to_hash() == hash_value

    # Modify the content and check that the hash changes
    modified_content = manga_request_content.copy()
    modified_content["id"] = "different-id"
    entity3 = BaseEntity(content=modified_content)
    assert entity3.to_hash() != hash_value

    # Test with reordered keys - hash should be the same due to sort_keys=True
    reordered_content = {}
    # Reverse the order of keys to ensure they're different
    for key in reversed(list(manga_request_content.keys())):
        reordered_content[key] = manga_request_content[key]
    entity4 = BaseEntity(content=reordered_content)
    assert entity4.to_hash() == hash_value
