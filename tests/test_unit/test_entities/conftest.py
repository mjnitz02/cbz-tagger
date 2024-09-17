import pytest


@pytest.fixture
def check_entity_for_save_and_load():
    def _check_entity_for_save_and_load(entity):
        json_str = entity.to_json()
        new_entity = entity.from_json(json_str)
        assert entity.content == new_entity.content

        new_json_str = new_entity.to_json()
        assert json_str == new_json_str

    return _check_entity_for_save_and_load
