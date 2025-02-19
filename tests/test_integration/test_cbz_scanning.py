import os
from unittest import mock


@mock.patch("cbz_tagger.common.input.get_input")
def test_process_cbz_files(mock_get_input, integration_scanner, build_test_cbz):
    """This test will generate a fake cached cbz file, and then process it with the scanner.
    The output should place the cleaned and parsed file into the storage after hitting all the
    real APIs. Inputs are mocked to automatically select a template manga and chapter."""

    def capture_input(test_input, *args, **kwargs):
        _ = args, kwargs
        if test_input == "Please select the manga that you are searching for in number: ":
            return 1
        if test_input == "Please select the local and storage name number: ":
            return 1
        return 0

    mock_get_input.side_effect = capture_input

    # Create a test cbz file for chapter 1, automatically select the metadata and process it
    build_test_cbz(1)
    integration_scanner.run_scan()

    # Assert the scanned files are all processed
    assert len(os.listdir(os.path.join(integration_scanner.config_path, "images"))) == 2
    assert os.listdir(integration_scanner.scan_path) == []
    storage_results = [
        os.path.relpath(str(os.path.join(root, name)), integration_scanner.storage_path)
        for root, dirs, files in os.walk(integration_scanner.storage_path)
        for name in files
    ]
    assert set(storage_results) == {
        "Touto Sugite Yome na a a a a a a i 4P Short Stories/"
        "Touto Sugite Yome na a a a a a a i 4P Short Stories - Chapter 001.cbz",
        "Touto Sugite Yome na a a a a a a i 4P Short Stories/series.json"
    }

    # Create a test cbz file for chapter 2, use existing metadata and process it
    build_test_cbz(2)
    integration_scanner.add_missing = False
    integration_scanner.run_scan()
    storage_results = [
        os.path.relpath(str(os.path.join(root, name)), integration_scanner.storage_path)
        for root, dirs, files in os.walk(integration_scanner.storage_path)
        for name in files
    ]
    assert set(storage_results) == {
        "Touto Sugite Yome na a a a a a a i 4P Short Stories/"
        "Touto Sugite Yome na a a a a a a i 4P Short Stories - Chapter 001.cbz",
        "Touto Sugite Yome na a a a a a a i 4P Short Stories/"
        "Touto Sugite Yome na a a a a a a i 4P Short Stories - Chapter 002.cbz",
        "Touto Sugite Yome na a a a a a a i 4P Short Stories/series.json",
    }


def test_process_cbz_files_with_no_files(integration_scanner):
    """This test will process the full scanner when no outputs are present. It should do nothing."""
    integration_scanner.process = mock.MagicMock()
    integration_scanner.run_scan()
    integration_scanner.process.assert_not_called()
