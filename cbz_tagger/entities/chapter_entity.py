import hashlib
import json
import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator

from cbz_tagger.common.plugins import Plugins

logger = logging.getLogger()


class ChapterEntity(BaseModel):
    """One chapter, as the application understands it.

    This is the real internal type. Plugins produce these directly instead of
    hand-building dicts shaped like MangaDex API responses, and MangaDex is now
    adapted into this shape by `ChapterPluginMDX` like every other source.

    The legacy MangaDex-shaped dict survives only as the on-disk encoding, in
    `to_content()` / `from_content()`. It disappears when storage moves to SQLite.
    """

    # Unknown fields from a dirty upstream feed are kept rather than rejected, so a
    # provider adding a key can never take the application down.
    model_config = ConfigDict(extra="allow")

    chapter_id: str
    plugin_type: str = Plugins.DEFAULT
    title: str | None = None
    url: str | None = None
    chapter: str | None = None
    translated_language: str | None = "en"
    pages: int = -1
    volume: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    scanlation_group_id: str | None = None

    @field_validator("pages", mode="before")
    @classmethod
    def _default_pages(cls, value):
        # -1 means "the source did not tell us"; download_chapter treats it as unknown.
        return -1 if value is None else value

    @field_validator("chapter", "volume", mode="before")
    @classmethod
    def _stringify(cls, value):
        # Sources are inconsistent about numeric vs string chapter/volume values.
        return value if value is None else str(value)

    # -- plugin dispatch ----------------------------------------------------
    @property
    def plugin(self):
        return Plugins.get_plugin(self.plugin_type)

    def get_chapter_url(self) -> str:
        return self.plugin.get_chapter_url(self)

    def parse_chapter_download_links(self, url: str) -> list[str]:
        return self.plugin.parse_chapter_download_links(self, url)

    def download_chapter(self, filepath: str) -> list[str]:
        return self.plugin.download_chapter(self, filepath)

    @classmethod
    def from_server_url(cls, query_params=None, **kwargs) -> list["ChapterEntity"]:
        plugin_type = kwargs.get("plugin_type", Plugins.DEFAULT)

        if query_params is None:
            query_params = {}
        entity_id = query_params["ids[]"][0]
        if plugin_type != Plugins.DEFAULT:
            if "plugin_id" not in kwargs:
                raise EnvironmentError("plugin_id not provided")

            entity_id = kwargs["plugin_id"]
        return Plugins.get_plugin(plugin_type).fetch_chapters(entity_id)

    # -- parsed values ------------------------------------------------------
    @property
    def scanlation_group(self) -> str:
        if self.scanlation_group_id is None:
            return "none"
        return self.scanlation_group_id.lower()

    @property
    def chapter_number(self) -> float | None:
        chapter = str(self.chapter or "")
        if not chapter:
            return None
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
        chapter_number = self.chapter_number
        if chapter_number is None:
            return str(chapter_number)
        if chapter_number.is_integer():
            return f"{int(chapter_number)}"
        return f"{chapter_number}"

    @property
    def padded_chapter_string(self) -> str:
        chapter_number = self.chapter_number
        if chapter_number is None:
            return str(chapter_number)
        if chapter_number.is_integer():
            return f"{int(chapter_number):03}"
        decimal_size = len(str(chapter_number).split(".", maxsplit=1)[-1])
        if decimal_size == 2:
            return f"{chapter_number:06.2f}"
        if decimal_size == 3:
            return f"{chapter_number:07.3f}"
        return f"{chapter_number:05.1f}"

    @property
    def volume_number(self) -> float | None:
        if self.volume is None:
            return None
        return float(self.volume)

    @property
    def updated(self) -> str | None:
        return self.updated_at

    @property
    def updated_date(self) -> datetime | None:
        if self.updated_at is None:
            return None
        try:
            return datetime.fromisoformat(self.updated_at)
        except ValueError:
            return datetime.strptime(self.updated_at, "%a, %d %b %Y %H:%M:%S %z")

    # -- storage encoding ---------------------------------------------------
    def to_content(self) -> dict[str, Any]:
        """The legacy MangaDex-shaped dict written to entity_db.json."""
        return {
            "id": self.chapter_id,
            "type": self.plugin_type,
            "attributes": {
                "title": self.title,
                "url": self.url,
                "chapter": self.chapter,
                "translatedLanguage": self.translated_language,
                "pages": self.pages,
                "volume": self.volume,
                "createdAt": self.created_at,
                "updatedAt": self.updated_at,
            },
            "relationships": [{"type": "scanlation_group", "id": self.scanlation_group_id}],
        }

    @classmethod
    def from_content(cls, content: dict[str, Any]) -> "ChapterEntity":
        """Read the legacy MangaDex-shaped dict, from disk or straight from the MDX API."""
        attributes = content.get("attributes") or {}
        relationships = content.get("relationships") or []
        group = next((rel for rel in relationships if rel.get("type") == "scanlation_group"), {})
        pages = attributes.get("pages")

        plugin_type = content.get("type") or Plugins.DEFAULT
        if plugin_type == "chapter":
            # MangaDex's own `type` field, as stored by older versions of this database.
            plugin_type = Plugins.DEFAULT

        return cls(
            chapter_id=content["id"],
            plugin_type=plugin_type,
            title=attributes.get("title"),
            url=attributes.get("url"),
            chapter=attributes.get("chapter"),
            translated_language=attributes.get("translatedLanguage"),
            pages=-1 if pages is None else pages,
            volume=attributes.get("volume"),
            created_at=attributes.get("createdAt"),
            updated_at=attributes.get("updatedAt"),
            scanlation_group_id=group.get("id"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_content())

    @classmethod
    def from_json(cls, json_str):
        if isinstance(json_str, list):
            return [cls.from_content(json.loads(content)) for content in json_str]
        return cls.from_content(json.loads(json_str))

    def to_hash(self) -> str:
        sha_1 = hashlib.sha1()
        sha_1.update(json.dumps(self.to_content(), sort_keys=True).encode("utf-8"))
        return sha_1.hexdigest()
