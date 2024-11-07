from cbz_tagger.container.gui_container import GuiContainer


def test_nicegui_reload_disabled():
    assert not GuiContainer.NICEGUI_DEBUG
