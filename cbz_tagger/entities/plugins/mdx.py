import logging
import time

from cbz_tagger.common.enums import Urls
from cbz_tagger.common.http_client import request_with_retry
from cbz_tagger.common.http_client import unpaginate_request
from cbz_tagger.common.plugins import Plugins
from cbz_tagger.entities.chapter_entity import ChapterEntity
from cbz_tagger.entities.plugins.plugin_entity import ChapterPluginEntity

logger = logging.getLogger()


@Plugins.register("mdx")
class ChapterPluginMDX(ChapterPluginEntity):
    """MangaDex chapter plugin.

    MangaDex's API response shape happens to be the shape this database has always
    stored on disk, so adapting it is a straight `ChapterEntity.from_content` call —
    but it is an adapter like every other plugin's, not a privileged path.
    """

    BASE_URL = Urls.MDX
    TITLE_URL = f"https://{BASE_URL}/title/"
    entity_url: str = f"https://api.{BASE_URL}/manga"
    download_url: str = f"https://api.{BASE_URL}/at-home/server"
    chapter_url: str = f"https://uploads.{BASE_URL}"

    @classmethod
    def parse_info_feed(cls, entity_id: str) -> list[ChapterEntity]:
        order = {
            "createdAt": "asc",
            "updatedAt": "asc",
            "publishAt": "asc",
            "readableAt": "asc",
            "volume": "asc",
            "chapter": "asc",
        }
        params = "&".join([f"order%5B{key}%5D={value}" for key, value in order.items()])
        response = unpaginate_request(f"{cls.entity_url}/{entity_id}/feed?{params}")

        chapters = []
        for item in response:
            try:
                chapters.append(ChapterEntity.from_content(item))
            except (KeyError, TypeError, ValueError) as err:
                # A single malformed entry must not take down a 400-chapter feed.
                logger.error("Skipping unparseable chapter in feed for %s: %s", entity_id, err)
        return chapters

    @classmethod
    def get_chapter_url(cls, chapter: ChapterEntity) -> str:
        return f"{cls.download_url}/{chapter.chapter_id}"

    @classmethod
    def parse_chapter_download_links(cls, chapter: ChapterEntity, url: str) -> list[str]:
        response = request_with_retry(url).json()
        pages = chapter.pages

        # If we didn't retrieve enough pages, try to query again
        if len(response["chapter"][cls.quality]) != pages:
            logger.error("Not enough pages returned from server. Waiting 10s and retrying query.")
            time.sleep(10)
            response = request_with_retry(url).json()
            if len(response["chapter"][cls.quality]) != pages:
                raise EnvironmentError(
                    f"Failed to download chapter {chapter.chapter_id}, not enough pages returned from server"
                )

        base_url = f"{cls.chapter_url}/{cls.quality}/{response['chapter']['hash']}"
        links = []
        for chapter_image_name in response["chapter"][cls.quality]:
            links.append(f"{base_url}/{chapter_image_name}")
        return links
