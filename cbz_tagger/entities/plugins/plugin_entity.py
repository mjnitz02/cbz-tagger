import logging
import os
from abc import abstractmethod
from io import BytesIO

from PIL import Image
from PIL import ImageFile

from cbz_tagger.common.html_scraper import HtmlScraper
from cbz_tagger.common.http_client import download_file
from cbz_tagger.common.http_client import request_with_retry
from cbz_tagger.entities.chapter_entity import ChapterEntity

logger = logging.getLogger()


class ChapterPluginEntity:
    """Base class for chapter source plugins.

    A plugin is transport only: it fetches from a source and adapts what it finds into
    ChapterEntity. It holds no per-chapter state, so every method is a classmethod that
    takes the chapter it is acting on.

    Subclasses must:
    - Define PLUGIN_TYPE class variable matching a Plugins constant
    - Implement parse_info_feed() to fetch chapter listings
    - Implement parse_chapter_download_links() to get image URLs for a chapter

    Use @Plugins.register() decorator to auto-register the plugin.
    """

    PLUGIN_TYPE: str = ""  # Must be set by subclasses; set with @Plugins.register("type") decorator
    BASE_URL: str = ""  # Must be set by subclasses; used to set API endpoints and construct chapter URLs
    TITLE_URL: str = ""  # Must be set by subclasses; used to construct entity links
    quality = "data"  # Default quality for chapter images; can be overridden by subclasses if needed

    @classmethod
    def fetch_chapters(cls, entity_id: str) -> list[ChapterEntity]:
        return cls.parse_info_feed(entity_id)

    @classmethod
    def fetch_and_parse(cls, url: str) -> HtmlScraper:
        """Fetch a URL and return an HtmlScraper for parsing.

        Args:
            url: The URL to fetch

        Returns:
            HtmlScraper instance ready for parsing
        """
        response = request_with_retry(url)
        return HtmlScraper.from_response(response)

    @classmethod
    def get_chapter_url(cls, chapter: ChapterEntity) -> str:
        return chapter.url or ""

    @classmethod
    @abstractmethod
    def parse_info_feed(cls, entity_id: str) -> list[ChapterEntity]:
        """Fetch and parse chapter listings for an entity.

        Args:
            entity_id: The unique identifier for the manga/series

        Returns:
            List of ChapterEntity. Use build_chapter() to construct them so the
            plugin's own type is recorded on each chapter.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def parse_chapter_download_links(cls, chapter: ChapterEntity, url: str) -> list[str]:
        """Parse download links for chapter images from a chapter URL.

        Args:
            chapter: The chapter being downloaded
            url: The chapter page URL

        Returns:
            List of image URLs to download
        """
        raise NotImplementedError

    @classmethod
    def build_chapter(
        cls,
        chapter_id: str,
        title: str,
        url: str,
        chapter: str,
        translated_language: str = "en",
        pages: int = -1,
        volume: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        scanlation_group_id: str | None = None,
    ) -> ChapterEntity:
        """Create a ChapterEntity stamped with this plugin's type."""
        return ChapterEntity(
            chapter_id=chapter_id,
            plugin_type=cls.PLUGIN_TYPE,
            title=title,
            url=url,
            chapter=chapter,
            translated_language=translated_language,
            pages=pages,
            volume=volume,
            created_at=created_at,
            updated_at=updated_at,
            scanlation_group_id=scanlation_group_id,
        )

    @classmethod
    def download_chapter(cls, chapter: ChapterEntity, filepath) -> list[str]:
        # Get chapter image urls
        url = cls.get_chapter_url(chapter)
        download_links = cls.parse_chapter_download_links(chapter, url)

        # Download the images for the chapter
        cached_images = []
        for index, image_url in enumerate(download_links):
            image_path = os.path.join(filepath, f"{index + 1:03}.jpg")
            cached_images.append(image_path)
            if not os.path.exists(image_path):
                image = download_file(image_url)
                in_memory_image = Image.open(BytesIO(image))
                if in_memory_image.format != "JPEG":
                    in_memory_image = in_memory_image.convert("RGB")
                try:
                    in_memory_image.save(image_path, quality=95, optimize=True)
                except OSError:
                    ImageFile.LOAD_TRUNCATED_IMAGES = True  # type: ignore[misc]
                    in_memory_image.save(image_path, quality=95, optimize=True)

        if chapter.pages != -1 and len(cached_images) != chapter.pages:
            logger.error("Failed to download chapter %s, not enough pages saved from server", chapter.chapter_id)
            raise EnvironmentError(
                f"Failed to download chapter {chapter.chapter_id}, not enough pages saved from server"
            )
        if chapter.pages == -1 and len(cached_images) != len(download_links):
            logger.error("Failed to download chapter %s, not enough pages saved from server", chapter.chapter_id)
            raise EnvironmentError(
                f"Failed to download chapter {chapter.chapter_id}, not enough pages saved from server"
            )

        return cached_images
