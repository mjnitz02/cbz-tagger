import json
from typing import Any
from typing import Dict
from typing import List
from xml.etree import ElementTree

from cbz_tagger.entities.base_entity import BaseEntity


class MangaSeeChapterEntity(BaseEntity):
    def __init__(self):
        self.rss_url = "https://mangasee123.com/rss/{}.xml"

    def parse_rss_feed(self, entity_id: str) -> Dict[str, str]:
        url = self.rss_url.format(entity_id)
        response = self.request_with_retry(url)

        root = ElementTree.fromstring(response.text)
        title_name = root.findall("channel")[0].find("title").text

        items = root.findall("channel/item")
        chapters = {}
        for item in items:
            title = item.find("title").text.replace(f"{title_name} ", "")
            link = str(item.find("link").text)
            chapters[title] = link
        return chapters

    def parse_chapter_download_links(self, url: str) -> List[str]:
        response = self.request_with_retry(url)
        chapter_metadata = {}
        for line in response.text.split("\n"):
            if "vm.CurChapter = {" in line:
                chapter_info = json.loads(line.replace(";\r", "").split("vm.CurChapter = ")[-1])
                chapter_metadata["chapter"] = float(chapter_info["Chapter"]) - 100000.0
                chapter_metadata["chapter"] = chapter_metadata["chapter"] / 10.0
                chapter_metadata["pages"] = int(chapter_info["Page"])
                chapter_metadata["date"] = chapter_info["Date"]
            if 'vm.CurPathName = "' in line:
                chapter_metadata["path_name"] = line.replace('";\r', "").split('vm.CurPathName = "')[-1]
            if 'vm.IndexName = "' in line:
                chapter_metadata["index_name"] = line.replace('";\r', "").split('vm.IndexName = "')[-1]

        if chapter_metadata["chapter"].is_integer():
            chapter_string = f"{int(chapter_metadata['chapter']):04}"
        else:
            chapter_string = f"{chapter_metadata['chapter']:06.1f}"

        links = []
        page_root_url = (
            f"https://{chapter_metadata['path_name']}/manga/{chapter_metadata['index_name']}/{chapter_string}"
        )
        for page in range(1, chapter_metadata["pages"] + 1):
            links.append(f"{page_root_url}-{page:03}.png")
        return links
