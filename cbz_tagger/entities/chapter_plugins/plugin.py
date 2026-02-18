import logging
import os
from abc import abstractmethod
from datetime import datetime
from io import BytesIO
from typing import Any

from PIL import Image
from PIL import ImageFile

from cbz_tagger.entities.base_entity import BaseEntity
from cbz_tagger.entities.chapter_plugins.html_scraper import HtmlScraper
from cbz_tagger.entities.chapter_plugins.response_builder import ChapterData
from cbz_tagger.entities.chapter_plugins.response_builder import ChapterResponseBuilder

logger = logging.getLogger()


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
    quality = "data"

    @classmethod
    def fetch_chapters(cls, entity_id: str) -> list[Any]:
        return cls.parse_info_feed(entity_id)

    @classmethod
    def fetch_and_parse(cls, url: str) -> HtmlScraper:
        """Fetch a URL and return an HtmlScraper for parsing.

        Args:
            url: The URL to fetch

        Returns:
            HtmlScraper instance ready for parsing
        """
        response = cls.request_with_retry(url)
        return HtmlScraper.from_response(response)

    def get_chapter_url(self):
        return self.attributes.get("url", "")

    @property
    def chapter_number(self) -> float | None:
        chapter = str(self.attributes.get("chapter", ""))
        if chapter[0] == ".":
            chapter = chapter[1:]
        if chapter.count(".") > 1:
            chapter_split = chapter.split(".")
            chapter = f"{chapter_split[0]}.{''.join(chapter_split[1:])}"
        try:
            return float(chapter)
        except ValueError:
            return None

    @property
    def chapter_string(self) -> str:
        chapter_number = self.chapter_number
        if chapter_number is None:
            return str(chapter_number)
        try:
            if chapter_number.is_integer():
                return f"{int(chapter_number)}"
            return f"{chapter_number}"
        except (ValueError, TypeError):
            return str(chapter_number)

    @property
    def padded_chapter_string(self) -> str:
        chapter_number = self.chapter_number
        if chapter_number is None:
            return str(chapter_number)
        try:
            if chapter_number.is_integer():
                return f"{int(chapter_number):03}"
            decimal_size = len(str(chapter_number).split(".", maxsplit=1)[-1])
            if decimal_size == 2:
                return f"{chapter_number:06.2f}"
            if decimal_size == 3:
                return f"{chapter_number:07.3f}"
            return f"{chapter_number:05.1f}"
        except (ValueError, TypeError):
            return str(chapter_number)

    @property
    def volume_number(self) -> float | None:
        volume = self.attributes.get("volume")
        if volume is None:
            return None
        return float(volume)

    @property
    def translated_language(self) -> str | None:
        return self.attributes.get("translatedLanguage")

    @property
    def pages(self) -> int | None:
        return self.attributes.get("pages")

    @property
    def scanlation_group(self) -> str:
        group = next(iter(rel for rel in self.relationships if rel["type"] == "scanlation_group"), {})
        scanlation_group = group.get("id", "none")
        if scanlation_group is None:
            return "none"
        return scanlation_group.lower()

    @property
    def updated(self) -> str | None:
        return self.attributes.get("updatedAt")

    @property
    def updated_date(self) -> datetime | None:
        if self.updated is None:
            return None
        try:
            return datetime.fromisoformat(self.updated)
        except ValueError:
            return datetime.strptime(self.updated, "%a, %d %b %Y %H:%M:%S %z")

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

    def download_chapter(self, filepath) -> list[str]:
        # Get chapter image urls
        url = self.get_chapter_url()
        download_links = self.parse_chapter_download_links(url)

        # Download the images for the chapter
        cached_images = []
        for index, image_url in enumerate(download_links):
            image_path = os.path.join(filepath, f"{index + 1:03}.jpg")
            cached_images.append(image_path)
            if not os.path.exists(image_path):
                image = self.download_file(image_url)
                in_memory_image = Image.open(BytesIO(image))
                if in_memory_image.format != "JPEG":
                    in_memory_image = in_memory_image.convert("RGB")
                try:
                    in_memory_image.save(image_path, quality=95, optimize=True)
                except OSError:
                    ImageFile.LOAD_TRUNCATED_IMAGES = True  # type: ignore[misc]
                    in_memory_image.save(image_path, quality=95, optimize=True)

        if self.pages != -1 and len(cached_images) != self.pages:
            logger.error("Failed to download chapter %s, not enough pages saved from server", self.entity_id)
            raise EnvironmentError(f"Failed to download chapter {self.entity_id}, not enough pages saved from server")
        if self.pages == -1 and len(cached_images) != len(download_links):
            logger.error("Failed to download chapter %s, not enough pages saved from server", self.entity_id)
            raise EnvironmentError(f"Failed to download chapter {self.entity_id}, not enough pages saved from server")

        return cached_images
