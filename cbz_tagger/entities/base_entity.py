import json
from time import sleep
from typing import Any
from typing import Dict
from typing import List

import requests

from cbz_tagger.common.enums import MANGADEX_DELAY_PER_REQUEST
from cbz_tagger.common.helpers import unpaginate_request


class BaseEntityObject:
    base_url = "https://api.mangadex.org"


class BaseEntity(BaseEntityObject):
    entity_url: str
    paginated: bool = False

    def __init__(self, content):
        self.content = content

    def to_json(self):
        return json.dumps(self.content)

    @classmethod
    def from_json(cls, json_str: str):
        if isinstance(json_str, list):
            return [cls(json.loads(content)) for content in json_str]
        return cls(json.loads(json_str))

    @classmethod
    def from_server_url(cls, query_params=None):
        response = unpaginate_request(cls.entity_url, query_params)
        return [cls(data) for data in response]

    @property
    def entity_id(self) -> str:
        return self.content.get("id")

    @property
    def entity_type(self) -> str:
        return self.content.get("type")

    @property
    def attributes(self) -> Dict[str, Any]:
        return self.content.get("attributes", {})

    @property
    def relationships(self) -> List[Dict[str, str]]:
        return self.content.get("relationships", {})

    @staticmethod
    def download_file(url, retries=3):
        attempt = 0
        while attempt < retries:
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                sleep(MANGADEX_DELAY_PER_REQUEST)
                return response.content
            print(f"Error downloading {url}: {response.status_code}")
            attempt += 1

        raise EnvironmentError(f"Failed to download {url} after {retries} attempts")
