import tomllib
from pathlib import Path

import pytest

from cbz_tagger.common.version import extract_version


@pytest.fixture
def pyproject_version():
    pyproject = Path(__file__).parents[3] / "pyproject.toml"
    return tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]


def test_version_from_release_build(monkeypatch):
    monkeypatch.setenv("CBZ_TAGGER_VERSION", "9.8.7")
    assert extract_version() == "9.8.7"


def test_version_falls_back_to_pyproject(monkeypatch, pyproject_version):
    monkeypatch.delenv("CBZ_TAGGER_VERSION", raising=False)
    assert extract_version() == pyproject_version


def test_empty_release_version_falls_back_to_pyproject(monkeypatch, pyproject_version):
    # A local `docker build` passes no VERSION, which leaves the variable set but empty.
    monkeypatch.setenv("CBZ_TAGGER_VERSION", "")
    assert extract_version() == pyproject_version
