import json
import re
from typing import Any
from typing import List
from xml.etree import ElementTree

from cbz_tagger.entities.chapter_entity import ChapterEntity


class ChapterEntityMangaSee(ChapterEntity):
    entity_url = "https://mangasee123.com/rss/"

    @classmethod
    def from_server_url(cls, query_params=None):
        entity_id = query_params["ids[]"][0]
        response = cls.parse_rss_feed(entity_id)
        return [cls(data) for data in response]

    def get_chapter_url(self):
        return self.attributes.get("url", "")

    @classmethod
    def parse_rss_feed(cls, entity_id: str) -> List[Any]:
        url = f"{cls.entity_url}{entity_id}.xml"
        response = cls.request_with_retry(url)

        root = ElementTree.fromstring(response.text)
        title_name = root.findall("channel")[0].find("title").text

        items = root.findall("channel/item")
        content = []
        # This constructs a mangadex api compatible response from the mangasee rss feed
        for item in items:
            title = item.find("title").text.replace(f"{title_name} ", "")
            link = str(item.find("link").text)
            content.append(
                {
                    "id": f"{entity_id}-{title}".replace(" ", "-").lower(),
                    "type": "chapter-manga-see",
                    "attributes": {
                        "title": title,
                        "url": link,
                        "chapter": re.sub("[^\\d.]", "", title),
                        "translatedLanguage": "en",
                        "pages": -1,
                        "volume": -1,
                    },
                }
            )
        return content

    def parse_chapter_download_links(self, url: str) -> List[str]:
        response = self.request_with_retry(url)
        chapter_metadata = {}
        for line in response.text.split("\n"):
            if "vm.CurChapter = {" in line:
                chapter_info = json.loads(line.replace(";", "").replace("\r", "").split("vm.CurChapter = ")[-1])
                chapter_metadata["chapter"] = float(chapter_info["Chapter"]) - 100000.0
                chapter_metadata["chapter"] = chapter_metadata["chapter"] / 10.0
                chapter_metadata["pages"] = int(chapter_info["Page"])
                chapter_metadata["date"] = chapter_info["Date"]
            if 'vm.CurPathName = "' in line:
                chapter_metadata["path_name"] = line.replace('";', "").replace("\r", "").split('vm.CurPathName = "')[-1]
            if 'vm.IndexName = "' in line:
                chapter_metadata["index_name"] = line.replace('";', "").replace("\r", "").split('vm.IndexName = "')[-1]

        if chapter_metadata["chapter"].is_integer():
            chapter_string = f"{int(chapter_metadata['chapter']):04}"
        else:
            chapter_string = f"{chapter_metadata['chapter']:06.1f}"

        links = []
        page_root_url = (
            f"https://{chapter_metadata['path_name']}/manga/{chapter_metadata['index_name']}/{chapter_string}"
        )
        self.content["attributes"]["pages"] = chapter_metadata["pages"]
        for page in range(1, chapter_metadata["pages"] + 1):
            links.append(f"{page_root_url}-{page:03}.png")
        return links
