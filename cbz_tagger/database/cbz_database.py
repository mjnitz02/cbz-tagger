import os

from cbz_tagger.database.entity_db import EntityDB


class CbzDatabase:
    def __init__(self, root_path, add_missing=True):
        self.add_missing = add_missing
        self.root_path = root_path
        self.entity_database = self.load()

    @property
    def entity_db_path(self) -> str:
        return os.path.join(self.root_path, "entity_db.json")

    @property
    def image_db_path(self) -> str:
        return os.path.join(self.root_path, "images")

    @property
    def entity_db_exists(self) -> bool:
        return os.path.exists(self.entity_db_path)

    def load(self) -> EntityDB:
        if self.entity_db_exists:
            with open(self.entity_db_path, "r", encoding="UTF-8") as read_file:
                contents = read_file.read()
            return EntityDB.from_json(contents)
        return EntityDB()

    def save(self) -> None:
        entity_database_json = self.entity_database.to_json()

        os.makedirs(self.root_path, exist_ok=True)
        with open(self.entity_db_path, "w", encoding="UTF-8") as write_file:
            write_file.write(entity_database_json)

    def get_metadata(self, manga_name, chapter_number):
        if manga_name not in self.entity_database.keys():
            if not self.add_missing:
                raise RuntimeError("Manual mode must be enabled for adding missing manga to the database.")
            self.entity_database.add(manga_name)
            self.entity_database.update_manga_entity(manga_name, os.path.join(self.root_path, "images"))
            self.save()

        entity_name = self.entity_database.to_entity_name(manga_name)
        entity_xml = self.entity_database.to_xml_string(manga_name, chapter_number)
        entity_image_path = self.entity_database.to_local_image_file(manga_name, chapter_number)
        return entity_name, entity_xml, entity_image_path

    def update_metadata(self, manga_name):
        self.entity_database.update_manga_entity(manga_name, self.image_db_path)
