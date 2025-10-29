import logging
import os
from datetime import datetime
from io import BytesIO

from PIL import Image
from PIL import ImageFile

from cbz_tagger.common.enums import Plugins
from cbz_tagger.entities.base_entity import BaseEntity
from cbz_tagger.entities.chapter_plugins.cmk import ChapterPluginCMK
from cbz_tagger.entities.chapter_plugins.kal import ChapterPluginKAL
from cbz_tagger.entities.chapter_plugins.mdx import ChapterPluginMDX
from cbz_tagger.entities.chapter_plugins.wbc import ChapterPluginWBC

logger = logging.getLogger()


class ChapterEntity(BaseEntity):
    download_url: str
    paginated: bool = False
    quality = "data"
    plugins = {
        Plugins.MDX: ChapterPluginMDX,
        Plugins.CMK: ChapterPluginCMK,
        Plugins.WBC: ChapterPluginWBC,
        Plugins.KAL: ChapterPluginKAL,
    }

    @classmethod
    def from_server_url(cls, query_params=None, **kwargs):
        plugin_type = kwargs.get("plugin_type", Plugins.MDX)
        entity_plugin = cls.plugins[plugin_type]
        response = entity_plugin.from_server_url(query_params=query_params, **kwargs)
        return [cls(data) for data in response]

    @property
    def chapter_number(self):
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
    def entity_type(self):
        # Backwards compatibility for old chapter types
        if self.content.get("type", "") == "chapter":
            return Plugins.MDX
        return self.content.get("type", Plugins.MDX)

    @property
    def entity_plugin(self):
        return self.plugins[self.entity_type](self.content)

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
    def scanlation_group(self) -> str:
        group = next(iter(rel for rel in self.relationships if rel["type"] == "scanlation_group"), {})
        scanlation_group = group.get("id", "none")
        if scanlation_group is None:
            return "none"
        return scanlation_group.lower()

    @property
    def updated(self):
        return self.attributes.get("updatedAt")

    @property
    def updated_date(self):
        try:
            return datetime.fromisoformat(self.updated)
        except ValueError:
            return datetime.strptime(self.updated, "%a, %d %b %Y %H:%M:%S %z")
        except TypeError:
            return None

    def get_chapter_url(self):
        return self.entity_plugin.get_chapter_url()

    def parse_chapter_download_links(self, url: str) -> list[str]:
        return self.entity_plugin.parse_chapter_download_links(url)

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
