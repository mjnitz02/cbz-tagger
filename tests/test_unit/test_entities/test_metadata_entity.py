from datetime import datetime
from unittest import mock

from cbz_tagger.entities.base_entity import BaseEntity
from cbz_tagger.entities.metadata_entity import MetadataEntity


def test_metadata_entity(manga_request_content):
    entity = MetadataEntity(content=manga_request_content)
    assert entity.entity_id == "831b12b8-2d0e-4397-8719-1efee4c32f40"
    assert entity.entity_type == "manga"

    assert entity.title == "Oshimai"
    assert entity.alt_title == "4 Page Stories"
    assert entity.all_titles == [
        "Oshimai",
        "4 Page Stories",
        "Oshi-Mai: Four Page Stories",
        "The 4 Pages",
        "おしまい",
        "お四枚",
        "Oshi-Mai: Four Page Storys",
    ]
    assert entity.description == "A collection of twitter published manga by Kawasaki Tadataka..."
    assert not entity.completed
    assert entity.age_rating == "Teen"
    assert entity.author_entities == ["88259f42-5a70-4eff-b5f0-8687ab8844b9"]
    assert entity.author_id == "88259f42-5a70-4eff-b5f0-8687ab8844b9"
    assert entity.artist_id == "88259f42-5a70-4eff-b5f0-8687ab8844b9"
    assert entity.creator_id is None
    assert entity.cover_art_id == "be31ba9c-3490-41ea-b1bd-7f31cad7322f"
    assert entity.created_at == datetime.strptime("2020-07-23 14:50:37", "%Y-%m-%d %H:%M:%S")
    assert entity.genres == ["Seinen", "Anthology", "Comedy", "Romance", "School Life", "Slice of Life"]
    assert entity.demographic == "Seinen"


def test_metadata_entity_from_url(manga_request_response):
    with mock.patch("cbz_tagger.entities.base_entity.BaseEntity.unpaginate_request") as mock_request:
        mock_request.return_value = manga_request_response["data"]
        entities = MetadataEntity.from_server_url()
        assert len(entities) == 2
        assert entities[0].entity_id == "831b12b8-2d0e-4397-8719-1efee4c32f40"
        assert entities[1].entity_id == "f98660a1-d2e2-461c-960d-7bd13df8b76d"
        mock_request.assert_called_once_with(f"{BaseEntity.base_url}/manga", None)


def test_metadata_entity_can_store_and_load(manga_request_content, check_entity_for_save_and_load):
    entity = MetadataEntity(content=manga_request_content)
    check_entity_for_save_and_load(entity)


def test_genres_with_demographic():
    attributes = {
        "tags": [{"attributes": {"name": {"en": "Comedy"}}}, {"attributes": {"name": {"en": "Romance"}}}],
        "publicationDemographic": "seinen",
    }
    entity = MetadataEntity(content={"attributes": attributes})
    expected_genres = ["Seinen", "Comedy", "Romance"]
    assert entity.genres == expected_genres


def test_genres_with_duplicate_demographic():
    attributes = {
        "tags": [
            {"attributes": {"name": {"en": "Comedy"}}},
            {"attributes": {"name": {"en": "Romance"}}},
            {"attributes": {"name": {"en": "Seinen"}}},
        ],
        "publicationDemographic": "seinen",
    }
    entity = MetadataEntity(content={"attributes": attributes})
    expected_genres = ["Comedy", "Romance", "Seinen"]
    assert entity.genres == expected_genres


def test_genres_without_demographic():
    attributes = {
        "tags": [{"attributes": {"name": {"en": "Comedy"}}}, {"attributes": {"name": {"en": "Romance"}}}],
    }
    entity = MetadataEntity(content={"attributes": attributes})
    expected_genres = ["Comedy", "Romance"]
    assert entity.genres == expected_genres


def test_demographic():
    attributes = {"publicationDemographic": "seinen"}
    entity = MetadataEntity(content={"attributes": attributes})
    assert entity.demographic == "Seinen"


def test_demographic_none():
    attributes = {"publicationDemographic": None}
    entity = MetadataEntity(content={"attributes": attributes})
    assert entity.demographic is None
