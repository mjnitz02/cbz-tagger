import os
import re
import shutil
import time
from os.path import join
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from manga_tag.common.enums import AppEnv, Mode
from manga_tag.services.manga_db import MangaDB


class MangaScanner(object):
    def __init__(self, args) -> None:
        self.downloads_path = AppEnv.downloads_path
        self.config_path = AppEnv.config_path

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

        print("Scanner running in {} mode.".format(self.mode))

        self.db = MangaDB()

    def run(self):
        while True:
            completed = self.scan(retag=(self.mode == Mode.RETAG))
            if not completed:
                print("Scan not completed. Sleeping 60s")
                time.sleep(60)
                print("Initiating rescan...")
            else:
                return

    def scan(self, retag=False):
        print("Starting scan....")
        for series in self.scan_for_series():

            if self.mode == Mode.AUTO:
                record = self.db.get(series, find_new=False)
                if record is None:
                    print(
                        "Skipping Series: {}".format(series),
                        "(run with --manual to add new series.)",
                    )
                    continue

            print("Scanning Series: {}".format(series))
            for chapter in self.scan_for_chapters(series):
                chapter_file = join(self.downloads_path, series, chapter)

                # Check if cover or metadata is missing
                try:
                    with ZipFile(chapter_file, "r") as zf:
                        update_xml = "ComicInfo.xml" not in zf.namelist() or retag
                        update_cover = "000_cover.jpg" not in zf.namelist() or retag

                    if retag:
                        self.rebuild_zip_without_metadata(chapter_file)

                    self.update_cbz(
                        series, chapter, chapter_file, update_xml, update_cover
                    )
                except BadZipFile:
                    print(
                        "Unable to read file... files are either in use or corrupted."
                    )
                    return False
        print("Scan completed.")
        return True

    def update_cbz(
        self, series, chapter, chapter_file, update_xml=False, update_cover=False
    ):
        if not update_xml and not update_cover:
            return

        print("Updating {}...".format(chapter_file))
        chapter_number = self.get_chapter_number_from_chapter(chapter)

        with ZipFile(chapter_file, "a", ZIP_DEFLATED) as zf:
            if update_xml:
                xml_path = join(self.config_path, "temp.xml")
                self.db.to_temp_xml(xml_path, series, chapter_number)
                zf.write(xml_path, os.path.basename("ComicInfo.xml"))
                os.remove(xml_path)
            if update_cover:
                image_path = self.db.get_image_path(series)
                zf.write(image_path, os.path.basename("000_cover.jpg"))

    def rebuild_zip_without_metadata(self, chapter_file):
        temp_file = join(self.config_path, "temp.cbz")
        with ZipFile(chapter_file, "r") as zf:
            with ZipFile(temp_file, "w", ZIP_DEFLATED) as zf_force:
                for item in zf.infolist():
                    if (
                        "ComicInfo" not in item.filename
                        and "000_cover.jpg" not in item.filename
                    ):
                        zf_force.writestr(item, zf.read(item.filename))
        shutil.move(temp_file, chapter_file)

    @staticmethod
    def get_chapter_number_from_chapter(chapter):
        chapter_number = chapter.replace(".cbz", "").split(" ")[-1]
        first_digit = re.search(r"\d", chapter_number).start()
        if first_digit > 0:
            chapter_number = chapter_number[first_digit:]
        try:
            return "{:03d}".format(int(chapter_number))
        except ValueError:
            return "{:06.2f}".format(float(chapter_number))

    def scan_for_series(self):
        return [
            f
            for f in os.listdir(self.downloads_path)
            if os.path.isdir(os.path.join(self.downloads_path, f))
        ]

    def scan_for_chapters(self, series):
        series_folder = join(self.downloads_path, series)
        return [
            f
            for f in os.listdir(series_folder)
            if (os.path.isfile(os.path.join(series_folder, f)) and ".cbz" in f)
        ]

    @staticmethod
    def check_if_cover(cbz_folder, cbz_file):
        with ZipFile(join(cbz_folder, cbz_file), "r") as zf:
            return "000_cover.jpg" in zf.namelist()

    @staticmethod
    def check_if_comicinfo(cbz_folder, cbz_file):
        with ZipFile(join(cbz_folder, cbz_file), "r") as zf:
            return "ComicInfo.xml" in zf.namelist()
