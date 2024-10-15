import json
from json import JSONDecodeError
from time import sleep
from typing import Any
from typing import Dict
from typing import List

import requests

from cbz_tagger.common.enums import DELAY_PER_REQUEST
from cbz_tagger.common.env import AppEnv


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
        response = cls.unpaginate_request(cls.entity_url, query_params)
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
    def request_with_retry(url, params=None, retries=3, timeout=30):
        env = AppEnv()

        attempt = 0
        while attempt < retries:
            try:
                if env.PROXY_URL is not None:
                    proxies = {"http": env.PROXY_URL, "https": env.PROXY_URL}
                    response = requests.get(url, params=params, proxies=proxies, timeout=timeout)
                else:
                    response = requests.get(url, params=params, timeout=timeout)
                if response.status_code == 200:
                    sleep(DELAY_PER_REQUEST)
                    return response
                # If the status code wasn't success, retry
                attempt += 1
                print(f"Error downloading {url}: {response.status_code}. Attempt: {attempt}")
                sleep(5 * attempt)
            # If the request times out, retry
            except requests.exceptions.Timeout:
                attempt += 1
                print(f"Error downloading {url}. Attempt: {attempt}")
                sleep(5 * attempt)

        raise EnvironmentError(f"Failed to receive response from {url} after {retries} attempts")

    @classmethod
    def download_file(cls, url):
        return cls.request_with_retry(url).content

    @classmethod
    def unpaginate_request(cls, url, query_params=None, limit=100) -> List[Dict[str, Any]]:
        if query_params is None:
            query_params = {}

        response_content = []
        offset = 0
        total = None
        try:
            while True:
                params = {"limit": limit, "offset": offset}
                params.update(query_params)

                response = cls.request_with_retry(url, params=params)
                response_json = response.json()
                if total is None:
                    total = response_json["total"]

                response_content.extend(response_json["data"])

                offset += limit
                if offset >= response_json["total"]:
                    # This is a deep sanity check to ensure the uniqueness of the retrieved IDs.
                    # Some endpoints with specific settings may return non-deterministic responses :(
                    if len(set(r["id"] for r in response_content)) != total:
                        raise EnvironmentError("Paginated response contains duplicate entries")
                    return response_content

                # Only make 2 queries per second
                sleep(DELAY_PER_REQUEST)
        except JSONDecodeError as err:
            raise EnvironmentError("API is down! Please try again later!") from err
