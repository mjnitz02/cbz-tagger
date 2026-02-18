import logging
from typing import Any

# Import plugins to trigger registration
import cbz_tagger.entities.plugins  # noqa: F401
from cbz_tagger.common.enums import Plugins
from cbz_tagger.entities.plugins.plugin import ChapterPluginEntity

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
