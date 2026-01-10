import hashlib
import json
import logging
import random
import time
from json import JSONDecodeError
from typing import Any

import cloudscraper
import requests

from cbz_tagger.common.enums import Urls
from cbz_tagger.common.env import AppEnv

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
        response = cls.unpaginate_request(cls.entity_url, query_params)
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

    @classmethod
    def _get_request_configs(cls) -> list[dict]:
        """Generate different browser configurations to rotate through for better anti-detection."""
        return [
            {
                "browser": "chrome",
                "platform": "windows",
                "headers": {
                    "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                },
            },
            {
                "browser": "firefox",
                "platform": "darwin",
                "headers": {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                },
            },
            {
                "browser": "chrome",
                "platform": "darwin",
                "headers": {
                    "Accept": "application/json,text/html,application/xhtml+xml",
                    "Accept-Language": "en-GB,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                },
            },
        ]

    @classmethod
    def request_with_retry(cls, url, params=None, retries=3, timeout=30):
        """Enhanced request with browser fingerprinting rotation and improved 403 handling."""
        env = AppEnv()
        configs = cls._get_request_configs()

        for attempt in range(retries):
            try:
                # Rotate through different browser configurations
                config = configs[attempt % len(configs)]

                with cloudscraper.create_scraper(
                    browser={"browser": config["browser"], "platform": config["platform"], "mobile": False},
                    delay=10,  # Add delay between challenge solving attempts
                ) as scraper:
                    request_parameters = {
                        "url": url,
                        "params": params,
                        "timeout": timeout,
                        "headers": config["headers"],
                    }

                    if env.PROXY_URL is not None:
                        request_parameters["proxies"] = {"http": env.PROXY_URL, "https": env.PROXY_URL}

                    # Add random jitter to appear more human-like
                    time.sleep(random.uniform(0.5, 2.0))

                    response = scraper.get(**request_parameters)

                    if response.status_code == 200:
                        time.sleep(AppEnv.DELAY_PER_REQUEST)
                        return response
                    elif response.status_code == 403:
                        logger.warning(
                            "403 Forbidden on %s - switching browser config (attempt %s/%s)",
                            url,
                            attempt + 1,
                            retries,
                        )
                        # Longer backoff for 403s to let rate limits reset
                        time.sleep(15 * (attempt + 1))
                    else:
                        logger.error(
                            "Error downloading %s: %s. Attempt: %s/%s", url, response.status_code, attempt + 1, retries
                        )
                        time.sleep(10 * (attempt + 1))

            except requests.exceptions.Timeout:
                logger.error("Timeout downloading %s. Attempt: %s/%s", url, attempt + 1, retries)
                time.sleep(10 * (attempt + 1))
            except Exception as e:
                logger.error("Unexpected error downloading %s: %s. Attempt: %s/%s", url, str(e), attempt + 1, retries)
                time.sleep(10 * (attempt + 1))

        raise EnvironmentError(f"Failed to receive response from {url} after {retries} attempts")

    @classmethod
    def download_file(cls, url):
        return cls.request_with_retry(url).content

    @classmethod
    def unpaginate_request(cls, url, query_params=None, limit=100) -> list[dict[str, Any]]:
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
                    unique_ids = set(r["id"] for r in response_content)
                    if len(unique_ids) != len(response_content):
                        logger.warning(
                            "Paginated response contains duplicate entries. "
                            "Expected %s unique entries, got %s. "
                            "Removing duplicates.",
                            total,
                            len(unique_ids),
                        )
                        # Remove duplicates while preserving order
                        seen_ids = set()
                        deduplicated_content = []
                        for item in response_content:
                            if item["id"] not in seen_ids:
                                seen_ids.add(item["id"])
                                deduplicated_content.append(item)
                        response_content = deduplicated_content

                    return response_content

                # Only make 2 queries per second
                time.sleep(AppEnv.DELAY_PER_REQUEST)
        except JSONDecodeError as err:
            raise EnvironmentError("API is down! Please try again later!") from err
