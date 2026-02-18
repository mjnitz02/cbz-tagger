import base64
import logging
import time
from typing import Any

from cbz_tagger.common.enums import Plugins
from cbz_tagger.entities.plugins.plugin import ChapterPluginEntity

logger = logging.getLogger()


@Plugins.register("cmk")
class ChapterPluginCMK(ChapterPluginEntity):
    PLUGIN_TYPE = "cmk"
    BASE_URL = base64.b64decode("YXBpLmNvbWljay5mdW4=").decode("utf-8")
    TITLE_URL = f"https://{BASE_URL}/comic/"
    entity_url = f"https://{BASE_URL}/"

    @classmethod
    def get_chapter_page_items(cls, page_url: str) -> tuple[list[Any], int]:
        items = []
        total = None
        page = 1
        while True:
            response = cls.request_with_retry(f"{page_url}{page}")
            data = response.json()
            if total is None:
                total = data["total"]
            items.extend(data["chapters"])
            if len(items) < total:
                page += 1
            else:
                break

        return items, total

    @classmethod
    def parse_info_feed(cls, entity_id: str) -> list[Any]:
        url = f"{cls.entity_url}comic/{entity_id}?tachiyomi=true"
        response = cls.request_with_retry(url)
        info = response.json()

        manga_id = info["comic"]["hid"]
        page_url = f"{cls.entity_url}comic/{manga_id}/chapters?lang=en&page="

        items = []
        total = 0
        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                items, total = cls.get_chapter_page_items(page_url)
                if len(set(r["id"] for r in items)) != total:
                    raise EnvironmentError("Paginated response contains duplicate entries")
                break  # Success, exit retry loop
            except EnvironmentError as e:
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in 10 seconds...")
                    time.sleep(10)
                else:
                    logger.error(f"All {max_retries + 1} attempts failed: {e}")
                    raise

        content = []
        for item in items:
            group_id = None
            if isinstance(item["group_name"], list) and len(item["group_name"]) > 0:
                group_id = item["group_name"][0]

            content.append(
                cls.ResponseBuilder.build(
                    cls.build_chapter_data(
                        chapter_id=f"{manga_id}-{item['hid']}",
                        entity_id=entity_id,
                        title=item["title"],
                        url=f"{cls.entity_url}chapter/{item['hid']}?tachiyomi=true",
                        chapter=item["chap"],
                        volume=item["vol"],
                        created_at=item.get("created_at"),
                        updated_at=item.get("created_at"),  # updatedAt is unreliable for CMK
                        scanlation_group=group_id,
                    )
                )
            )
        return content

    def parse_chapter_download_links(self, url: str) -> list[str]:
        response = self.request_with_retry(url)
        response_json = response.json()
        chapter_content = response_json["chapter"]
        links = []
        for image in chapter_content["images"]:
            if "null" not in image["url"]:
                links.append(image["url"])
        return links
