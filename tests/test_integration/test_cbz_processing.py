import os
import shutil
from unittest import mock
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile

import pytest

from cbz_tagger.container.container import get_environment_variables
from cbz_tagger.container.file_scanner import FileScanner


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
def integration_environment(config_path, scan_path, storage_path):
    try:
        os.makedirs(config_path, exist_ok=True)
        os.makedirs(scan_path, exist_ok=True)
        os.makedirs(storage_path, exist_ok=True)

        yield config_path, scan_path, storage_path

    finally:
        shutil.rmtree(config_path)
        shutil.rmtree(scan_path)
        shutil.rmtree(storage_path)


@pytest.fixture
def build_test_cbz(tests_fixtures_path, scan_path, manga_name):
    def _build_test_cbz(chapter_number=1):
        os.makedirs(os.path.join(scan_path, manga_name), exist_ok=True)

        test_cbz_path = os.path.join(scan_path, manga_name, f"{manga_name} - {chapter_number}")
        image_source_path = os.path.join(tests_fixtures_path, "page.jpg")

        with ZipFile(f"{test_cbz_path}.cbz", "w", ZIP_DEFLATED) as zip_write:
            for i in range(1, 6):
                zip_write.write(image_source_path, f"{i:03}.jpg")

    return _build_test_cbz


@mock.patch("cbz_tagger.database.entity_db.get_input")
def test_process_cbz_files(mock_get_input, integration_environment, build_test_cbz):
    def capture_input(test_input, *args, **kwargs):
        _ = args, kwargs
        if test_input == "Please select the manga that you are searching for in number: ":
            return 1
        if test_input == "Please select the manga that you are searching for in number: ":
            return 1
        return 0

    mock_get_input.side_effect = capture_input
    config_path, scan_path, storage_path = integration_environment
    build_test_cbz()
    env_vars = get_environment_variables()

    scanner = FileScanner(
        config_path=config_path,
        scan_path=scan_path,
        storage_path=storage_path,
        environment=env_vars["environment"],
    )
    scanner.run_scan()

    # Assert the scanned files are all processed
    assert len(os.listdir(os.path.join(config_path, "images"))) == 2
    assert os.listdir(scan_path) == []
    storage_results = [
        os.path.relpath(os.path.join(root, name), storage_path)
        for root, dirs, files in os.walk(storage_path)
        for name in files
    ]
    assert storage_results == [
        "Touto Sugite Yome na a a a a a a i 4P Short Stories/"
        "Touto Sugite Yome na a a a a a a i 4P Short Stories - Chapter 001.cbz"
    ]


def test_process_cbz_files_with_no_files(integration_environment):
    config_path, scan_path, storage_path = integration_environment
    env_vars = get_environment_variables()
    scanner = FileScanner(
        config_path=config_path,
        scan_path=scan_path,
        storage_path=storage_path,
        environment=env_vars["environment"],
    )
    scanner.run_scan()
