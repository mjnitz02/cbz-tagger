from unittest.mock import patch

from cbz_tagger.gui.functions import notify_and_log


@patch("cbz_tagger.gui.functions.ui.notify")
@patch("cbz_tagger.gui.functions.logger")
def test_notify_and_log(mock_logger, mock_ui_notify):
    msg = "Test message"
    with patch("cbz_tagger.gui.functions.datetime") as mock_datetime:
        mock_datetime.now.return_value = "test_date"
        notify_and_log(msg)
    mock_ui_notify.assert_called_once_with(msg)
    mock_logger.info.assert_called_once_with("%s %s", "test_date", msg)
