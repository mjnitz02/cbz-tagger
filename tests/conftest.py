import os
import shutil

import pytest

from cbz_tagger.common.env import AppEnv
from cbz_tagger.database.file_scanner import FileScanner


@pytest.fixture
def tests_path():
    path = os.path.split(os.path.abspath(__file__))[0]
    return path


@pytest.fixture
def tests_fixtures_path(tests_path):
    return os.path.join(tests_path, "fixtures")


@pytest.fixture
def temp_folder_path(tests_path):
    return os.path.join(tests_path, "temp_test_dir")


@pytest.fixture
def temp_dir(temp_folder_path):
    os.makedirs(temp_folder_path, exist_ok=True)
    yield temp_folder_path
    shutil.rmtree(temp_folder_path)


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

        env_vars = AppEnv.get_user_environment()

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
