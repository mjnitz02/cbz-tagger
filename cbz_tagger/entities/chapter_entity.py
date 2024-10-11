import json
import os
import re
from io import BytesIO
from time import sleep
from typing import Any
from typing import List
from xml.etree import ElementTree

from PIL import Image
from PIL import ImageFile

from cbz_tagger.entities.base_entity import BaseEntity


class MangaDexChapterEntity(BaseEntity):
    entity_url: str = f"{BaseEntity.base_url}/manga"
    download_url: str = f"{BaseEntity.base_url}/at-home/server"
    paginated: bool = False
    quality = "data"

    @classmethod
    def from_server_url(cls, query_params=None):
        entity_id = query_params["ids[]"][0]

        order = {
            "createdAt": "asc",
            "updatedAt": "asc",
            "publishAt": "asc",
            "readableAt": "asc",
            "volume": "asc",
            "chapter": "asc",
        }
        params = "&".join([f"order%5B{key}%5D={value}" for key, value in order.items()])
        response = cls.unpaginate_request(f"{cls.entity_url}/{entity_id}/feed?{params}")
        return [cls(data) for data in response]

    @property
    def chapter_number(self):
        chapter = str(self.attributes.get("chapter", ""))
        if chapter.count(".") > 1:
            chapter_split = chapter.split(".")
            chapter = f"{chapter_split[0]}.{''.join(chapter_split[1:])}"
        return float(chapter)

    @property
    def chapter_string(self) -> str:
        try:
            if self.chapter_number.is_integer():
                chapter_number = int(self.chapter_number)
            else:
                chapter_number = self.chapter_number
            return f"{chapter_number}"
        except (ValueError, TypeError):
            return str(self.chapter_number)

    @property
    def padded_chapter_string(self) -> str:
        try:
            if self.chapter_number.is_integer():
                chapter_number = int(self.chapter_number)
                return f"{chapter_number:03}"
            chapter_number = self.chapter_number
            decimal_size = len(str(self.chapter_number).split(".", maxsplit=1)[-1])
            if decimal_size == 2:
                return f"{chapter_number:06.2f}"
            if decimal_size == 3:
                return f"{chapter_number:07.3f}"
            return f"{chapter_number:05.1f}"
        except (ValueError, TypeError):
            return str(self.chapter_number)

    @property
    def volume_number(self):
        return float(self.attributes.get("volume"))

    @property
    def translated_language(self):
        return self.attributes.get("translatedLanguage")

    @property
    def pages(self):
        return self.attributes.get("pages")

    @property
    def scanlation_group(self):
        group = next(iter(rel for rel in self.relationships if rel["type"] == "scanlation_group"), {})
        return group.get("id", "none")

    def parse_chapter_download_links(self, url: str) -> List[str]:
        response = self.request_with_retry(url).json()

        # If we didn't retrieve enough pages, try to query again
        if len(response["chapter"][self.quality]) != self.pages:
            print("Not enough pages returned from server. Waiting 10s and retrying query.")
            sleep(10)
            response = self.request_with_retry(url).json()
            if len(response["chapter"][self.quality]) != self.pages:
                raise EnvironmentError(
                    f"Failed to download chapter {self.entity_id}, not enough pages returned from server"
                )

        base_url = f"{response['baseUrl']}/{self.quality}/{response['chapter']['hash']}"
        links = []
        for chapter_image_name in response["chapter"][self.quality]:
            links.append(f"{base_url}/{chapter_image_name}")
        return links

    def get_chapter_url(self):
        url = f"{self.download_url}/{self.entity_id}"
        return url

    def download_chapter(self, filepath) -> List[str]:
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
                    ImageFile.LOAD_TRUNCATED_IMAGES = True
                    in_memory_image.save(image_path, quality=95, optimize=True)

        if len(cached_images) != self.pages:
            raise EnvironmentError(f"Failed to download chapter {self.entity_id}, not enough pages saved from server")

        return cached_images


class MangaSeeChapterEntity(MangaDexChapterEntity):
    base_url = "https://mangasee123.com"
    entity_url = f"{base_url}/rss/"

    @property
    def mangasee_url(self):
        return self.attributes.get("url", "")

    @classmethod
    def from_server_url(cls, query_params=None):
        entity_id = query_params["ids[]"][0]
        response = cls.parse_rss_feed(entity_id)
        return [cls(data) for data in response]

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

    def get_chapter_url(self):
        return self.mangasee_url

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
        self.content["attributes"]["pages"] = chapter_metadata["pages"]
        for page in range(1, chapter_metadata["pages"] + 1):
            links.append(f"{page_root_url}-{page:03}.png")
        return links
