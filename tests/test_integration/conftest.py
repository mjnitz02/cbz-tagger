import os
import shutil
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile

import pytest

from cbz_tagger.container.container import get_environment_variables
from cbz_tagger.database.file_scanner import FileScanner


@pytest.fixture
def manga_name():
    return "Precious. 4P Short Stories"


@pytest.fixture
def integration_path():
    return os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def config_path(integration_path):
    return os.path.join(integration_path, "config")


@pytest.fixture
def scan_path(integration_path):
    return os.path.join(integration_path, "scan")


@pytest.fixture
def storage_path(integration_path):
    return os.path.join(integration_path, "storage")


@pytest.fixture
def integration_scanner(config_path, scan_path, storage_path):
    try:
        os.makedirs(config_path, exist_ok=True)
        os.makedirs(scan_path, exist_ok=True)
        os.makedirs(storage_path, exist_ok=True)

        env_vars = get_environment_variables()

        scanner = FileScanner(
            config_path=config_path,
            scan_path=scan_path,
            storage_path=storage_path,
            environment=env_vars["environment"],
        )

        yield scanner

    finally:
        shutil.rmtree(config_path)
        shutil.rmtree(scan_path)
        shutil.rmtree(storage_path)


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
