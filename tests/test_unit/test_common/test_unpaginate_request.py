import pytest
import requests
import requests_mock  # pylint: disable=unused-import

from cbz_tagger.common.helpers import unpaginate_request


def test_unpaginate_request_success(requests_mock):
    url = "https://api.example.com/data"
    data = [{"id": 1}, {"id": 2}]
    requests_mock.get(url, json={"data": data, "total": 2})

    result = unpaginate_request(url)
    assert result == data


def test_unpaginate_request_multiple_pages(requests_mock):
    url = "https://api.example.com/data"
    data_page_1 = [{"id": 1}, {"id": 2}]
    data_page_2 = [{"id": 3}, {"id": 4}]
    requests_mock.get(url, [{"json": {"data": data_page_1, "total": 4}}, {"json": {"data": data_page_2, "total": 4}}])

    result = unpaginate_request(url, limit=2)
    assert result == data_page_1 + data_page_2


def test_unpaginate_request_api_down(requests_mock):
    url = "https://api.example.com/data"
    requests_mock.get(url, exc=requests.exceptions.JSONDecodeError("Expecting value", "", 0))

    with pytest.raises(EnvironmentError, match="Mangadex API is down! Please try again later!"):
        unpaginate_request(url)
