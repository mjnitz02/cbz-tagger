import base64
from datetime import UTC
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit

from cbz_tagger.common.plugins import Plugins
from cbz_tagger.entities.plugins.plugin_entity import ChapterPluginEntity


@Plugins.register("mfi")
class ChapterPluginMFI(ChapterPluginEntity):
    """Chapter plugin backed by the site's JSON API.

    The plugin_id is the title's short id from its URL (e.g. "1abc2" from /title/1abc2-some-slug);
    the full "1abc2-some-slug" form is accepted too.
    """

    BASE_URL = base64.b64decode("bWFuZ2FmaXJlLnRv").decode("utf-8")
    TITLE_URL = f"https://{BASE_URL}/title/"
    HARU_SOURCE = base64.b64decode("TWFuZ2FGaXJlLnRz").decode("utf-8")
    IMAGE_HEADERS = {"Referer": f"https://{BASE_URL}/"}  # The image CDN returns 403 without it
    api_url = f"https://{BASE_URL}/api"
    language = "en"
    page_limit = 200

    # Every API request must carry a `vrf` signature: three byte-substitution stages over the request path and
    # sorted query. Copied from HARU_SOURCE (STAGE_DATA / ComputeVrf). If every API call starts failing
    # with 403 "Missing token.", the site has rotated these tables; re-copy them from upstream.
    VRF_STAGES: list[tuple[str, str, int]] = [
        (
            "yINlmUNho8VYJT+ibTIP+9ESiULpVEtMOoD6U6lRE0R/xwXo/Xp9NrUgC4cw/Lmo33vUyjUE40kUoEWIr/fxfNNcq2s79ShQ5NhNrFnJ"
            "4hXPwOu/SuXzIbuTQKGFvfm08E9jvCfqAtoDqvQq3dVWPQFmJjgvkISBeXY3BgANR+yVnjGbcxZ47d6kLNfZPIayTq3/YGySb1KuVZod"
            "Wp/WGNAO5pfMcpaK53Hhs0allBszaMaxuouOwdxbwgxIw6YunSsXjI05Yi0j9j4eHKfSXR8Ifo/Od+8iamRfCXTyvm7NGRGYdcQ0ywcK"
            "/u6RXhrbcCm4t2eCtrDgQVecJGkQ+A==",
            "0Ec58JOY3uBzJK9m3zqIOpdlF7UFiax9DmA=",
            0x5A,
        ),
        (
            "IUFltCxD3Oc2cwCgkJffthaOg9cgPUb0LgW6H/VtfcF0kc5F25t+aWj6JH9VOhOaY0rAFdUxlDnl5BLNvwEJvQtP5qcw7vdb/K+chnbw"
            "nspSHT8mz5lqwz41TezG0hkO06FTjJZhsyNuFLDpD2ZZxQj/QIRcF90zpmQ7Byu483WsQqUE0C342HL+JXngRB6fRzxRyVTaKu83h7UY"
            "TJ0QMt6ixFh6S3F8gqkKwrGTL3jHNBsD45UnifK8+RGtishQV2K3rujLKEkiZxpr2dYcudFW4oFsDKhad3CLBvuyTqsCo4B7mL5IKQ1v"
            "Xo/MOOvq1I1d8ar9X6Ttu5KF4fZgiA==",
            "AAdjb1iPY8CiDmq9H34tKTBF8a3oDQ==",
            0x35,
        ),
        (
            "NQHlu1/wVO5EmkwQymF810qqY2xG1k2obcas4Z9mCsPEIFl9pRIjFxbJ7ybMHbBckT5Ton85E0FOeHezbh/mjlEYpmpnlXOS8dgrqeq2"
            "KfxImTh1YK9y0PeMNhzA1OQzSY9brYOJq/l2QnE/hwOeZIhPixVSKIUlDb5vLcH6RWKxkIEMuP0bDwIqQ71AJJaEaMJL7A6YtyIwoRT+"
            "L5v4aZzodN/0+3nOGsfblFjgxSfPzVDjNFeNl5P26+kEC/8AHgdrpAbt3hHz3HrRN1Y6e+JHgF7ncFWnoF0y3THL1S71WgWGCa6KtSzT"
            "CCG58n68nTyj2T3Sshk7utqCtMi/ZQ==",
            "DELOJgPsVaCcblDtTGMdHzM=",
            0xBA,
        ),
    ]

    @classmethod
    def compute_vrf(cls, path: str, params: dict[str, Any] | None = None) -> str:
        """Sign an API request; `path` is relative to the API root (e.g. "/titles/abc/chapters").

        The server signs the decoded query (e.g. `keyword=a b`), so values are joined raw rather than URL-encoded.
        """
        query = "&".join(f"{key}={value}" for key, value in sorted((params or {}).items()))
        data = f"{path}?{query}".encode() if query else path.encode()
        for table_b64, key_b64, previous in cls.VRF_STAGES:
            table = base64.b64decode(table_b64)
            key = base64.b64decode(key_b64)
            output = bytearray()
            for index, byte in enumerate(data):
                previous = table[byte ^ key[index % len(key)] ^ previous]
                output.append(previous)
            data = bytes(output)
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    @classmethod
    def request_api(cls, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = params or {}
        response = cls.request_with_retry(
            f"{cls.api_url}{path}", params={**params, "vrf": cls.compute_vrf(path, params)}
        )
        return response.json()

    @classmethod
    def parse_info_feed(cls, entity_id: str) -> list[Any]:
        title_id = entity_id.split("-", maxsplit=1)[0]

        items = []
        page = 1
        while True:
            response = cls.request_api(
                f"/titles/{title_id}/chapters",
                {"sort": "number", "order": "desc", "page": page, "limit": cls.page_limit},
            )
            items.extend(response["items"])
            if not response["items"] or not response.get("meta", {}).get("hasNext"):
                break
            page += 1

        content = []
        for item in items:
            # The same chapter number is listed once per language and per release type (official/unofficial)
            if item["language"] != cls.language:
                continue
            name = (item.get("name") or "").strip()
            created = datetime.fromtimestamp(item["createdAt"], tz=UTC).isoformat() if item.get("createdAt") else None
            content.append(
                cls.ResponseBuilder.build(
                    cls.build_chapter_data(
                        chapter_id=f"{title_id}-{item['id']}",
                        entity_id=entity_id,
                        title=f"Chapter {item['number']}: {name}" if name else f"Chapter {item['number']}",
                        url=f"{cls.api_url}/chapters/{item['id']}",
                        chapter=str(item["number"]),
                        created_at=created,
                        updated_at=created,
                        scanlation_group=item.get("type"),
                    )
                )
            )
        return content

    def parse_chapter_download_links(self, url: str) -> list[str]:
        # Stored chapter URLs are unsigned, so they keep working after the signing tables are updated
        path = urlsplit(url).path.removeprefix("/api")
        response = self.request_api(path)
        return [page["url"] for page in response["data"]["pages"]]
