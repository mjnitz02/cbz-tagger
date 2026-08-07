"""The no-missing-writes net.

For every mutating `EntityDB` method: mutate, take an independent `repository.snapshot()`,
and assert the change actually reached the store. Parameterized over every backend, so a
granular write that `EntityDB` forgets to make is caught by the row store even though the
aliasing JSON backend's full rewrite would hide it.
"""

from unittest import mock

import pytest

from cbz_tagger.database.entity_db import EntityDB
from cbz_tagger.database.series import ChapterSource
from cbz_tagger.database.series import Series


@pytest.fixture
def entity_db(repository):
    return EntityDB("unused-root", repository)


@pytest.fixture
def populated_entity_db(
    repository,
    manga_name,
    manga_request_id,
    mock_author_db,
    mock_cover_db,
    mock_metadata_db,
    mock_volume_db,
    mock_chapter_db,
):
    """An EntityDB whose live state is the repository's, with real entities in every
    container. Nothing has been persisted yet — the tests do that through EntityDB."""
    entity_db = EntityDB("unused-root", repository)
    entity_db.series.add(
        Series(
            entity_id=manga_request_id,
            canonical_name="Oshimai",
            aliases=[manga_name],
            source=ChapterSource(plugin_id=manga_request_id),
        )
    )
    entity_db.authors = mock_author_db
    entity_db.covers = mock_cover_db
    entity_db.metadata = mock_metadata_db
    entity_db.volumes = mock_volume_db
    entity_db.chapters = mock_chapter_db
    return entity_db


def _chapter(key: str):
    return mock.MagicMock(chapter_id=key, padded_chapter_string=key)


# -- add_entity ------------------------------------------------------------
def test_add_entity_persists_the_series(entity_db, repository, manga_request_id):
    entity_db.add_entity("Some Series", manga_request_id, update=False)

    restored = repository.snapshot().series.get(manga_request_id)
    assert restored is not None
    assert restored.canonical_name == "Some Series"
    assert restored.storage_name == "Some Series"


def test_add_entity_persists_the_series_before_the_update_runs(entity_db, repository, manga_request_id):
    """A failed metadata update must not lose the row that was just added."""

    def explode(_entity_id, update_metadata=True):
        raise EnvironmentError("API down")

    entity_db.update_manga_entity_id = explode
    with pytest.raises(EnvironmentError):
        entity_db.add_entity("Some Series", manga_request_id, update=True)

    assert repository.snapshot().series.get(manga_request_id) is not None


def test_add_entity_persists_tracking_and_the_source(entity_db, repository, manga_request_id):
    entity_db.add_entity(
        "Some Series",
        manga_request_id,
        update=False,
        track=True,
        backend={"plugin_type": "wbc", "plugin_id": "some-slug"},
    )

    restored = repository.snapshot().series[manga_request_id]
    assert restored.tracked
    assert restored.source.plugin_type == "wbc"
    assert restored.source.plugin_id == "some-slug"


def test_add_entity_persists_downloads_when_marking_all_tracked(
    entity_db, repository, manga_request_id, mock_chapter_db
):
    entity_db.chapters = mock_chapter_db
    expected = {(manga_request_id, c.chapter_id) for c in mock_chapter_db[manga_request_id]}

    entity_db.add_entity("Some Series", manga_request_id, update=False, track=True, mark_as_tracked=True)

    assert set(repository.snapshot().downloads.as_tuples()) == expected


# -- remove_entity_id_from_tracking ---------------------------------------
def test_remove_entity_id_from_tracking_persists(populated_entity_db, repository, manga_request_id):
    populated_entity_db.series[manga_request_id].tracked = True
    populated_entity_db.downloads.mark(manga_request_id, _chapter("001"))
    populated_entity_db.downloads.mark("other-entity", _chapter("010"))
    repository.write_state(populated_entity_db.state)

    populated_entity_db.remove_entity_id_from_tracking(manga_request_id)

    snapshot = repository.snapshot()
    assert not snapshot.series[manga_request_id].tracked
    assert set(snapshot.downloads.as_tuples()) == {("other-entity", "010")}


# -- delete_entity_id ------------------------------------------------------
def test_delete_entity_id_persists(populated_entity_db, repository, manga_request_id, manga_name):
    populated_entity_db.downloads.mark(manga_request_id, _chapter("001"))
    repository.write_state(populated_entity_db.state)

    populated_entity_db.delete_entity_id(manga_request_id, manga_name)

    snapshot = repository.snapshot()
    assert snapshot.series.get(manga_request_id) is None
    assert snapshot.series.by_alias(manga_name) is None
    assert set(snapshot.downloads.as_tuples()) == set()
    for kind in ("metadata", "covers", "volumes", "chapters"):
        assert snapshot.blob_db(kind)[manga_request_id] is None
    # Authors are shared between series and are deliberately never garbage collected.
    assert len(snapshot.authors) == 1


def test_delete_entity_id_is_a_single_unit_of_work(populated_entity_db, repository, manga_request_id, manga_name):
    repository.write_state(populated_entity_db.state)
    with mock.patch.object(repository, "_commit_transaction", wraps=repository._commit_transaction) as commit:
        populated_entity_db.delete_entity_id(manga_request_id, manga_name)
    assert commit.call_count == 1


# -- set_downloaded_chapters ----------------------------------------------
def test_set_downloaded_chapters_persists(populated_entity_db, repository, manga_request_id, mock_chapter_db):
    chapters = mock_chapter_db[manga_request_id]
    keep, drop = chapters[0], chapters[1]
    populated_entity_db.downloads.mark(manga_request_id, drop)
    repository.write_state(populated_entity_db.state)

    populated_entity_db.set_downloaded_chapters(manga_request_id, [keep.chapter_id])

    assert set(repository.snapshot().downloads.as_tuples()) == {(manga_request_id, keep.chapter_id)}


# -- update_manga_entity_id ------------------------------------------------
def test_update_manga_entity_id_persists_every_blob(populated_entity_db, repository, manga_request_id):
    for container in ("metadata", "chapters", "volumes", "covers", "authors"):
        getattr(populated_entity_db, container).update = mock.MagicMock()
    populated_entity_db.covers.download = mock.MagicMock()

    populated_entity_db.update_manga_entity_id(manga_request_id)

    snapshot = repository.snapshot()
    for kind in ("metadata", "covers", "volumes", "chapters"):
        assert snapshot.blob_db(kind)[manga_request_id] is not None, kind
    author_id = populated_entity_db.metadata[manga_request_id].author_id
    assert snapshot.authors[author_id] is not None


def test_update_manga_entity_id_drops_a_blob_the_series_no_longer_has(
    populated_entity_db, repository, manga_request_id
):
    for container in ("metadata", "chapters", "volumes", "covers", "authors"):
        getattr(populated_entity_db, container).update = mock.MagicMock()
    populated_entity_db.covers.download = mock.MagicMock()
    populated_entity_db.update_manga_entity_id(manga_request_id)
    assert repository.snapshot().volumes[manga_request_id] is not None

    populated_entity_db.volumes.database.pop(manga_request_id)
    populated_entity_db.update_manga_entity_id(manga_request_id)
    assert repository.snapshot().volumes[manga_request_id] is None


def test_update_manga_entity_id_persists_nothing_when_the_api_is_down(
    populated_entity_db, repository, manga_request_id
):
    populated_entity_db.metadata.update = mock.MagicMock(side_effect=EnvironmentError("API down"))
    populated_entity_db.update_manga_entity_id(manga_request_id)
    assert repository.snapshot().metadata[manga_request_id] is None


# -- download_chapter ------------------------------------------------------
@pytest.fixture
def downloadable_entity_db(populated_entity_db, repository_storage_path):
    entity_db = populated_entity_db
    entity_db.build_chapter_metadata = mock.MagicMock()
    entity_db.chapters.download = mock.MagicMock()
    entity_db.to_mylar_series_json = mock.MagicMock(return_value="{}")

    def build_cbz(chapter_filepath):
        with open(f"{chapter_filepath}.cbz", "w", encoding="UTF-8") as write_file:
            write_file.write("cbz")

    entity_db.build_chapter_cbz = mock.MagicMock(side_effect=build_cbz)
    return entity_db


def test_download_chapter_persists_the_download(
    downloadable_entity_db, repository, manga_request_id, mock_chapter_db, repository_storage_path
):
    chapter = mock_chapter_db[manga_request_id][0]
    downloadable_entity_db.download_chapter(manga_request_id, chapter, repository_storage_path)

    expected = downloadable_entity_db.downloads.keys_for(manga_request_id)
    assert expected  # the ledger recorded it, so the store must have too
    assert set(repository.snapshot().downloads.as_tuples()) == {(manga_request_id, key) for key in expected}


def test_download_chapter_persists_the_removal_on_failure(
    downloadable_entity_db, repository, manga_request_id, mock_chapter_db, repository_storage_path
):
    """A failure *after* the ledger entry is written must un-record it in the store too."""
    chapter = mock_chapter_db[manga_request_id][0]
    downloadable_entity_db.to_mylar_series_json = mock.MagicMock(side_effect=EnvironmentError("boom"))

    downloadable_entity_db.download_chapter(manga_request_id, chapter, repository_storage_path)

    assert downloadable_entity_db.downloads.keys_for(manga_request_id) == set()
    assert set(repository.snapshot().downloads.as_tuples()) == set()
