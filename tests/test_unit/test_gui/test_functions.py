from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cbz_tagger.gui.functions import add_new_to_scanner
from cbz_tagger.gui.functions import notify_and_log
from cbz_tagger.gui.functions import refresh_scanner


def test_refresh_scanner():
    mock_scanner = MagicMock()
    result = refresh_scanner(mock_scanner)
    mock_scanner.run.assert_called_once()
    assert result == mock_scanner


@pytest.mark.parametrize(
    "enable_tracking, mark_all_tracked",
    [
        (True, True),
        (False, True),
        (True, False),
    ],
)
def test_add_new_to_scanner(enable_tracking, mark_all_tracked):
    mock_scanner = MagicMock()
    entity_name = "test_entity"
    entity_id = "123"
    backend = {"plugin_type": "test_plugin", "plugin_id": "456"}

    result = add_new_to_scanner(mock_scanner, entity_name, entity_id, backend, enable_tracking, mark_all_tracked)

    # pylint: disable=duplicate-code
    mock_scanner.entity_database.add_entity.assert_called_once_with(
        entity_name,
        entity_id,
        manga_name=None,
        backend=backend,
        update=True,
        track=enable_tracking,
        mark_as_tracked=mark_all_tracked,
    )
    assert result == mock_scanner


@patch("cbz_tagger.gui.functions.ui.notify")
@patch("cbz_tagger.gui.functions.logger")
def test_notify_and_log(mock_logger, mock_ui_notify):
    msg = "Test message"
    with patch("cbz_tagger.gui.functions.datetime") as mock_datetime:
        mock_datetime.now.return_value = "test_date"
        notify_and_log(msg)
    mock_ui_notify.assert_called_once_with(msg)
    mock_logger.info.assert_called_once_with("%s %s", "test_date", msg)
