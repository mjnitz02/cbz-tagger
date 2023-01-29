import os
import re
import shutil
import time
from os.path import join
from zipfile import ZIP_DEFLATED
from zipfile import BadZipFile
from zipfile import ZipFile

from cbz_tagger.common.enums import Mode
from cbz_tagger.common.env import AppEnv
from cbz_tagger.scanner.manga_db import MangaDB


class MangaScanner:
    def __init__(self, args) -> None:
        if args["auto"]:
            self.mode = Mode.AUTO
        elif args["manual"]:
            self.mode = Mode.MANUAL
        elif args["retag"]:
            self.mode = Mode.RETAG
        elif args["update"]:
            self.mode = Mode.UPDATE
        else:
            raise ValueError("No mode specified.")

        self.downloads_path = AppEnv.DOWNLOADS
        self.storage_path = AppEnv.STORAGE
        self.config_path = AppEnv.CONFIG
        self.move_files = AppEnv.MOVE_FILES
        self.retag_files = self.mode == Mode.RETAG

        print(f"Scanner running in {self.mode} mode.")

        self.database = MangaDB()

    def run(self):
        while True:
            completed = self.scan()
            if not completed:
                print("Scan not completed. Sleeping 60s")
                time.sleep(60)
                print("Initiating rescan...")
            else:
                return

    def scan(self):
        print("Starting scan....")
        for series in self.scan_for_series():
            if self.mode == Mode.AUTO:
                record = self.database.get(series, find_new=False)
                if record is None:
                    print(
                        f"Skipping Series: {series}",
                        "(run with --manual to add new series.)",
                    )
                    continue

            print(f"Scanning Series: {series}")
            for chapter in self.scan_for_chapters(series):
                chapter_file = join(self.downloads_path, series, chapter)

                # Check if cover or metadata is missing
                try:
                    with ZipFile(chapter_file, "r") as zip_file:
                        update_xml = "ComicInfo.xml" not in zip_file.namelist() or self.retag_files
                        update_cover = "000_cover.jpg" not in zip_file.namelist() or self.retag_files

                    if self.retag_files:
                        self.rebuild_zip_without_metadata(chapter_file)

                    self.update_cbz(series, chapter, chapter_file, update_xml, update_cover)
                    self.move_cbz(series, chapter, chapter_file)
                except BadZipFile:
                    print("Unable to read file... files are either in use or corrupted.")
                    return False
        print("Removing empty dirs")
        self.remove_empty_dirs()
        print("Scan completed.")
        return True

    def remove_empty_dirs(self):
        folders = list(os.walk(self.downloads_path))[1:]
        for folder in folders:
            files = [f for f in folder[2] if f != ".DS_Store"]
            if not files:
                shutil.rmtree(folder[0])

    def update_cbz(self, series, chapter, chapter_file, update_xml=False, update_cover=False):
        if not update_xml and not update_cover:
            return

        print(f"Updating {chapter_file}...")
        chapter_number = self.get_chapter_number_from_chapter(chapter)

        with ZipFile(chapter_file, "a", ZIP_DEFLATED) as zip_file:
            if update_xml:
                xml_path = join(self.config_path, "temp.xml")
                self.database.to_temp_xml(xml_path, series, chapter_number)
                zip_file.write(xml_path, os.path.basename("ComicInfo.xml"))
                os.remove(xml_path)
            if update_cover:
                image_path = self.database.get_image_path(series)
                zip_file.write(image_path, os.path.basename("000_cover.jpg"))

    def move_cbz(self, series, chapter, chapter_file):
        storage_dir = os.path.join(self.storage_path, series)
        storage_chapter = os.path.join(storage_dir, chapter)
        if not os.path.exists(storage_dir):
            os.mkdir(storage_dir)
        if os.path.exists(storage_chapter):
            print(f"Cannot move {chapter}, file already exists in storage!")
            return
        shutil.copy(chapter_file, storage_chapter)
        os.remove(chapter_file)

    def rebuild_zip_without_metadata(self, chapter_file):
        temp_file = join(self.config_path, "temp.cbz")
        with ZipFile(chapter_file, "r") as zip_file:
            with ZipFile(temp_file, "w", ZIP_DEFLATED) as zf_force:
                for item in zip_file.infolist():
                    if "ComicInfo" not in item.filename and "000_cover.jpg" not in item.filename:
                        zf_force.writestr(item, zip_file.read(item.filename))
        shutil.move(temp_file, chapter_file)

    @staticmethod
    def get_chapter_number_from_chapter(chapter):
        chapter_number = chapter.replace(".cbz", "").split(" ")[-1]
        first_digit = re.search(r"\d", chapter_number).start()
        if first_digit > 0:
            chapter_number = chapter_number[first_digit:]
        try:
            return f"{int(chapter_number):03d}"
        except ValueError:
            return f"{float(chapter_number):06.2f}"

    def scan_for_series(self):
        return [f for f in os.listdir(self.downloads_path) if os.path.isdir(os.path.join(self.downloads_path, f))]

    def scan_for_chapters(self, series):
        series_folder = join(self.downloads_path, series)
        return [
            f for f in os.listdir(series_folder) if (os.path.isfile(os.path.join(series_folder, f)) and ".cbz" in f)
        ]

    @staticmethod
    def check_if_cover(cbz_folder, cbz_file):
        with ZipFile(join(cbz_folder, cbz_file), "r") as zip_file:
            return "000_cover.jpg" in zip_file.namelist()

    @staticmethod
    def check_if_comicinfo(cbz_folder, cbz_file):
        with ZipFile(join(cbz_folder, cbz_file), "r") as zip_file:
            return "ComicInfo.xml" in zip_file.namelist()
