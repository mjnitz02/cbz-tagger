import json
import os
from os.path import exists, join

import requests as requests

from manga_tag.common.env import AppEnv
from manga_tag.scanner.manga_object import MangaObject


class MangaDB(object):
    def __init__(self):
        self.config_path = AppEnv.CONFIG

        self.db_path = join(self.config_path, "manga_db.json")
        self.image_path = join(self.config_path, "images")
        self.version = 1
        self.db = None

        self.load()

    def load(self):
        if not exists(self.db_path):
            with open(self.db_path, "w") as f:
                json.dump({"db_version": 1}, f)

        with open(self.db_path, "r") as f:
            self.db = json.load(f)

    def save(self):
        with open(self.db_path, "w") as f:
            json.dump(self.db, f, indent=4)

    def get(self, manga_name, find_new=True):
        record = self.db.get(manga_name)
        if record is None:
            if not find_new:
                return None
            self.db[manga_name] = MangaObject(manga_name).to_dict()
            record = self.db.get(manga_name)
            self.save()

        return MangaObject.from_dict(record)

    def get_image_path(self, manga_name):
        manga_object = self.get(manga_name)
        if not exists(self.image_path):
            os.mkdir(self.image_path)

        image_path = join(self.image_path, "{}.jpg".format(manga_name))
        if not exists(image_path):
            image_url = manga_object.manga_info["coverImage"]["large"]
            img_data = requests.get(image_url).content
            with open(image_path, "wb") as handler:
                handler.write(img_data)
        return image_path

    def to_temp_xml(self, filepath, manga_name, chapter):
        manga_object = self.get(manga_name)
        manga_object.to_xml_file(chapter, filepath)
