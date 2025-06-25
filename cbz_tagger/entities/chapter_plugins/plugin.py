from typing import Any

from cbz_tagger.entities.base_entity import BaseEntity


class ChapterPluginEntity(BaseEntity):
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
    def parse_info_feed(cls, entity_id: str) -> list[Any]:
        raise NotImplementedError

    def parse_chapter_download_links(self, url: str) -> list[str]:
        raise NotImplementedError
