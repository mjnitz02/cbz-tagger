from abc import abstractmethod
from typing import Any

from cbz_tagger.entities.base_entity import BaseEntity
from cbz_tagger.entities.chapter_plugins.response_builder import ChapterData
from cbz_tagger.entities.chapter_plugins.response_builder import ChapterResponseBuilder


class ChapterPluginEntity(BaseEntity):
    """Base class for chapter source plugins.

    Subclasses must:
    - Define PLUGIN_TYPE class variable matching a Plugins constant
    - Implement parse_info_feed() to fetch chapter listings
    - Implement parse_chapter_download_links() to get image URLs for a chapter

    Use @Plugins.register() decorator to auto-register the plugin.
    """

    PLUGIN_TYPE: str = ""  # Must be set by subclasses
    BASE_URL: str = ""  # Must be set by subclasses; used to set API endpoints and construct chapter URLs
    TITLE_URL: str = ""  # Must be set by subclasses; used to construct entity links
    ResponseBuilder = ChapterResponseBuilder

    @classmethod
    def from_server_url(cls, query_params=None, **kwargs):
        if "plugin_id" not in kwargs:
            raise EnvironmentError("plugin_id not provided")
        entity_id = kwargs["plugin_id"]
        response = cls.parse_info_feed(entity_id)
        return response

    def get_chapter_url(self):
        return self.attributes.get("url", "")

    @classmethod
    @abstractmethod
    def parse_info_feed(cls, entity_id: str) -> list[Any]:
        """Fetch and parse chapter listings for an entity.

        Args:
            entity_id: The unique identifier for the manga/series

        Returns:
            List of chapter response dicts. Use build_chapter_data() and
            ResponseBuilder.build() for standardized formatting.
        """
        raise NotImplementedError

    @abstractmethod
    def parse_chapter_download_links(self, url: str) -> list[str]:
        """Parse download links for chapter images from a chapter URL.

        Args:
            url: The chapter page URL

        Returns:
            List of image URLs to download
        """
        raise NotImplementedError

    @classmethod
    def build_chapter_data(
        cls,
        chapter_id: str,
        entity_id: str,
        title: str,
        url: str,
        chapter: str,
        translated_language: str = "en",
        pages: int = -1,
        volume: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        scanlation_group: str | None = None,
    ) -> ChapterData:
        """Create a ChapterData instance with the plugin's type.

        Convenience method that automatically sets the plugin_type from
        the class's PLUGIN_TYPE attribute.
        """
        return ChapterData(
            chapter_id=chapter_id,
            entity_id=entity_id,
            plugin_type=cls.PLUGIN_TYPE,
            title=title,
            url=url,
            chapter=chapter,
            translated_language=translated_language,
            pages=pages,
            volume=volume,
            created_at=created_at,
            updated_at=updated_at,
            scanlation_group=scanlation_group,
        )
