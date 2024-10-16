from typing import Any
from typing import List

from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.enums import Urls
from cbz_tagger.entities.base_entity import BaseEntity


class ChapterPluginCMK(BaseEntity):
    entity_url = f"https://{Urls.CMK}/"

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
    def parse_info_feed(cls, entity_id: str) -> List[Any]:
        url = f"{cls.entity_url}comic/{entity_id}"
        response = cls.request_with_retry(url)
        info = response.json()

        manga_id = info["comic"]["hid"]
        page_url = f"{cls.entity_url}comic/{manga_id}/chapters?lang=en&page="

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

        if len(set(r["id"] for r in items)) != total:
            raise EnvironmentError("Paginated response contains duplicate entries")

        content = []
        # This constructs an api compatible response from the rss feed
        for item in items:
            # link = str(item.find("link").text)
            group_id = None
            if len(item["group_name"]) > 0:
                group_id = item["group_name"][0]
            content.append(
                {
                    "id": f"{manga_id}-{item['hid']}",
                    "type": Plugins.CMK,
                    "attributes": {
                        "title": item["title"],
                        "url": f"{cls.entity_url}chapter/{item['hid']}?tachiyomi=true",
                        "chapter": item["chap"],
                        "translatedLanguage": "en",
                        "pages": -1,
                        "volume": item["vol"],
                    },
                    "relationships": [{"type": "scanlation_group", "id": group_id}],
                }
            )
        return content

    def parse_chapter_download_links(self, url: str) -> List[str]:
        response = self.request_with_retry(url)
        response_json = response.json()
        chapter_content = response_json["chapter"]
        links = []
        for image in chapter_content["images"]:
            links.append(image["url"])
        return links
