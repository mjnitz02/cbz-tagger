import logging
from collections.abc import Iterable

logger = logging.getLogger()


class DownloadLedger:
    """Records which chapters have been successfully written to disk.

    Replaces the bare `entity_downloads` set of (entity_id, plugin_chapter_id) tuples.

    IMPORTANT: every method takes a *chapter object*, never a bare chapter id. The key
    stored internally is an implementation detail of this class. Step 5 changes that key
    from `chapter.chapter_id` (a plugin transport handle) to `chapter.padded_chapter_string`
    (the real domain identity, and the name of the file on disk) without touching any caller.

    In step 1 the key is unchanged, so behaviour is identical to today.
    """

    def __init__(self, downloads: set[tuple[str, str]] | None = None):
        self._downloads: set[tuple[str, str]] = downloads if downloads is not None else set()

    @staticmethod
    def _key(chapter) -> str:
        # STEP 5: becomes `return chapter.padded_chapter_string`
        return chapter.chapter_id

    # -- queries ------------------------------------------------------------
    def has(self, entity_id: str, chapter) -> bool:
        return (entity_id, self._key(chapter)) in self._downloads

    def count_for(self, entity_id: str) -> int:
        return sum(1 for (e, _) in self._downloads if e == entity_id)

    def __len__(self) -> int:
        return len(self._downloads)

    def as_tuples(self) -> list[tuple[str, str]]:
        """Serialization escape hatch. Only EntityDB.to_json may call this."""
        return [tuple(item) for item in self._downloads]

    # -- mutation -----------------------------------------------------------
    def mark(self, entity_id: str, chapter) -> None:
        self._downloads.add((entity_id, self._key(chapter)))

    def unmark(self, entity_id: str, chapter) -> None:
        self._downloads.discard((entity_id, self._key(chapter)))

    def mark_all(self, entity_id: str, chapters: Iterable) -> None:
        self._downloads.update((entity_id, self._key(c)) for c in chapters)

    def clear_series(self, entity_id: str) -> None:
        for key in [k for k in self._downloads if k[0] == entity_id]:
            self._downloads.discard(key)

    def reconcile(self, entity_id: str, known_chapters: Iterable, desired_keys: Iterable[str]) -> None:
        """Make the ledger for `entity_id` match `desired_keys`, restricted to chapters the
        database actually knows about. Chapters outside `known_chapters` are left untouched.

        STEP 5: `desired_keys` becomes padded chapter numbers rather than chapter ids. This
        is the only method whose external contract changes, because it is driven by the
        frontend checkbox list via PUT /api/scanner/series/{id}/downloads.
        """
        known = {self._key(c) for c in known_chapters}
        desired = set(desired_keys) & known
        current = {k for (e, k) in self._downloads if e == entity_id}
        for key in desired - current:
            self._downloads.add((entity_id, key))
        for key in (current & known) - desired:
            self._downloads.discard((entity_id, key))
