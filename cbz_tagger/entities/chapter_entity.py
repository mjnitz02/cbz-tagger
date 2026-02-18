import logging
import os
from io import BytesIO
from typing import Any

from PIL import Image
from PIL import ImageFile

# Import plugins to trigger registration
import cbz_tagger.entities.chapter_plugins  # noqa: F401
from cbz_tagger.common.enums import Plugins
from cbz_tagger.entities.chapter_plugins.plugin import ChapterPluginEntity

logger = logging.getLogger()


class ChapterEntity(ChapterPluginEntity):
    @classmethod
    def from_server_url(cls, query_params=None, **kwargs):
        plugin_type = kwargs.get("plugin_type", Plugins.DEFAULT)

        if query_params is None:
            query_params = {}
        entity_id = query_params["ids[]"][0]
        if plugin_type != Plugins.DEFAULT:
            if "plugin_id" not in kwargs:
                raise EnvironmentError("plugin_id not provided")

            entity_id = kwargs["plugin_id"]
        plugin_cls = Plugins.get_plugin(plugin_type)
        response = plugin_cls.fetch_chapters(entity_id)
        return [cls(data) for data in response]

    @classmethod
    def parse_info_feed(cls, entity_id: str) -> list[Any]:
        raise NotImplementedError("ChapterEntity fetches via from_server_url")

    @property
    def entity_type(self):
        # Backwards compatibility for old chapter types
        if self.content.get("type", "") == "chapter":
            return Plugins.DEFAULT
        return self.content.get("type", Plugins.DEFAULT)

    @property
    def entity_plugin(self):
        return Plugins.get_plugin(self.entity_type)(self.content)

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
