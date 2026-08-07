"""An in-memory `Repository` for tests that must not touch the filesystem."""

from collections.abc import Iterable

from cbz_tagger.database.repository import AliasingRepository
from cbz_tagger.database.repository import DatabaseState
from cbz_tagger.database.repository import deserialize_state
from cbz_tagger.database.repository import serialize_state


class MemoryRepository(AliasingRepository):
    """The drop-in for fixtures that used to stub out `EntityDB.save`.

    It holds the live state and nothing else — a "flush" only bumps `flush_count`. That
    keeps it usable by the many fixtures that put `MagicMock`s into the blob containers,
    which cannot be serialized.

    The consequence is that `snapshot()` returns an independent copy of the state *as it
    is now*, not as of the last flush. Tests that care about real write semantics should
    use `JsonRepository` (see `test_repository.py` and `test_entity_db_persistence.py`).

    Every granular call is recorded in `calls`, which is what tests that used to assert
    `entity_db.save.assert_called()` should assert on instead.
    """

    def __init__(self, initial_state: DatabaseState | None = None) -> None:
        super().__init__()
        self._live_state = initial_state if initial_state is not None else DatabaseState.empty()
        self.calls: list[tuple] = []
        self.flush_count = 0

    # -- lifecycle ---------------------------------------------------------
    def open(self) -> DatabaseState:
        assert self._live_state is not None
        return self._live_state

    def snapshot(self) -> DatabaseState:
        assert self._live_state is not None
        return deserialize_state(serialize_state(self._live_state))

    def write_state(self, state: DatabaseState) -> None:
        self._live_state = state

    def _flush(self) -> None:
        self.flush_count += 1

    # -- call recording ----------------------------------------------------
    def save_series(self, series) -> None:
        self.calls.append(("save_series", series.entity_id))
        super().save_series(series)

    def delete_series(self, entity_id: str) -> None:
        self.calls.append(("delete_series", entity_id))
        super().delete_series(entity_id)

    def add_download(self, entity_id: str, key: str) -> None:
        self.calls.append(("add_download", entity_id, key))
        super().add_download(entity_id, key)

    def remove_download(self, entity_id: str, key: str) -> None:
        self.calls.append(("remove_download", entity_id, key))
        super().remove_download(entity_id, key)

    def replace_downloads(self, entity_id: str, keys: Iterable[str]) -> None:
        keys = sorted(keys)
        self.calls.append(("replace_downloads", entity_id, tuple(keys)))
        super().replace_downloads(entity_id, keys)

    def clear_downloads(self, entity_id: str) -> None:
        self.calls.append(("clear_downloads", entity_id))
        super().clear_downloads(entity_id)

    def put_blob(self, kind: str, key: str, payload: str) -> None:
        self.calls.append(("put_blob", kind, key))
        super().put_blob(kind, key, payload)

    def delete_blob(self, kind: str, key: str) -> None:
        self.calls.append(("delete_blob", kind, key))
        super().delete_blob(kind, key)

    # -- assertions --------------------------------------------------------
    def call_names(self) -> list[str]:
        return [call[0] for call in self.calls]

    def wrote(self) -> bool:
        """True if anything was actually persisted (i.e. a flush happened)."""
        return self.flush_count > 0
