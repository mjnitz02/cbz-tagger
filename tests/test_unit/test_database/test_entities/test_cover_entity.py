from unittest import mock

from cbz_tagger.database.entities.base_entity import BaseEntity
from cbz_tagger.database.entities.cover_entity import CoverEntity


def test_cover_entity(cover_request_content):
    entity = CoverEntity(content=cover_request_content)
    assert entity.entity_id == "be31ba9c-3490-41ea-b1bd-7f31cad7322f"
    assert entity.entity_type == "cover_art"

    assert entity.filename == "87ad56cd-780b-48bc-82b1-fa425836f9a4.jpg"
    assert entity.local_filename == "87ad56cd-780b-48bc-82b1-fa425836f9a4.jpg"
    assert entity.volume == "4"
    assert entity.manga_id == "831b12b8-2d0e-4397-8719-1efee4c32f40"
    assert (
        entity.cover_url
        == "https://uploads.mangadex.org/covers/831b12b8-2d0e-4397-8719-1efee4c32f40/87ad56cd-780b-48bc-82b1-fa425836f9a4.jpg"
    )


def test_cover_entity_with_png(cover_request_content_png):
    entity = CoverEntity(content=cover_request_content_png)
    assert entity.entity_id == "5d989a45-0946-4f22-9a79-53cc26e6e958"
    assert entity.entity_type == "cover_art"

    assert entity.filename == "39194a9c-719b-4a27-b8ef-99a3d6fa0997.png"
    assert entity.local_filename == "39194a9c-719b-4a27-b8ef-99a3d6fa0997.jpg"
    assert entity.volume == "2"
    assert entity.manga_id == "831b12b8-2d0e-4397-8719-1efee4c32f40"
    assert (
        entity.cover_url
        == "https://uploads.mangadex.org/covers/831b12b8-2d0e-4397-8719-1efee4c32f40/39194a9c-719b-4a27-b8ef-99a3d6fa0997.png"
    )


def test_cover_entity_from_url(cover_request_response):
    with mock.patch("cbz_tagger.database.entities.base_entity.unpaginate_request") as mock_request:
        mock_request.return_value = cover_request_response["data"]
        entities = CoverEntity.from_server_url()
        assert len(entities) == 4
        assert entities[0].entity_id == "be31ba9c-3490-41ea-b1bd-7f31cad7322f"
        assert entities[1].entity_id == "5d989a45-0946-4f22-9a79-53cc26e6e958"
        assert entities[2].entity_id == "7be23c33-7b1e-4f2a-a9fe-ad3d6263f30f"
        assert entities[3].entity_id == "9d64b6fb-0cac-4fa7-b3da-553fea602d2d"
        mock_request.assert_called_once_with(f"{BaseEntity.base_url}/cover", None)


def test_cover_entity_can_store_and_load(cover_request_content):
    entity = CoverEntity(content=cover_request_content)

    json_str = entity.to_json()
    new_entity = entity.from_json(json_str)
    assert entity.content == new_entity.content

    new_json_str = new_entity.to_json()
    assert json_str == new_json_str
