from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cbz_tagger.common.enums import ContainerMode
from cbz_tagger.container.container import run_container


@pytest.fixture
def mock_manual_container():
    with patch("cbz_tagger.container.container.ManualContainer") as mock_container:
        yield mock_container


@pytest.fixture
def mock_timer_container():
    with patch("cbz_tagger.container.container.TimerContainer") as mock_container:
        yield mock_container


def test_run_container_entrymode_timer(mock_timer_container):
    mock_timer_container.return_value.run = MagicMock()
    with patch("cbz_tagger.container.container.AppEnv.CONTAINER_MODE", ContainerMode.TIMER):
        run_container(entrymode=True)
        mock_timer_container.assert_called_once()
        mock_timer_container.return_value.run.assert_called_once()


def test_run_container_entrymode_manual(mock_manual_container):
    mock_manual_container.return_value.run = MagicMock()
    with patch("cbz_tagger.container.container.AppEnv.CONTAINER_MODE", ContainerMode.MANUAL):
        run_container(entrymode=True)
        mock_manual_container.assert_called_once()
        mock_manual_container.return_value.run.assert_called_once()


def test_run_container_manual_mode(mock_manual_container):
    mock_manual_container.return_value.scanner.run = MagicMock()
    run_container(entrymode=False)
    mock_manual_container.assert_called_once()
    mock_manual_container.return_value.scanner.run.assert_called_once()


def test_run_container_add_mode(mock_manual_container):
    mock_manual_container.return_value.scanner.add_tracked_entity = MagicMock()
    run_container(entrymode=False, add=True)
    mock_manual_container.assert_called_once()
    mock_manual_container.return_value.scanner.add_tracked_entity.assert_called_once()


def test_run_container_refresh_mode(mock_manual_container):
    mock_manual_container.return_value.scanner.refresh = MagicMock()
    run_container(entrymode=False, refresh=True)
    mock_manual_container.assert_called_once()
    mock_manual_container.return_value.scanner.refresh.assert_called_once()
