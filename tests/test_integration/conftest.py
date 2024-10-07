import os
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile

import pytest


@pytest.fixture
def manga_name():
    return "Precious. 4P Short Stories"


@pytest.fixture
def build_test_cbz(tests_fixtures_path, scan_path, manga_name):
    """We don't want to actually download anything, so we'll create a test cbz file instead."""

    def _build_test_cbz(chapter_number=1):
        os.makedirs(os.path.join(scan_path, manga_name), exist_ok=True)

        test_cbz_path = os.path.join(scan_path, manga_name, f"{manga_name} - {chapter_number}")
        image_source_path = os.path.join(tests_fixtures_path, "page.jpg")

        with ZipFile(f"{test_cbz_path}.cbz", "w", ZIP_DEFLATED) as zip_write:
            for i in range(1, 6):
                zip_write.write(image_source_path, f"{i:03}.jpg")

    return _build_test_cbz


@pytest.fixture
def capture_input_fixture():
    def _func(manga_name):
        def capture_input(test_input, *args, **kwargs):
            _ = args, kwargs
            if test_input == "Enter a new name to search for: ":
                return manga_name
            if test_input == "Please select the manga that you are searching for in number: ":
                return 1
            if "Mark all chapters" in test_input:
                return 0
            return 0

        return capture_input

    return _func
