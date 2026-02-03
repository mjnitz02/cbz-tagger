from cbz_tagger.container import Container


def test_nicegui_reload_disabled():
    assert not Container.NICEGUI_DEBUG
