import pytest

from cbz_tagger.entities.chapter_entity import ChapterEntity


@pytest.fixture
def get_chapter_entity():
    def _get_chapter_entity(chapter: str | None) -> ChapterEntity:
        return ChapterEntity.from_content(
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


def test_scanlation_group(get_chapter_entity):
    entity = get_chapter_entity("1")
    assert entity.scanlation_group == "group_id"


def test_scanlation_group_with_no_relationships():
    entity = ChapterEntity.from_content({"id": "chapter_id", "attributes": {"chapter": "1"}, "relationships": []})
    assert entity.scanlation_group == "none"


def test_scanlation_group_with_no_defined_group():
    entity = ChapterEntity.from_content(
        {
            "id": "chapter_id",
            "attributes": {"chapter": "1"},
            "relationships": [{"type": "scanlation_group", "id": None}],
        }
    )
    assert entity.scanlation_group == "none"


def test_from_content_reads_a_legacy_mangadex_row():
    """Rows written by older versions carry MangaDex's own `type` and its extra attributes."""
    entity = ChapterEntity.from_content(
        {
            "id": "chapter_id",
            "type": "chapter",
            "attributes": {
                "chapter": "5",
                "volume": "1",
                "translatedLanguage": "en",
                "pages": 12,
                "createdAt": "2024-01-01T00:00:00+00:00",
                "updatedAt": "2024-01-02T00:00:00+00:00",
                "externalUrl": None,
                "publishAt": "2024-01-03T00:00:00+00:00",
                "version": 3,
            },
            "relationships": [
                {"type": "scanlation_group", "id": "GROUP_ID"},
                {"type": "manga", "id": "manga_id"},
            ],
        }
    )

    assert entity.plugin_type == "mdx"
    assert entity.chapter_id == "chapter_id"
    assert entity.chapter_number == 5
    assert entity.volume_number == 1.0
    assert entity.pages == 12
    assert entity.scanlation_group == "group_id"

    # Fields the application never reads are not carried back out. MangaDex is now adapted
    # into the same shape as every other plugin rather than stored verbatim.
    assert entity.to_content() == {
        "id": "chapter_id",
        "type": "mdx",
        "attributes": {
            "title": None,
            "url": None,
            "chapter": "5",
            "translatedLanguage": "en",
            "pages": 12,
            "volume": "1",
            "createdAt": "2024-01-01T00:00:00+00:00",
            "updatedAt": "2024-01-02T00:00:00+00:00",
        },
        "relationships": [{"type": "scanlation_group", "id": "GROUP_ID"}],
    }


def test_to_content_round_trips():
    content = ChapterEntity.from_content(
        {
            "id": "chapter_id",
            "type": "wbc",
            "attributes": {
                "title": "Chapter 3.1",
                "url": "https://example.com/chapters/3.1",
                "chapter": "3.1",
                "translatedLanguage": "en",
                "pages": -1,
                "volume": None,
                "createdAt": None,
                "updatedAt": "2024-09-07T17:04:15.717343Z",
            },
            "relationships": [{"type": "scanlation_group", "id": None}],
        }
    ).to_content()

    assert ChapterEntity.from_content(content).to_content() == content
