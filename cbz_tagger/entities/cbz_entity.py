import logging
import os
import re
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile

from cbz_tagger.common.helpers import make_directory_with_ownership
from cbz_tagger.common.helpers import set_file_ownership

logger = logging.getLogger()


class CbzEntity:
    def __init__(
        self,
        filepath: str,
        config_path: str = "",
        scan_path: str = "",
        storage_path: str = "",
    ):
        self.filepath = filepath
        self.config_path = config_path
        self.scan_path = scan_path
        self.storage_path = storage_path

    def check_path(self):
        if len(os.path.split(self.filepath)) > 2:
            raise ValueError(
                "Multiple file path depths found, please ensure files are in format: Series Name/Chapter Name.cbz"
            )

    @property
    def manga_name(self):
        self.check_path()
        manga_name = os.path.split(self.filepath)[0]
        return manga_name

    @property
    def chapter_is_volume(self):
        """If the volume is removed are there any numbers left? If not this is a volume only entity"""
        filename = self.chapter_name.replace(".cbz", "")
        filename = str.lower(filename)
        filename = re.sub(r"volume \d+", "", filename)
        filename_numeric_only = re.sub(r"[^0-9.]", "", filename)
        if len(filename_numeric_only) == 0:
            return True
        return False

    @property
    def chapter_name(self):
        self.check_path()
        return os.path.split(self.filepath)[1]

    @staticmethod
    def convert_to_number(value):
        try:
            float(value)
            return value
        except ValueError:
            # If the chapter number starts with a "." we should skip this first period
            if value[0] == ".":
                try:
                    float(value[1:])
                    return value[1:]
                except ValueError:
                    return None
            return None

    @property
    def chapter_number(self) -> str:
        filename = self.chapter_name.replace(".cbz", "")
        filename = str.lower(filename)

        # Check if formatting with chapter title, if so remove the word title
        if filename.find("-") != filename.rfind("-") and filename.find("-") != -1 and filename.rfind("-") != -1:
            chapter_pos = filename.find("ch")
            if filename.find("-") < chapter_pos < filename.rfind("-"):
                filename = filename[: filename.rfind("-")]

        filename = re.sub(r"\.\.+", "", filename)
        filename = re.sub(r"\(.*\)", "", filename)
        filename = re.sub(r"volume \d+ ", "", filename)
        filename = re.sub(r"part \d+", "", filename)
        filename_numeric_only = re.sub(r"[^0-9.]", " ", filename)
        valid_parts = [p for p in filename_numeric_only.split(" ") if len(p) > 0]
        valid_parts = [self.convert_to_number(p) for p in valid_parts if self.convert_to_number(p) is not None]
        valid_number = valid_parts[-1]
        # If the chapter number starts with a "." we should skip this first period
        if valid_number[0] == ".":
            valid_number = valid_number[1:]

        try:
            chapter_number = float(valid_number)
            if chapter_number.is_integer():
                chapter_number = int(chapter_number)
        except ValueError:
            chapter_number = valid_number

        return str(chapter_number)

    def get_name_and_chapter(self):
        return self.manga_name, self.chapter_number

    def get_entity_cover_image_path(self, image_filename):
        return os.path.join(self.config_path, "images", image_filename)

    def get_entity_read_path(self):
        return os.path.join(self.scan_path, self.filepath)

    def get_entity_write_path(self, entity_name, chapter_number):
        make_directory_with_ownership(os.path.join(self.storage_path, entity_name))
        chapter_number_string = str(chapter_number)
        if "." in chapter_number_string:
            fill = 5
            try:
                decimal_int = int(chapter_number_string.rsplit(".", maxsplit=1)[-1])
                if decimal_int >= 10:
                    fill = 6
            except ValueError:
                pass
            chapter_number_string = chapter_number_string.zfill(fill)
        else:
            chapter_number_string = chapter_number_string.zfill(3)
        if self.chapter_is_volume:
            return os.path.join(self.storage_path, entity_name, f"{entity_name} - Volume {chapter_number_string}.cbz")
        return os.path.join(self.storage_path, entity_name, f"{entity_name} - Chapter {chapter_number_string}.cbz")

    def get_mylar_series_json_path(self, entity_name):
        return os.path.join(self.storage_path, entity_name, "series.json")

    def build(
        self, entity_name, entity_xml, entity_image_path, mylar_series_json, remove_on_write=True, environment=None
    ):
        _ = environment
        read_path = self.get_entity_read_path()
        write_path = self.get_entity_write_path(entity_name, self.chapter_number)
        cover_image_path = self.get_entity_cover_image_path(entity_image_path)

        if os.path.exists(write_path):
            logger.error("ERROR >> Destination file already present!")
            return

        with ZipFile(read_path, "r") as zip_read:
            with ZipFile(write_path, "w", ZIP_DEFLATED) as zip_write:
                for item in zip_read.infolist():
                    if "ComicInfo" not in item.filename and "000_cover.jpg" not in item.filename:
                        zip_write.writestr(item, zip_read.read(item.filename))
                zip_write.writestr("ComicInfo.xml", entity_xml)
                zip_write.write(cover_image_path, "000_cover.jpg")

        if remove_on_write:
            os.remove(read_path)

        # Set the ownership of the file
        set_file_ownership(write_path)

        mylar_series_json_path = self.get_mylar_series_json_path(entity_name)
        with open(mylar_series_json_path, "w", encoding="utf-8") as json_file:
            json_file.write(mylar_series_json)
        set_file_ownership(mylar_series_json_path)
