import os

import pytest


@pytest.fixture
def unit_path():
    return os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def config_path(unit_path):
    return os.path.join(unit_path, "config")


@pytest.fixture
def scan_path(unit_path):
    return os.path.join(unit_path, "scan")


@pytest.fixture
def storage_path(unit_path):
    return os.path.join(unit_path, "storage")
