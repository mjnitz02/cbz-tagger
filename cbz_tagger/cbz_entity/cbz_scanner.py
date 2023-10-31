import os
import shutil
import time
from zipfile import BadZipFile

from cbz_tagger.cbz_entity.cbz_entity import CbzEntity
from cbz_tagger.database.cbz_database import CbzDatabase


class CbzScanner:
    def __init__(self, config_path, scan_path, storage_path, add_missing=True) -> None:
        self.config_path = config_path
        self.scan_path = scan_path
        self.storage_path = storage_path

        self.cbz_database = CbzDatabase(root_path=self.config_path, add_missing=add_missing)

    def run(self):
        while True:
            completed = self.scan()
            if not completed:
                print("Scan not completed. Sleeping 120s")
                time.sleep(120)
                print("Initiating rescan...")
            else:
                return

    def scan(self):
        print("Starting scan....")
        for filepath in self.get_cbz_files():
            try:
                self.process(filepath)
            except BadZipFile:
                print("Unable to read file... files are either in use or corrupted.")
                return False

        self.remove_empty_dirs()
        return True

    def get_cbz_files(self):
        filepaths = [
            list(os.path.join(root, f) for f in filenames if os.path.splitext(f)[-1] == ".cbz")
            for (root, _, filenames) in os.walk(self.scan_path)
        ]
        filepaths = sorted([os.path.relpath(item, self.scan_path) for items in filepaths for item in items])
        return filepaths

    def process(self, filepath):
        cbz_entity = CbzEntity(filepath)
        manga_name, chapter_number = cbz_entity.get_name_and_chapter()
        print(filepath, manga_name, chapter_number)

        try:
            entity_name, entity_xml, entity_image_path = self.cbz_database.get_metadata(manga_name, chapter_number)
        except RuntimeError:
            print(f"ERROR >> {manga_name} not in database. Run manual mode to add new series.")
            return

        read_path = self.get_entity_read_path(filepath)
        write_path = self.get_entity_write_path(entity_name, chapter_number)
        cover_image_path = self.get_entity_cover_image_path(entity_image_path)

        if os.path.exists(write_path):
            print("ERROR >> Destination file already present!")
            return

        cbz_entity.build(entity_xml, read_path, write_path, cover_image_path)

    def get_entity_read_path(self, filepath):
        return os.path.join(self.scan_path, filepath)

    def get_entity_write_path(self, entity_name, chapter_number):
        os.makedirs(os.path.join(self.storage_path, entity_name), exist_ok=True)
        return os.path.join(
            self.storage_path, entity_name, f"{entity_name} - Chapter {str(chapter_number).zfill(3)}.cbz"
        )

    def get_entity_cover_image_path(self, entity_image_path):
        return os.path.join(self.config_path, "images", entity_image_path)

    def remove_empty_dirs(self):
        folders = list(os.walk(self.scan_path))[1:]
        for folder in folders:
            files = [f for f in folder[2] if f != ".DS_Store"]
            if not files:
                shutil.rmtree(folder[0])
