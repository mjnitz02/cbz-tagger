import os
from contextlib import suppress
from pathlib import Path

from cbz_tagger.common.enums import APPLICATION_MAJOR_VERSION


def extract_version() -> str:
    """Returns the release version baked into the published image, or
    failing that the one found in nearby pyproject.toml"""
    if released_version := os.getenv("CBZ_TAGGER_VERSION"):
        return released_version
    with suppress(FileNotFoundError, StopIteration):
        with open(Path(__file__).parent.parent.parent / "pyproject.toml", encoding="utf-8") as pyproject_toml:
            lines = list(line for line in pyproject_toml)
            version = next(line for line in lines if line.startswith("version = ")).split("=")[1].strip("'\"\n ")
            return f"{version}"
    return f"{APPLICATION_MAJOR_VERSION}"
