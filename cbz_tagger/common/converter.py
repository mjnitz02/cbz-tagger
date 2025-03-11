import re
from typing import Optional


def convert_value_to_number(value) -> Optional[float]:
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


def convert_chapter_to_number(filename) -> str:
    filename = filename.replace(".cbz", "")
    filename = filename.lower()

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
    valid_parts = [convert_value_to_number(p) for p in valid_parts if convert_value_to_number(p) is not None]
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
