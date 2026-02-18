from cbz_tagger.common.get_arg_parser import get_arg_parser


def test_get_arg_parser_no_args(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program"])
    args = get_arg_parser()
    assert args == {
        "entrymode": False,
        "manual": False,
        "refresh": False,
        "add": False,
        "delete": False,
        "remove": False,
    }


def test_get_arg_parser_entrymode(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program", "--entrymode"])
    args = get_arg_parser()
    assert args == {
        "entrymode": True,
        "manual": False,
        "refresh": False,
        "add": False,
        "delete": False,
        "remove": False,
    }


def test_get_arg_parser_manual(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program", "--manual"])
    args = get_arg_parser()
    assert args == {
        "entrymode": False,
        "manual": True,
        "refresh": False,
        "add": False,
        "delete": False,
        "remove": False,
    }


def test_get_arg_parser_refresh(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program", "--refresh"])
    args = get_arg_parser()
    assert args == {
        "entrymode": False,
        "manual": False,
        "refresh": True,
        "add": False,
        "delete": False,
        "remove": False,
    }


def test_get_arg_parser_add(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program", "--add"])
    args = get_arg_parser()
    assert args == {
        "entrymode": False,
        "manual": False,
        "refresh": False,
        "add": True,
        "delete": False,
        "remove": False,
    }


def test_get_arg_parser_delete(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program", "--delete"])
    args = get_arg_parser()
    assert args == {
        "entrymode": False,
        "manual": False,
        "refresh": False,
        "add": False,
        "delete": True,
        "remove": False,
    }


def test_get_arg_parser_remove(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program", "--remove"])
    args = get_arg_parser()
    assert args == {
        "entrymode": False,
        "manual": False,
        "refresh": False,
        "add": False,
        "delete": False,
        "remove": True,
    }


def test_get_arg_parser_multiple_args(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program", "--entrymode", "--manual"])
    args = get_arg_parser()
    assert args == {"entrymode": True, "manual": True, "refresh": False, "add": False, "delete": False, "remove": False}
