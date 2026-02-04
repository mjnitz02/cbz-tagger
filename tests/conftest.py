import os
import shutil
import tempfile

import pytest

# Set up test environment variables BEFORE importing cbz_tagger modules
# This prevents cbz_tagger/__init__.py from trying to create directories in /config
_TEST_TEMP_DIR = tempfile.mkdtemp(prefix="cbz_tagger_test_")
os.environ.setdefault("CONFIG_PATH", os.path.join(_TEST_TEMP_DIR, "config"))
os.environ.setdefault("SCAN_PATH", os.path.join(_TEST_TEMP_DIR, "scan"))
os.environ.setdefault("STORAGE_PATH", os.path.join(_TEST_TEMP_DIR, "storage"))
os.environ.setdefault("LOG_PATH", os.path.join(_TEST_TEMP_DIR, "config", "logs", "cbz_tagger.log"))

from cbz_tagger.common.env import AppEnv
from cbz_tagger.database.file_scanner import FileScanner


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_temp_dir():
    """Clean up the temporary test directory after all tests complete."""
    yield
    if os.path.exists(_TEST_TEMP_DIR):
        shutil.rmtree(_TEST_TEMP_DIR, ignore_errors=True)


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

        scanner = FileScanner(
            config_path=config_path,
            scan_path=scan_path,
            storage_path=storage_path,
            environment=AppEnv().get_user_environment(),
        )

        yield scanner

    finally:
        shutil.rmtree(config_path)
        shutil.rmtree(scan_path)
        shutil.rmtree(storage_path)
