import os
import re
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile


class CbzEntity:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def check_path(self):
        if len(os.path.split(self.filepath)) > 2:
            raise ValueError(
                "Multiple file path depths found, please ensure files are in format: Series Name/Chapter Name.cbz"
            )

    @property
    def manga_name(self):
        self.check_path()
        return os.path.split(self.filepath)[0]

    @property
    def chapter_name(self):
        self.check_path()
        return os.path.split(self.filepath)[1]

    @property
    def chapter_number(self) -> str:
        if "Ch.1.cbz" in self.chapter_name:
            assert True
        filename = self.chapter_name.replace(".cbz", "")
        filename_numeric_only = re.sub("[^0-9.]", " ", filename)
        valid_parts = [p for p in filename_numeric_only.split(" ") if len(p) > 0]
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

    def build(self, entity_xml, read_path, write_path, cover_image_path, remove_on_write=True):
        with ZipFile(read_path, "r") as zip_read:
            with ZipFile(write_path, "w", ZIP_DEFLATED) as zip_write:
                for item in zip_read.infolist():
                    if "ComicInfo" not in item.filename and "000_cover.jpg" not in item.filename:
                        zip_write.writestr(item, zip_read.read(item.filename))
                zip_write.writestr("ComicInfo.xml", entity_xml)
                zip_write.write(cover_image_path, "000_cover.jpg")

        if remove_on_write:
            os.remove(read_path)
