import hashlib
import json
import logging
from typing import Any

from cbz_tagger.common.enums import Urls
from cbz_tagger.common.http_client import unpaginate_request

logger = logging.getLogger()


class BaseEntityObject:
    base_url = f"https://api.{Urls.MDX}"


class BaseEntity(BaseEntityObject):
    entity_url: str
    paginated: bool = False

    def __init__(self, content):
        self.content = content

    def to_json(self):
        return json.dumps(self.content)

    def to_hash(self) -> str:
        """
        Returns a hash of the entity content.
        This is useful for comparing entities or checking if they have changed.
        """
        sha_1 = hashlib.sha1()
        sha_1.update(json.dumps(self.content, sort_keys=True).encode("utf-8"))
        return sha_1.hexdigest()

    @classmethod
    def from_json(cls, json_str: str):
        if isinstance(json_str, list):
            return [cls(json.loads(content)) for content in json_str]
        return cls(json.loads(json_str))

    @classmethod
    def from_server_url(cls, query_params: dict | None = None, **kwargs):
        _ = kwargs
        if query_params is None:
            query_params = {}
        response = unpaginate_request(cls.entity_url, query_params)
        return [cls(data) for data in response]

    @property
    def entity_id(self) -> str:
        return self.content.get("id")

    @property
    def entity_type(self) -> str:
        return self.content.get("type")

    @property
    def attributes(self) -> dict[str, Any]:
        return self.content.get("attributes", {})

    @property
    def relationships(self) -> list[dict[str, str]]:
        return self.content.get("relationships", {})
