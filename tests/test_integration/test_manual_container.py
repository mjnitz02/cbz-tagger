from unittest import mock

import pytest

from cbz_tagger.container.manual_container import ManualContainer


@mock.patch("time.sleep")
def test_timer_container(mock_time_sleep, config_path, scan_path, storage_path):
    container = ManualContainer(config_path, scan_path, storage_path, 0.01)
    mock_time_sleep.side_effect = KeyboardInterrupt

    # We want to let the infinite loop be killed
    with pytest.raises(KeyboardInterrupt):
        container.run()

    mock_time_sleep.assert_called_once()
