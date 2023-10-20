from unittest import mock

from cbz_tagger.database.entities.author_entity import AuthorEntity
from cbz_tagger.database.entities.base_entity import BaseEntity


def test_author_entity(author_request_content):
    entity = AuthorEntity(content=author_request_content)
    assert entity.entity_id == "88259f42-5a70-4eff-b5f0-8687ab8844b9"
    assert entity.entity_type == "author"

    assert entity.name == "Kawasaki Tadataka"


def test_author_entity_from_url(author_request_response):
    with mock.patch("cbz_tagger.database.entities.base_entity.unpaginate_request") as mock_request:
        mock_request.return_value = author_request_response["data"]
        entities = AuthorEntity.from_server_url()
        assert len(entities) == 1
        assert entities[0].entity_id == "88259f42-5a70-4eff-b5f0-8687ab8844b9"
        mock_request.assert_called_once_with(f"{BaseEntity.base_url}/author", None)


def test_author_entity_can_store_and_load(author_request_content):
    entity = AuthorEntity(content=author_request_content)

    json_str = entity.to_json()
    new_entity = entity.from_json(json_str)
    assert entity.content == new_entity.content

    new_json_str = new_entity.to_json()
    assert json_str == new_json_str
