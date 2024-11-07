from unittest.mock import MagicMock
from unittest.mock import patch

from cbz_tagger.gui.elements.config_table import config_table


@patch("cbz_tagger.gui.elements.config_table.AppEnv")
@patch("cbz_tagger.gui.elements.config_table.ui.table")
def test_config_table(mock_ui_table, mock_app_env):
    mock_env = MagicMock()
    mock_env.CONTAINER_MODE = "mock_container_mode"
    mock_env.CONFIG_PATH = "mock_config_path"
    mock_env.SCAN_PATH = "mock_scan_path"
    mock_env.STORAGE_PATH = "mock_storage_path"
    mock_env.TIMER_DELAY = "mock_timer_delay"
    mock_env.PROXY_URL = "mock_proxy_url"
    mock_env.PUID = "mock_puid"
    mock_env.PGID = "mock_pgid"
    mock_env.UMASK = "mock_umask"
    mock_app_env.return_value = mock_env

    config_table()

    expected_columns = [
        {"name": "property", "label": "property", "field": "property", "align": "left"},
        {"name": "value", "label": "value", "field": "value", "align": "left"},
    ]
    expected_rows = [
        {"property": "container_mode", "value": "mock_container_mode"},
        {"property": "config_path", "value": "mock_config_path"},
        {"property": "scan_path", "value": "mock_scan_path"},
        {"property": "storage_path", "value": "mock_storage_path"},
        {"property": "timer_delay", "value": "mock_timer_delay"},
        {"property": "proxy_url", "value": "mock_proxy_url"},
        {"property": "PUID", "value": "mock_puid"},
        {"property": "PGID", "value": "mock_pgid"},
        {"property": "UMASK", "value": "mock_umask"},
    ]

    mock_ui_table.assert_called_once_with(columns=expected_columns, rows=expected_rows)
