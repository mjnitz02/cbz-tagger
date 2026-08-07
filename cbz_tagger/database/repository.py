"""Persistence seam for the entity database.

`EntityDB` used to be both the domain aggregate and its own storage layer: every mutation
ended in `save()`, which serialized the entire database and rewrote `entity_db.json`.

This module splits those apart. `DatabaseState` is the in-memory aggregate, and
`Repository` is the write surface — deliberately expressed as the individual mutation
points (`save_series`, `add_download`, `put_blob`, ...) rather than a single
`save(state)`, so a row store can write only what changed.

`JsonRepository` is the only implementation for now and it still rewrites the whole file
on every call, so behaviour is unchanged from `save()`.
"""

import json
import logging
import os
import tempfile
from abc import ABC
from abc import abstractmethod
from collections.abc import Iterable
from collections.abc import Iterator
from contextlib import contextmanager
from contextlib import suppress
from dataclasses import dataclass
from dataclasses import field

from cbz_tagger.common.plugins import Plugins
from cbz_tagger.database.author_entity_db import AuthorEntityDB
from cbz_tagger.database.base_db import BaseEntityDB
from cbz_tagger.database.chapter_entity_db import ChapterEntityDB
from cbz_tagger.database.cover_entity_db import CoverEntityDB
from cbz_tagger.database.downloads import DownloadLedger
from cbz_tagger.database.metadata_entity_db import MetadataEntityDB
from cbz_tagger.database.series import ChapterSource
from cbz_tagger.database.series import Series
from cbz_tagger.database.series import SeriesIndex
from cbz_tagger.database.volume_entity_db import VolumeEntityDB

logger = logging.getLogger()

ENTITY_DB_FILENAME = "entity_db.json"

# The five opaque provider-payload containers. `authors` is keyed by *author* id; the
# other four are keyed by series entity_id.
BLOB_KINDS = ("metadata", "covers", "authors", "volumes", "chapters")


@dataclass
class DatabaseState:
    """Everything the application persists, in memory."""

    series: SeriesIndex = field(default_factory=SeriesIndex)
    downloads: DownloadLedger = field(default_factory=DownloadLedger)
    metadata: MetadataEntityDB = field(default_factory=MetadataEntityDB)
    covers: CoverEntityDB = field(default_factory=CoverEntityDB)
    authors: AuthorEntityDB = field(default_factory=AuthorEntityDB)
    volumes: VolumeEntityDB = field(default_factory=VolumeEntityDB)
    chapters: ChapterEntityDB = field(default_factory=ChapterEntityDB)

    @classmethod
    def empty(cls) -> "DatabaseState":
        return cls()

    def blob_db(self, kind: str) -> BaseEntityDB:
        if kind not in BLOB_KINDS:
            raise KeyError(f"Unknown blob kind: {kind}")
        return getattr(self, kind)


def blob_payload(db: BaseEntityDB, key: str) -> str:
    """The stored payload for one blob, identical to the value `BaseEntityDB.to_json()`
    puts under that key."""
    value = db.database[key]
    if isinstance(value, list):
        return json.dumps([v.to_json() for v in value])
    return json.dumps(value.to_json())


def blob_from_payload(db: BaseEntityDB, payload: str):
    """Inverse of `blob_payload`, for a container of the same kind."""
    return db.entity_class.from_json(json.loads(payload))


def serialize_state(state: DatabaseState) -> str:
    """The legacy entity_db.json encoding. Moved verbatim from `EntityDB.to_json`."""
    entity_map = {}
    entity_names = {}
    entity_tracked = []
    entity_chapter_plugin = {}
    for series in state.series:
        entity_names[series.entity_id] = series.canonical_name
        for alias in series.aliases:
            entity_map[alias] = series.entity_id
        if series.tracked:
            entity_tracked.append(series.entity_id)
        # Only non-default sources are written, so the file stays legacy-compatible.
        if not series.source.is_default:
            entity_chapter_plugin[series.entity_id] = {
                "plugin_type": series.source.plugin_type,
                "plugin_id": series.source.plugin_id,
            }

    content = {
        "entity_map": entity_map,
        "entity_names": entity_names,
        "entity_downloads": state.downloads.as_tuples(),
        "entity_tracked": entity_tracked,
        "entity_chapter_plugin": entity_chapter_plugin,
        "metadata": state.metadata.to_json(),
        "covers": state.covers.to_json(),
        "authors": state.authors.to_json(),
        "volumes": state.volumes.to_json(),
        "chapters": state.chapters.to_json(),
    }
    return json.dumps(content)


def deserialize_state(json_data: str) -> DatabaseState:
    """Inverse of `serialize_state`. Moved verbatim from `EntityDB.from_json`."""
    content = json.loads(json_data)
    entity_map = content["entity_map"]
    entity_names = content["entity_names"]
    entity_tracked = set(content.get("entity_tracked", []))
    entity_chapter_plugin = content.get("entity_chapter_plugin", {})

    # Preserve insertion order of entity_map so `storage_name` keeps picking the same alias
    # that the old `next(iter(...))` scan in download_chapter picked.
    aliases_by_id: dict[str, list[str]] = {}
    for alias, entity_id in entity_map.items():
        aliases_by_id.setdefault(entity_id, []).append(alias)

    series_records = {}
    for entity_id in list(entity_map.values()) + list(entity_names.keys()):
        if entity_id in series_records:
            continue
        aliases = aliases_by_id.get(entity_id, [])
        canonical_name = entity_names.get(entity_id)
        if canonical_name is None:
            # Orphan: present in entity_map but never given a canonical name.
            logger.warning("Series %s has no canonical name; using its alias.", entity_id)
            canonical_name = aliases[0] if aliases else entity_id
        if not aliases:
            # Orphan: named but unreachable by any local name. Keep it so it is not silently
            # dropped, and give it an alias so storage_name stays valid.
            logger.warning("Series %s (%s) has no local name mapping.", canonical_name, entity_id)
            aliases = [canonical_name]
        plugin = entity_chapter_plugin.get(entity_id, {})
        series_records[entity_id] = Series(
            entity_id=entity_id,
            canonical_name=canonical_name,
            aliases=aliases,
            tracked=entity_id in entity_tracked,
            source=ChapterSource(
                plugin_type=plugin.get("plugin_type", Plugins.DEFAULT),
                plugin_id=plugin.get("plugin_id", entity_id),
            ),
        )

    return DatabaseState(
        series=SeriesIndex(series_records),
        downloads=DownloadLedger(set(tuple(item) for item in content.get("entity_downloads", []))),
        metadata=MetadataEntityDB.from_json(content["metadata"]),
        covers=CoverEntityDB.from_json(content["covers"]),
        authors=AuthorEntityDB.from_json(content["authors"]),
        volumes=VolumeEntityDB.from_json(content["volumes"]),
        chapters=ChapterEntityDB.from_json(content.get("chapters", "{}")),
    )


class Repository(ABC):
    """Where a `DatabaseState` lives.

    Granular writes are the interface on purpose. A `load()`/`save(state)` pair would buy
    nothing — a row store would still have to reserialize everything on each call.
    """

    def __init__(self) -> None:
        self._txn_depth = 0

    # -- lifecycle ---------------------------------------------------------
    @abstractmethod
    def open(self) -> DatabaseState:
        """The live state for this process. Called ONCE, by `EntityDB`.

        Implementations may retain the returned object — `JsonRepository` does, because it
        is what it serializes on every write. Never call this for a read-only view; use
        `snapshot()`.
        """

    @abstractmethod
    def snapshot(self) -> DatabaseState:
        """An independent, throwaway copy for read-only use. Never retained by the
        repository, never written back."""

    @abstractmethod
    def write_state(self, state: DatabaseState) -> None:
        """Replace everything with `state`.

        This does not rebind the live state returned by `open()`; it is a bulk write for
        migrations and for tests that build a state by hand.
        """

    def close(self) -> None:  # noqa: B027 - optional hook, most backends hold nothing
        """Release any resources. No-op unless an implementation needs it."""

    # -- unit of work ------------------------------------------------------
    @property
    def in_transaction(self) -> bool:
        return self._txn_depth > 0

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Reentrant. Granular writes inside are committed once, on exit of the outermost
        block, and discarded on exception. Granular writes outside a transaction commit
        immediately."""
        if self._txn_depth == 0:
            self._begin_transaction()
        self._txn_depth += 1
        try:
            yield
        except BaseException:
            self._txn_depth -= 1
            if self._txn_depth == 0:
                self._rollback_transaction()
            raise
        self._txn_depth -= 1
        if self._txn_depth == 0:
            self._commit_transaction()

    def _begin_transaction(self) -> None:  # noqa: B027 - optional hook
        """Hook, called when the outermost transaction opens."""

    def _commit_transaction(self) -> None:  # noqa: B027 - optional hook
        """Hook, called when the outermost transaction exits cleanly."""

    def _rollback_transaction(self) -> None:  # noqa: B027 - optional hook
        """Hook, called when the outermost transaction exits on an exception."""

    # -- granular writes ---------------------------------------------------
    @abstractmethod
    def save_series(self, series: Series) -> None:
        """Upsert the series row and replace its aliases."""

    @abstractmethod
    def delete_series(self, entity_id: str) -> None:
        """Remove the series row and its aliases."""

    @abstractmethod
    def add_download(self, entity_id: str, key: str) -> None: ...

    @abstractmethod
    def remove_download(self, entity_id: str, key: str) -> None: ...

    @abstractmethod
    def replace_downloads(self, entity_id: str, keys: Iterable[str]) -> None:
        """Make the stored download keys for this series exactly `keys`."""

    @abstractmethod
    def clear_downloads(self, entity_id: str) -> None: ...

    @abstractmethod
    def put_blob(self, kind: str, key: str, payload: str) -> None: ...

    @abstractmethod
    def delete_blob(self, kind: str, key: str) -> None: ...


class AliasingRepository(Repository):
    """Shared base for backends with no incremental write path.

    These retain the very `DatabaseState` object `EntityDB` mutates, so "persist this one
    series" degrades to "reserialize and rewrite everything" — which is exactly what
    `EntityDB.save()` did before this seam existed. Same I/O, same cost, same semantics.

    THIS ALIASING IS DELIBERATE. It is also why `snapshot()` must never be routed through
    `open()`: doing so would rebind the flush target to a throwaway object, and subsequent
    writes would persist the read copy instead of the live one.

    Rollback is therefore only partial: on an exception inside `transaction()` the pending
    write is dropped, but the in-memory state has already been mutated by the caller. A row
    store gets real rollback. This is acceptable because every transaction in `EntityDB`
    wraps mutations that either all succeed, or leave the process logging an error anyway.
    """

    def __init__(self) -> None:
        super().__init__()
        self._live_state: DatabaseState | None = None
        self._dirty = False

    def _flush(self) -> None:
        raise NotImplementedError

    def _touch(self) -> None:
        """Every granular write funnels here: the whole state is rewritten."""
        if self._live_state is None:
            raise RuntimeError("Repository was written to before open() was called.")
        if self.in_transaction:
            self._dirty = True
        else:
            self._flush()

    def _commit_transaction(self) -> None:
        if self._dirty:
            self._dirty = False
            self._flush()

    def _rollback_transaction(self) -> None:
        self._dirty = False

    # Every granular write is the same full rewrite. The arguments are ignored, and named
    # only to document the interface a row store will actually use.
    def save_series(self, series: Series) -> None:
        _ = series
        self._touch()

    def delete_series(self, entity_id: str) -> None:
        _ = entity_id
        self._touch()

    def add_download(self, entity_id: str, key: str) -> None:
        _ = (entity_id, key)
        self._touch()

    def remove_download(self, entity_id: str, key: str) -> None:
        _ = (entity_id, key)
        self._touch()

    def replace_downloads(self, entity_id: str, keys: Iterable[str]) -> None:
        _ = (entity_id, list(keys))
        self._touch()

    def clear_downloads(self, entity_id: str) -> None:
        _ = entity_id
        self._touch()

    def put_blob(self, kind: str, key: str, payload: str) -> None:
        _ = (kind, key, payload)
        self._touch()

    def delete_blob(self, kind: str, key: str) -> None:
        _ = (kind, key)
        self._touch()


class JsonRepository(AliasingRepository):
    """The legacy `entity_db.json` file, written atomically."""

    def __init__(self, root_path: str) -> None:
        super().__init__()
        self.root_path = root_path

    @property
    def path(self) -> str:
        return os.path.join(self.root_path, ENTITY_DB_FILENAME)

    def _read(self) -> DatabaseState:
        if not os.path.exists(self.path):
            return DatabaseState.empty()
        with open(self.path, "r", encoding="UTF-8") as read_file:
            return deserialize_state(read_file.read())

    def open(self) -> DatabaseState:
        self._live_state = self._read()
        return self._live_state

    def snapshot(self) -> DatabaseState:
        return self._read()

    def write_state(self, state: DatabaseState) -> None:
        self._write(serialize_state(state))

    def _flush(self) -> None:
        assert self._live_state is not None
        self._write(serialize_state(self._live_state))

    def _write(self, json_str: str) -> None:
        os.makedirs(self.root_path, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=self.root_path, prefix=".entity_db.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="UTF-8") as write_file:
                write_file.write(json_str)
                write_file.flush()
                os.fsync(write_file.fileno())
            os.replace(tmp_path, self.path)
        except BaseException:
            with suppress(OSError):
                os.unlink(tmp_path)
            raise
