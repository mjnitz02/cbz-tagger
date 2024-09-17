from cbz_tagger.container.container import get_arg_parser


def test_get_arg_parser_no_args(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program"])
    args = get_arg_parser()
    assert args == {"entrymode": False, "manual": False, "refresh": False, "add": False}


def test_get_arg_parser_entrymode(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program", "--entrymode"])
    args = get_arg_parser()
    assert args == {"entrymode": True, "manual": False, "refresh": False, "add": False}


def test_get_arg_parser_manual(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program", "--manual"])
    args = get_arg_parser()
    assert args == {"entrymode": False, "manual": True, "refresh": False, "add": False}


def test_get_arg_parser_refresh(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program", "--refresh"])
    args = get_arg_parser()
    assert args == {"entrymode": False, "manual": False, "refresh": True, "add": False}


def test_get_arg_parser_add(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program", "--add"])
    args = get_arg_parser()
    assert args == {"entrymode": False, "manual": False, "refresh": False, "add": True}


def test_get_arg_parser_multiple_args(monkeypatch):
    monkeypatch.setattr("sys.argv", ["program", "--entrymode", "--manual"])
    args = get_arg_parser()
    assert args == {"entrymode": True, "manual": True, "refresh": False, "add": False}
