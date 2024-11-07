import logging
from unittest.mock import MagicMock
from unittest.mock import patch

from cbz_tagger.gui.elements.ui_logger import ui_logger


@patch("cbz_tagger.gui.elements.ui_logger.ui.log")
@patch("cbz_tagger.gui.elements.ui_logger.LogElementHandler")
def test_ui_logger(mock_log_element_handler, mock_ui_log):
    mock_log = MagicMock()
    mock_ui_log.return_value = mock_log
    mock_handler = MagicMock()
    mock_log_element_handler.return_value = mock_handler

    ui_logger()

    mock_ui_log.assert_called_once_with(max_lines=1000)
    mock_log.classes.assert_called_once_with("w-full")
    mock_handler.setLevel.assert_called_once_with(logging.INFO)
