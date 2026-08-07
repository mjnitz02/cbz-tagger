"""Repository conformance suite.

Every backend must behave identically here. The suite is parameterized by the `repository`
fixture in conftest.py, which is driven by `tests.support.repositories.REPOSITORY_BACKENDS`.

Note the shape of every write test: mutate the live state, *then* call the granular write.
That is what `EntityDB` does, and it is the only shape that works for both an aliasing
backend (which rewrites everything from the live state) and a row store (which writes only
what the call names).
"""

import os
from unittest import mock

import pytest

from cbz_tagger.database.repository import DatabaseState
from cbz_tagger.database.repository import blob_payload
from cbz_tagger.database.repository import deserialize_state
from cbz_tagger.database.repository import serialize_state
from cbz_tagger.database.series import ChapterSource
from cbz_tagger.database.series import Series


def _series(entity_id: str, *aliases: str, tracked: bool = False) -> Series:
    return Series(
        entity_id=entity_id,
        canonical_name=aliases[0] if aliases else entity_id,
        aliases=list(aliases),
        tracked=tracked,
        source=ChapterSource(plugin_id=entity_id),
    )


def _add_series(repository, state, series: Series) -> None:
    state.series.add(series)
    repository.save_series(series)


def _chapter(key: str):
    """A stand-in chapter whose ledger key is `key`, whichever attribute the ledger uses."""
    return mock.MagicMock(chapter_id=key, padded_chapter_string=key)


# -- lifecycle -------------------------------------------------------------
def test_open_on_an_empty_store_returns_empty_state(repository):
    state = repository.open()
    assert len(state.series) == 0
    assert len(state.downloads) == 0
    for kind in ("metadata", "covers", "authors", "volumes", "chapters"):
        assert len(state.blob_db(kind)) == 0


def test_write_state_then_open_round_trips_the_legacy_fixture(repository, tests_fixtures_path):
    with open(os.path.join(tests_fixtures_path, "entity_db_legacy.json"), encoding="UTF-8") as read_file:
        legacy = deserialize_state(read_file.read())

    repository.write_state(legacy)
    restored = repository.open()

    assert sorted(restored.series.entity_ids()) == sorted(legacy.series.entity_ids())
    assert set(restored.downloads.as_tuples()) == set(legacy.downloads.as_tuples())
    assert {s.entity_id for s in restored.series.tracked()} == {s.entity_id for s in legacy.series.tracked()}
    two = restored.series["22222222-2222-2222-2222-222222222222"]
    assert two.source.plugin_type == "wbc"
    assert two.source.plugin_id == "series-two-slug"


def test_write_state_fully_replaces(repository):
    state = repository.open()
    _add_series(repository, state, _series("entity-1", "One"))
    assert repository.snapshot().series.get("entity-1") is not None

    replacement = DatabaseState.empty()
    replacement.series.add(_series("entity-2", "Two"))
    repository.write_state(replacement)

    snapshot = repository.snapshot()
    assert snapshot.series.get("entity-1") is None
    assert snapshot.series.get("entity-2") is not None


# -- granular writes -------------------------------------------------------
def test_save_series_is_visible_in_snapshot(repository):
    state = repository.open()
    _add_series(repository, state, _series("entity-1", "Primary Alias", "Second Alias", tracked=True))

    restored = repository.snapshot().series["entity-1"]
    assert restored.tracked
    # aliases[0] is storage_name, so the order has to survive
    assert restored.aliases == ["Primary Alias", "Second Alias"]


def test_save_series_updates_an_existing_row(repository):
    state = repository.open()
    _add_series(repository, state, _series("entity-1", "One"))

    series = state.series["entity-1"]
    series.tracked = True
    series.source = ChapterSource(plugin_type="wbc", plugin_id="one-slug")
    repository.save_series(series)

    restored = repository.snapshot().series["entity-1"]
    assert restored.tracked
    assert restored.source.plugin_type == "wbc"
    assert restored.source.plugin_id == "one-slug"


def test_delete_series_is_visible_in_snapshot(repository):
    state = repository.open()
    _add_series(repository, state, _series("entity-1", "One"))
    _add_series(repository, state, _series("entity-2", "Two"))

    state.series.remove("entity-1")
    repository.delete_series("entity-1")

    snapshot = repository.snapshot()
    assert snapshot.series.get("entity-1") is None
    assert snapshot.series.by_alias("One") is None
    assert snapshot.series.get("entity-2") is not None


def test_add_and_remove_download(repository):
    state = repository.open()
    _add_series(repository, state, _series("entity-1", "One"))

    key = state.downloads.mark("entity-1", _chapter("001"))
    repository.add_download("entity-1", key)
    assert set(repository.snapshot().downloads.as_tuples()) == {("entity-1", "001")}

    key = state.downloads.unmark("entity-1", _chapter("001"))
    repository.remove_download("entity-1", key)
    assert set(repository.snapshot().downloads.as_tuples()) == set()


def test_replace_downloads_only_touches_one_series(repository):
    state = repository.open()
    state.downloads.mark_all("entity-1", [_chapter("001"), _chapter("002")])
    state.downloads.mark("entity-2", _chapter("010"))
    repository.replace_downloads("entity-1", ["001", "002"])
    repository.replace_downloads("entity-2", ["010"])

    state.downloads.clear_series("entity-1")
    state.downloads.mark("entity-1", _chapter("003"))
    repository.replace_downloads("entity-1", ["003"])

    assert set(repository.snapshot().downloads.as_tuples()) == {("entity-1", "003"), ("entity-2", "010")}


def test_clear_downloads_only_touches_one_series(repository):
    state = repository.open()
    state.downloads.mark("entity-1", _chapter("001"))
    state.downloads.mark("entity-2", _chapter("010"))
    repository.replace_downloads("entity-1", ["001"])
    repository.replace_downloads("entity-2", ["010"])

    state.downloads.clear_series("entity-1")
    repository.clear_downloads("entity-1")

    assert set(repository.snapshot().downloads.as_tuples()) == {("entity-2", "010")}


@pytest.mark.parametrize("kind", ["metadata", "covers", "authors", "volumes", "chapters"])
def test_put_and_delete_blob(
    repository,
    kind,
    mock_metadata_db,
    mock_cover_db,
    mock_author_db,
    mock_volume_db,
    mock_chapter_db,
):
    source = {
        "metadata": mock_metadata_db,
        "covers": mock_cover_db,
        "authors": mock_author_db,
        "volumes": mock_volume_db,
        "chapters": mock_chapter_db,
    }[kind]
    key = next(iter(source.database))

    state = repository.open()
    blob_db = state.blob_db(kind)
    blob_db.database[key] = source.database[key]
    repository.put_blob(kind, key, blob_payload(blob_db, key))

    assert repository.snapshot().blob_db(kind)[key] is not None

    blob_db.database.pop(key)
    repository.delete_blob(kind, key)
    assert repository.snapshot().blob_db(kind)[key] is None


def test_blob_kinds_are_independent(repository, mock_metadata_db, mock_chapter_db, manga_request_id):
    state = repository.open()
    state.metadata.database[manga_request_id] = mock_metadata_db[manga_request_id]
    repository.put_blob("metadata", manga_request_id, blob_payload(state.metadata, manga_request_id))
    state.chapters.database[manga_request_id] = mock_chapter_db[manga_request_id]
    repository.put_blob("chapters", manga_request_id, blob_payload(state.chapters, manga_request_id))

    state.metadata.database.pop(manga_request_id)
    repository.delete_blob("metadata", manga_request_id)

    snapshot = repository.snapshot()
    assert snapshot.metadata[manga_request_id] is None
    assert snapshot.chapters[manga_request_id] is not None


# -- transactions ----------------------------------------------------------
def test_transaction_batches_writes_into_one_visible_result(repository):
    state = repository.open()
    _add_series(repository, state, _series("entity-1", "One"))

    with repository.transaction():
        state.series["entity-1"].tracked = True
        repository.save_series(state.series["entity-1"])
        key = state.downloads.mark("entity-1", _chapter("001"))
        repository.add_download("entity-1", key)

        # Nothing is visible until the outermost block exits.
        mid = repository.snapshot()
        assert not mid.series["entity-1"].tracked
        assert set(mid.downloads.as_tuples()) == set()

    after = repository.snapshot()
    assert after.series["entity-1"].tracked
    assert set(after.downloads.as_tuples()) == {("entity-1", "001")}


def test_transaction_is_reentrant(repository):
    state = repository.open()

    with repository.transaction():
        _add_series(repository, state, _series("entity-1", "One"))
        with repository.transaction():
            _add_series(repository, state, _series("entity-2", "Two"))
            assert len(repository.snapshot().series) == 0
        # The inner block exiting must not commit.
        assert len(repository.snapshot().series) == 0

    assert len(repository.snapshot().series) == 2


def test_transaction_discards_its_writes_on_exception(repository):
    state = repository.open()
    _add_series(repository, state, _series("entity-1", "One"))

    with pytest.raises(RuntimeError):
        with repository.transaction():
            _add_series(repository, state, _series("entity-2", "Two"))
            raise RuntimeError("boom")

    snapshot = repository.snapshot()
    assert snapshot.series.get("entity-1") is not None
    assert snapshot.series.get("entity-2") is None


def test_writes_outside_a_transaction_commit_immediately(repository):
    state = repository.open()
    _add_series(repository, state, _series("entity-1", "One"))
    assert repository.snapshot().series.get("entity-1") is not None


def test_transaction_state_is_reset_after_an_exception(repository):
    state = repository.open()
    with pytest.raises(RuntimeError):
        with repository.transaction():
            raise RuntimeError("boom")

    assert not repository.in_transaction
    _add_series(repository, state, _series("entity-1", "One"))
    assert repository.snapshot().series.get("entity-1") is not None


# -- snapshots -------------------------------------------------------------
def test_snapshot_is_independent_of_the_live_state(repository):
    state = repository.open()
    _add_series(repository, state, _series("entity-1", "One"))

    snapshot = repository.snapshot()
    snapshot.series.add(_series("entity-2", "Two"))
    snapshot.series["entity-1"].tracked = True

    assert repository.snapshot().series.get("entity-2") is None
    assert not repository.snapshot().series["entity-1"].tracked
    assert not state.series["entity-1"].tracked


def test_snapshot_does_not_rebind_the_write_target(repository):
    """A read must never make later writes persist the read copy instead of the live one."""
    state = repository.open()
    _add_series(repository, state, _series("entity-1", "One"))

    repository.snapshot()

    state.series["entity-1"].tracked = True
    repository.save_series(state.series["entity-1"])
    assert repository.snapshot().series["entity-1"].tracked


def test_snapshot_matches_the_live_state_after_a_write(repository, mock_metadata_db, manga_request_id):
    state = repository.open()
    _add_series(repository, state, _series(manga_request_id, "One", tracked=True))
    state.metadata.database[manga_request_id] = mock_metadata_db[manga_request_id]
    repository.put_blob("metadata", manga_request_id, blob_payload(state.metadata, manga_request_id))

    assert serialize_state(repository.snapshot()) == serialize_state(state)
