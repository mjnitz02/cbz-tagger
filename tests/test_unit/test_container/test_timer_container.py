import pytest

from cbz_tagger.container.timer_container import TimerContainer


class MockTimerContainer(TimerContainer):
    """Mock class to allow testing the timer container infinite loop.
    Implement a counter to stop the loop"""

    def __init__(self, config_path, scan_path, storage_path, timer_delay, environment=None):
        super().__init__(config_path, scan_path, storage_path, timer_delay, environment=environment)
        # Attach the mock run method to the scanner
        self.scanner.run = self.mock_run
        self.mock_scans = 0

    def mock_run(self):
        """Mock the run method to count the number of scans"""
        self.mock_scans += 1
        if self.mock_scans == 5:
            raise KeyboardInterrupt


def test_timer_container(config_path, scan_path, storage_path):
    container = MockTimerContainer(config_path, scan_path, storage_path, 0.01)

    # We want to attach to the infinite loop and allow it to be killed
    with pytest.raises(KeyboardInterrupt):
        container.run()
    assert container.mock_scans == 5
