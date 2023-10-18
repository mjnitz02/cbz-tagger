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
    def __init__(self) -> None:
        self.import_path = AppEnv.IMPORT
        self.export_path = AppEnv.EXPORT
        self.config_path = AppEnv.CONFIG

        self.cbz_database = CbzDatabase()

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
        for manga_name in self.scan_for_series():
            print(f"Scanning Series: {manga_name}")
            for chapter in self.scan_for_chapters(manga_name):
                try:
                    print(f"Retrieving metadata for {chapter}...")
                    chapter_number = self.get_chapter_number_from_chapter(chapter)
                    local_name, xml, image_path = self.cbz_database.get_metadata(manga_name, chapter_number)

                    read_file = join(self.import_path, manga_name, str(chapter))
                    write_file = join(self.export_path, local_name, f"{local_name} - Chapter {str(chapter_number).zfill(3)}")

                    print(f"Updating {read_file}...")
                    with ZipFile(read_file, "r") as zip_read:
                        with ZipFile(write_file, "w", ZIP_DEFLATED) as zip_write:
                            for item in zip_read.infolist():
                                if "ComicInfo" not in item.filename and "000_cover.jpg" not in item.filename:
                                    zip_write.writestr(item, zip_read.read(item.filename))
                            zip_write.writestr(xml, "ComicInfo.xml")
                            zip_write.write(os.path.join(self.config_path, "images", image_path), os.path.basename("000_cover.jpg"))
                except BadZipFile:
                    print("Unable to read file... files are either in use or corrupted.")
                    return False
        print("Removing empty dirs")
        self.remove_empty_dirs()
        print("Scan completed.")
        return True

    def remove_empty_dirs(self):
        folders = list(os.walk(self.import_path))[1:]
        for folder in folders:
            files = [f for f in folder[2] if f != ".DS_Store"]
            if not files:
                shutil.rmtree(folder[0])

    @staticmethod
    def get_chapter_number_from_chapter(chapter):
        chapter_number = chapter.replace(".cbz", "").split(" ")[-1]
        first_digit = re.search(r"\d", chapter_number).start()
        if first_digit > 0:
            chapter_number = chapter_number[first_digit:]
        try:
            return str(int(chapter_number))
        except ValueError:
            return str(float(chapter_number))

    def scan_for_series(self):
        return [f for f in os.listdir(self.import_path) if os.path.isdir(os.path.join(self.import_path, f))]

    def scan_for_chapters(self, series):
        series_folder = join(self.import_path, series)
        return [
            f for f in os.listdir(series_folder) if (os.path.isfile(os.path.join(series_folder, f)) and ".cbz" in f)
        ]
