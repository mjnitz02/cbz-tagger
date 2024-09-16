import os

from cbz_tagger.database.entity_db import EntityDB


def test_entity_database_image_db_path(mock_entity_db, temp_folder_path):
    expected = os.path.join(temp_folder_path, "images")
    assert expected == mock_entity_db.image_db_path


def test_entity_database_creates_new_database_with_none_present(temp_folder_path):
    entity_database = EntityDB(temp_folder_path)
    assert entity_database.entity_map == {}


def test_entity_database_can_save_and_load(mock_entity_db, temp_dir):
    mock_entity_db.save()
    entity_database = EntityDB.load(root_path=temp_dir)

    # Restored database will likely match, but check the json dumps to ensure they are the same
    assert mock_entity_db.to_json() == entity_database.to_json()
