from typing import Optional

import pytest

from cbz_tagger.entities.chapter_entity import ChapterEntity


@pytest.fixture
def get_chapter_entity():
    def _get_chapter_entity(chapter: Optional[str]) -> ChapterEntity:
        return ChapterEntity(
            {
                "id": "chapter_id",
                "attributes": {"chapter": chapter, "translatedLanguage": "en", "pages": 2},
                "relationships": [{"type": "scanlation_group", "id": "group_id"}],
            }
        )

    return _get_chapter_entity


def test_chapter_number_simple_float(get_chapter_entity):
    entity = get_chapter_entity("1.5")
    assert entity.chapter_number == 1.5


def test_chapter_number_multiple_dots(get_chapter_entity):
    entity = get_chapter_entity("1.2.3")
    assert entity.chapter_number == 1.23


def test_chapter_number_leading_dots(get_chapter_entity):
    entity = get_chapter_entity(".1.2.3")
    assert entity.chapter_number == 1.23


def test_chapter_number_invalid_float(get_chapter_entity):
    entity = get_chapter_entity("invalid")
    assert entity.chapter_number is None


def test_chapter_number_missing_entry(get_chapter_entity):
    entity = get_chapter_entity(None)
    assert entity.chapter_number is None
