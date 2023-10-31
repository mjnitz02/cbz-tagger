import os
import re
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile


class CbzEntity:
    def __init__(self, filepath: str):
        self.filepath = filepath

    @property
    def manga_name(self):
        return os.path.split(self.filepath)[0]

    @property
    def chapter_number(self) -> str:
        # Remove all non numeric characters and split by contigous numbers.
        # Take the last seen number as the chapter
        filepath_parts = re.sub("[^0-9.]", " ", self.filepath.replace(".cbz", "")).split(" ")
        chapter_parts = [num for num in filepath_parts if len(num)]
        chapter_number = chapter_parts[-1]
        chapter_number = float(chapter_number)
        if chapter_number.is_integer():
            chapter_number = int(chapter_number)
        chapter_number = str(chapter_number)

        return chapter_number

    def get_name_and_chapter(self):
        return self.manga_name, self.chapter_number

    def build(self, entity_xml, read_path, write_path, cover_image_path, remove_on_write=True):
        with ZipFile(read_path, "r") as zip_read:
            with ZipFile(write_path, "w", ZIP_DEFLATED) as zip_write:
                for item in zip_read.infolist():
                    if "ComicInfo" not in item.filename and "000_cover.jpg" not in item.filename:
                        zip_write.writestr(item, zip_read.read(item.filename))
                zip_write.writestr(entity_xml, "ComicInfo.xml")
                zip_write.write(cover_image_path, "000_cover.jpg")

        if remove_on_write:
            os.remove(read_path)
