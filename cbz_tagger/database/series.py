import logging
from collections.abc import Iterator

from pydantic import BaseModel
from pydantic import Field

from cbz_tagger.common.plugins import Plugins

logger = logging.getLogger()


class ChapterSource(BaseModel):
    """Where a series' chapters are fetched from.

    Always present on a Series. Previously this was an optional entry in
    entity_chapter_plugin, where absence implicitly meant "MangaDex, keyed by entity_id".
    """

    plugin_type: str = Plugins.DEFAULT
    plugin_id: str

    @property
    def is_default(self) -> bool:
        """True when this series is served by MangaDex under its own entity_id."""
        return self.plugin_type == Plugins.DEFAULT

    def to_update_kwargs(self) -> dict[str, str]:
        """Kwargs for ChapterEntityDB.update(). Empty for default sources, matching the
        legacy behaviour where no entity_chapter_plugin entry meant no kwargs."""
        if self.is_default:
            return {}
        return {"plugin_type": self.plugin_type, "plugin_id": self.plugin_id}


class Series(BaseModel):
    """One tracked manga series, keyed by its MangaDex entity_id."""

    entity_id: str
    canonical_name: str  # was entity_names[entity_id] — cleaned MangaDex title
    aliases: list[str] = Field(default_factory=list)  # was entity_map keys pointing here
    tracked: bool = False
    source: ChapterSource

    @property
    def storage_name(self) -> str:
        """The on-disk folder name. Preserves the legacy `next(iter(...))` behaviour of
        picking the first-inserted entity_map key for this entity_id."""
        return self.aliases[0]


class SeriesIndex:
    """Owns the Series records and a derived alias -> entity_id lookup.

    Replaces entity_map, entity_names, entity_tracked and entity_chapter_plugin.
    """

    def __init__(self, series: dict[str, Series] | None = None):
        self._series: dict[str, Series] = series if series is not None else {}
        self._alias_index: dict[str, str] = {}
        self._rebuild_alias_index()

    def _rebuild_alias_index(self) -> None:
        self._alias_index = {}
        for series in self._series.values():
            for alias in series.aliases:
                self._alias_index[alias] = series.entity_id

    # -- lookup -------------------------------------------------------------
    def __getitem__(self, entity_id: str) -> Series:
        return self._series[entity_id]

    def get(self, entity_id: str) -> Series | None:
        return self._series.get(entity_id)

    def __contains__(self, entity_id: object) -> bool:
        return entity_id in self._series

    def __len__(self) -> int:
        return len(self._series)

    def __iter__(self) -> Iterator[Series]:
        return iter(self._series.values())

    def entity_ids(self) -> list[str]:
        return list(self._series.keys())

    def by_alias(self, alias: str) -> Series | None:
        entity_id = self._alias_index.get(alias)
        return self._series.get(entity_id) if entity_id else None

    def aliases(self) -> list[str]:
        return list(self._alias_index.keys())

    def tracked(self) -> Iterator[Series]:
        return iter(s for s in self._series.values() if s.tracked)

    def has_tracked(self) -> bool:
        return any(s.tracked for s in self._series.values())

    # -- mutation -----------------------------------------------------------
    def add(self, series: Series) -> None:
        self._series[series.entity_id] = series
        for alias in series.aliases:
            self._alias_index[alias] = series.entity_id

    def add_alias(self, entity_id: str, alias: str) -> None:
        series = self._series[entity_id]
        if alias not in series.aliases:
            series.aliases.append(alias)
        self._alias_index[alias] = entity_id

    def remove(self, entity_id: str) -> Series | None:
        series = self._series.pop(entity_id, None)
        if series is not None:
            for alias in series.aliases:
                self._alias_index.pop(alias, None)
        return series
