from contextlib import suppress
from pathlib import Path

from cbz_tagger.common.enums import APPLICATION_MAJOR_VERSION


def extract_version() -> str:
    """Returns either the version of installed package or the one
    found in nearby pyproject.toml"""
    with suppress(FileNotFoundError, StopIteration):
        with open(
            (root_dir := Path(__file__).parent.parent.parent) / "pyproject.toml", encoding="utf-8"
        ) as pyproject_toml:
            lines = [line for line in pyproject_toml]
            version = next(line for line in lines if line.startswith("version = ")).split("=")[1].strip("'\"\n ")
            return f"{version}"
    return f"{APPLICATION_MAJOR_VERSION}"
