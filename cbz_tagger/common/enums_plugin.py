from pydantic import BaseModel


class ChapterData(BaseModel):
    """Data model representing chapter information for building standardized responses."""

    chapter_id: str
    entity_id: str
    plugin_type: str
    title: str
    url: str
    chapter: str
    translated_language: str = "en"
    pages: int = -1
    volume: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    scanlation_group: str | None = None


class ChapterResponseBuilder:
    """Builder for creating standardized chapter response dictionaries."""

    @staticmethod
    def build(data: ChapterData) -> dict:
        """Build a complete standardized response dict from ChapterData.

        Returns a dict with all required fields for API compatibility,
        including relationships and timestamp fields.
        """
        return {
            "id": data.chapter_id,
            "type": data.plugin_type,
            "attributes": {
                "title": data.title,
                "url": data.url,
                "chapter": data.chapter,
                "translatedLanguage": data.translated_language,
                "pages": data.pages,
                "volume": data.volume,
                "createdAt": data.created_at,
                "updatedAt": data.updated_at,
            },
            "relationships": [{"type": "scanlation_group", "id": data.scanlation_group}],
        }
