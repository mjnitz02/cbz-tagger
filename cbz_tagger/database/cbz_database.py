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
        if self.entity_database.check_manga_missing(manga_name):
            if not self.add_missing:
                raise RuntimeError("Manual mode must be enabled for adding missing manga to the database.")
            self.entity_database.add_and_update(manga_name, self.root_path)
            self.save()

        return self.entity_database.get_comicinfo_and_image(manga_name, chapter_number)

    def download_chapters(self, config_path, storage_path):
        for entity_id, chapter_items in self.entity_database.chapters.database.items():
            for chapter_item in chapter_items:
                key = (entity_id, chapter_item.entity_id)
                if key not in self.entity_database.entity_downloads:
                    try:
                        self.entity_database.download_chapter(entity_id, chapter_item, config_path, storage_path)
                        self.save()
                    except EnvironmentError as e:
                        print(f"Could not download chapter: {entity_id}, {chapter_item.entity_id}", e)

    def refresh(self):
        for manga_name in self.entity_database.entity_map.keys():
            print(f"Refreshing {manga_name}")
            self.update_metadata(manga_name)
        self.entity_database.clean(self.image_db_path)
        self.save()

    def update_metadata(self, manga_name, save=False):
        if self.entity_database.check_manga_missing(manga_name):
            return

        try:
            self.entity_database.update_manga_entity(manga_name, self.image_db_path)
            if save:
                self.save()
        except EnvironmentError:
            print(f"Mangadex API Down >> Unable to update {manga_name} metadata.")
