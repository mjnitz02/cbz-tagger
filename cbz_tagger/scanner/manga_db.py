import json
import os
from os.path import exists
from os.path import join

import requests

from cbz_tagger.common.env import AppEnv
from cbz_tagger.scanner.manga_object import MangaObject


class MangaDB:
    def __init__(self):
        self.config_path = AppEnv.CONFIG

        self.db_path = join(self.config_path, "manga_db.json")
        self.image_path = join(self.config_path, "images")
        self.version = 1
        self.database = None

        self.load()

    def load(self):
        if not exists(self.db_path):
            with open(self.db_path, "w", encoding="UTF-8") as write_file:
                json.dump({"db_version": 1}, write_file)

        with open(self.db_path, "r", encoding="UTF-8") as write_file:
            self.database = json.load(write_file)

    def save(self):
        with open(self.db_path, "w", encoding="UTF-8") as write_file:
            json.dump(self.database, write_file, indent=4)

    def get(self, manga_name, find_new=True):
        record = self.database.get(manga_name)
        if record is None:
            if not find_new:
                return None
            self.database[manga_name] = MangaObject(manga_name).to_dict()
            record = self.database.get(manga_name)
            self.save()

        return MangaObject.from_dict(record)

    def get_image_path(self, manga_name):
        manga_object = self.get(manga_name)
        if not exists(self.image_path):
            os.mkdir(self.image_path)

        image_path = join(self.image_path, f"{manga_name}.jpg")
        if not exists(image_path):
            image_url = manga_object.manga_info["coverImage"]["large"]
            img_data = requests.get(image_url, timeout=30).content
            with open(image_path, "wb") as handler:
                handler.write(img_data)
        return image_path

    def to_temp_xml(self, filepath, manga_name, chapter):
        manga_object = self.get(manga_name)
        manga_object.to_xml_file(chapter, filepath)
