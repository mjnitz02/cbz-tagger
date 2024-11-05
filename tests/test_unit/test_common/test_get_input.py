from cbz_tagger.common.input import get_input
from cbz_tagger.common.input import get_raw_input


def test_valid_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "5")
    assert get_input("Enter a number: ", 10) == 5


def test_input_above_max_val(monkeypatch):
    inputs = iter(["15", "5"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert get_input("Enter a number: ", 10) == 5


def test_negative_input_not_allowed(monkeypatch):
    inputs = iter(["-1", "5"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert get_input("Enter a number: ", 10) == 5


def test_non_integer_input(monkeypatch):
    inputs = iter(["abc", "5"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert get_input("Enter a number: ", 10) == 5


def test_negative_input_allowed(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "-1")
    assert get_input("Enter a number: ", 10, allow_negative_exit=True) == -1


def test_get_raw_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "test input")
    assert get_raw_input("Enter something: ") == "test input"
