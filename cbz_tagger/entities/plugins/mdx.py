import logging
import time
from typing import Any

from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.enums import Urls
from cbz_tagger.entities.plugins.plugin import ChapterPluginEntity

logger = logging.getLogger()


@Plugins.register("mdx")
class ChapterPluginMDX(ChapterPluginEntity):
    """MangaDex chapter plugin.

    Note: MDX uses the standard API response format directly from the server,
    so it doesn't use the ResponseBuilder for parse_info_feed.
    """

    PLUGIN_TYPE = "mdx"
    BASE_URL = Urls.MDX
    TITLE_URL = f"https://{BASE_URL}/title/"
    entity_url: str = f"https://api.{BASE_URL}/manga"
    download_url: str = f"https://api.{BASE_URL}/at-home/server"

    @classmethod
    def fetch_chapters(cls, entity_id: str) -> list:
        order = {
            "createdAt": "asc",
            "updatedAt": "asc",
            "publishAt": "asc",
            "readableAt": "asc",
            "volume": "asc",
            "chapter": "asc",
        }
        params = "&".join([f"order%5B{key}%5D={value}" for key, value in order.items()])
        return cls.unpaginate_request(f"{cls.entity_url}/{entity_id}/feed?{params}")

    def get_chapter_url(self):
        url = f"{self.download_url}/{self.entity_id}"
        return url

    @classmethod
    def parse_info_feed(cls, entity_id: str) -> list[Any]:
        return []

    def parse_chapter_download_links(self, url: str) -> list[str]:
        response = self.request_with_retry(url).json()
        pages = self.attributes.get("pages")

        # If we didn't retrieve enough pages, try to query again
        if len(response["chapter"][self.quality]) != pages:
            logger.error("Not enough pages returned from server. Waiting 10s and retrying query.")
            time.sleep(10)
            response = self.request_with_retry(url).json()
            if len(response["chapter"][self.quality]) != pages:
                raise EnvironmentError(
                    f"Failed to download chapter {self.entity_id}, not enough pages returned from server"
                )

        base_url = f"{response['baseUrl']}/{self.quality}/{response['chapter']['hash']}"
        links = []
        for chapter_image_name in response["chapter"][self.quality]:
            links.append(f"{base_url}/{chapter_image_name}")
        return links
