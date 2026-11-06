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
    # Whether requests from this class go through cloudscraper with rotating browser
    # headers. Off by default: a plain client with an honest User-Agent is what most
    # APIs expect, and some now gate browser-looking traffic behind a JS challenge
    # that cloudscraper cannot solve (MangaDex since 2026-11-01). A source that sits
    # behind a Cloudflare challenge sets this to True on its class.
    CLOUDSCRAPER: bool = False

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
        """Generate different browser configurations to rotate through for better anti-detection.

        cloudscraper's bundled fake-user-agent pool is stuck on ~2016-2017 browser builds
        (some tagged with QQBrowser/UBrowser strings), which modern WAFs increasingly flag
        with 400s. Pin explicit, current desktop User-Agents here instead of relying on
        cloudscraper's auto-generated ones.
        """
        return [
            {
                "browser": "chrome",
                "platform": "windows",
                "headers": {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                    ),
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-site",
                    "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24", "Google Chrome";v="131"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                },
            },
            {
                "browser": "chrome",
                "platform": "darwin",
                "headers": {
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                    ),
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-site",
                    "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24", "Google Chrome";v="131"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"macOS"',
                },
            },
            {
                "browser": "firefox",
                "platform": "windows",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-site",
                },
            },
        ]

    @classmethod
    def user_agent(cls) -> str:
        return f"cbz-tagger/{AppEnv.VERSION} (+https://github.com/mjnitz02/cbz-tagger)"

    @classmethod
    def _create_session(cls, attempt: int) -> tuple[requests.Session, dict[str, str]]:
        """Return the session and base headers for one attempt.

        With CLOUDSCRAPER set, each attempt rotates to the next browser configuration;
        otherwise it is a plain requests session that identifies itself honestly.
        """
        if not cls.CLOUDSCRAPER:
            return requests.Session(), {"User-Agent": cls.user_agent()}
        configs = cls._get_request_configs()
        config = configs[attempt % len(configs)]
        scraper = cloudscraper.create_scraper(
            browser={"browser": config["browser"], "platform": config["platform"], "mobile": False},
            delay=10,  # Add delay between challenge solving attempts
        )
        return scraper, config["headers"]

    @classmethod
    def request_with_retry(cls, url, params=None, retries=3, timeout=30, headers=None):
        """GET with retries and backoff; see CLOUDSCRAPER for how the request is made.

        Args:
            headers: Extra headers merged over the base headers (e.g. a Referer)
        """
        env = AppEnv()

        for attempt in range(retries):
            try:
                session, base_headers = cls._create_session(attempt)
                with session as scraper:
                    proxies = None
                    if env.PROXY_URL is not None:
                        proxies = {"http": env.PROXY_URL, "https": env.PROXY_URL}

                    # Add random jitter to appear more human-like
                    time.sleep(random.uniform(0.5, 2.0))

                    response = scraper.get(
                        url,
                        params=params,
                        timeout=timeout,
                        headers={**base_headers, **(headers or {})},
                        proxies=proxies,
                    )

                    if response.status_code == 200:
                        time.sleep(AppEnv.DELAY_PER_REQUEST)
                        return response
                    elif response.status_code == 403:
                        logger.warning(
                            "403 Forbidden on %s (attempt %s/%s)",
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

        raise OSError(f"Failed to receive response from {url} after {retries} attempts")

    @classmethod
    def download_file(cls, url, headers=None):
        return cls.request_with_retry(url, headers=headers).content

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
            raise OSError("API is down! Please try again later!") from err
