"""The legacy entity_db.json encoding, which now lives in JsonRepository.

These tests moved out of test_entity_db.py when EntityDB.to_json/from_json/save were
replaced by the repository seam. The on-disk format is unchanged.
"""

import json
import os

from cbz_tagger.database.repository import DatabaseState
from cbz_tagger.database.repository import JsonRepository
from cbz_tagger.database.repository import deserialize_state
from cbz_tagger.database.repository import serialize_state


def _entity_map(state: DatabaseState):
    return {s.storage_name: s.entity_id for s in state.series}


def _entity_names(state: DatabaseState):
    return {s.entity_id: s.canonical_name for s in state.series}


def test_serialize_round_trip_is_stable(mock_entity_db, manga_request_id):
    json_str = serialize_state(mock_entity_db.state)
    restored = deserialize_state(json_str)

    assert _entity_map(restored) == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
    assert _entity_names(restored) == {manga_request_id: "Oshimai"}
    assert len(restored.authors) == 1
    assert len(restored.covers) == 1
    assert len(restored.metadata) == 1
    assert len(restored.volumes) == 1
    assert len(restored.chapters) == 1

    assert serialize_state(restored) == json_str


def test_deserialize_is_backwards_compatible(mock_entity_db, manga_request_id):
    """A pre-downloads, pre-chapters database still loads."""
    legacy_json_dump = json.dumps(
        {
            "entity_map": _entity_map(mock_entity_db.state),
            "entity_names": _entity_names(mock_entity_db.state),
            "metadata": mock_entity_db.metadata.to_json(),
            "covers": mock_entity_db.covers.to_json(),
            "authors": mock_entity_db.authors.to_json(),
            "volumes": mock_entity_db.volumes.to_json(),
        }
    )

    restored = deserialize_state(legacy_json_dump)
    assert _entity_map(restored) == {"Kanojyo to Himitsu to Koimoyou": manga_request_id}
    assert _entity_names(restored) == {manga_request_id: "Oshimai"}
    assert len(restored.authors) == 1
    assert len(restored.covers) == 1
    assert len(restored.metadata) == 1
    assert len(restored.volumes) == 1
    assert len(restored.chapters) == 0
    assert len(restored.downloads) == 0
    assert not restored.series.has_tracked()


def test_json_round_trip_is_unchanged(tests_fixtures_path):
    with open(os.path.join(tests_fixtures_path, "entity_db_legacy.json"), encoding="UTF-8") as read_file:
        original = read_file.read()

    def normalize(payload: str) -> dict:
        content = json.loads(payload)
        content["entity_downloads"] = sorted(tuple(x) for x in content["entity_downloads"])
        content["entity_tracked"] = sorted(content["entity_tracked"])
        return content

    assert normalize(serialize_state(deserialize_state(original))) == normalize(original)


def test_deserialize_recovers_a_series_with_no_canonical_name(caplog):
    payload = json.dumps(
        {
            "entity_map": {"Only Alias": "entity-1"},
            "entity_names": {},
            "metadata": "{}",
            "covers": "{}",
            "authors": "{}",
            "volumes": "{}",
        }
    )
    state = deserialize_state(payload)
    assert state.series["entity-1"].canonical_name == "Only Alias"
    assert "has no canonical name" in caplog.text


def test_deserialize_recovers_a_series_with_no_alias(caplog):
    payload = json.dumps(
        {
            "entity_map": {},
            "entity_names": {"entity-1": "Named Only"},
            "metadata": "{}",
            "covers": "{}",
            "authors": "{}",
            "volumes": "{}",
        }
    )
    state = deserialize_state(payload)
    assert state.series["entity-1"].storage_name == "Named Only"
    assert "has no local name mapping" in caplog.text


def test_write_is_atomic_and_leaves_no_temp_files(temp_dir, mock_entity_db):
    repository = JsonRepository(temp_dir)
    repository.write_state(mock_entity_db.state)

    assert os.path.exists(os.path.join(temp_dir, "entity_db.json"))
    assert [f for f in os.listdir(temp_dir) if f.startswith(".entity_db.")] == []


def test_open_on_an_empty_directory_returns_empty_state(temp_dir):
    state = JsonRepository(temp_dir).open()
    assert len(state.series) == 0
    assert len(state.downloads) == 0
    assert not os.path.exists(os.path.join(temp_dir, "entity_db.json"))
