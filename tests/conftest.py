import os

import pytest


@pytest.fixture
def tests_path():
    path = os.path.split(os.path.abspath(__file__))[0]
    return path


@pytest.fixture
def tests_fixtures_path(tests_path):
    return os.path.join(tests_path, "fixtures")
