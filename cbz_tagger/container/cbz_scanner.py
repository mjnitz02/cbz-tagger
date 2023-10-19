import os
import re
import shutil
import time
from os.path import join
from zipfile import BadZipFile
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile

from cbz_tagger.common.env import AppEnv
from cbz_tagger.database.cbz_database import CbzDatabase


class CbzScanner:
    def __init__(self, add_missing=True) -> None:
        self.import_path = os.path.abspath(AppEnv.IMPORT)
        self.export_path = os.path.abspath(AppEnv.EXPORT)
        self.config_path = os.path.abspath(AppEnv.CONFIG)

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
        files = [list(os.path.join(root, f) for f in filenames if os.path.splitext(f)[-1] == ".cbz") for
                 (root, _, filenames) in
                 os.walk(self.import_path)]
        files = sorted([os.path.relpath(item, self.import_path) for items in files for item in items])

        for file in files:
            try:
                self.process_file(file)
            except BadZipFile:
                print("Unable to read file... files are either in use or corrupted.")
                return False
        self.remove_empty_dirs()
        return True

    def process_file(self, filepath):
        print(f"Retrieving metadata for {filepath}...")
        manga_name = os.path.split(filepath)[0]

        # Remove all non numeric characters and split by contigous numbers.
        # Take the last seen number as the chapter
        chapter_number = [
            num for num in re.sub("[^0-9.]", " ", filepath.replace(".cbz", "")).split(" ") if len(num)
        ][-1]
        chapter_number = float(chapter_number)
        if chapter_number.is_integer():
            chapter_number = int(chapter_number)
        chapter_number = str(chapter_number)

        print(f"Manga: {manga_name}, Chapter: {chapter_number}")
        try:
            entity_name, entity_xml, entity_image_path = self.cbz_database.get_metadata(manga_name, chapter_number)
        except RuntimeError:
            print(f"ERROR >> {manga_name} not in database. Run manual mode to add new series.")
            return

        os.makedirs(os.path.join(self.export_path, entity_name), exist_ok=True)
        read_path = os.path.join(self.import_path, filepath)
        write_path = os.path.join(self.export_path, entity_name, f"{entity_name} - Chapter {str(chapter_number).zfill(3)}.cbz")
        if os.path.exists(write_path):
            print("ERROR >> Destination file already present!")
            return

        with ZipFile(read_path, "r") as zip_read:
            with ZipFile(write_path, "w", ZIP_DEFLATED) as zip_write:
                for item in zip_read.infolist():
                    if "ComicInfo" not in item.filename and "000_cover.jpg" not in item.filename:
                        zip_write.writestr(item, zip_read.read(item.filename))
                zip_write.writestr(entity_xml, "ComicInfo.xml")
                zip_write.write(os.path.join(self.config_path, "images", entity_image_path), "000_cover.jpg")
        os.remove(read_path)

    def remove_empty_dirs(self):
        folders = list(os.walk(self.import_path))[1:]
        for folder in folders:
            files = [f for f in folder[2] if f != ".DS_Store"]
            if not files:
                shutil.rmtree(folder[0])
