# Import all plugins to trigger registration with @Plugins.register()
from cbz_tagger.entities.chapter_plugins.cmk import ChapterPluginCMK
from cbz_tagger.entities.chapter_plugins.kal import ChapterPluginKAL
from cbz_tagger.entities.chapter_plugins.mdx import ChapterPluginMDX
from cbz_tagger.entities.chapter_plugins.wbc import ChapterPluginWBC

__all__ = [
    "ChapterPluginCMK",
    "ChapterPluginKAL",
    "ChapterPluginMDX",
    "ChapterPluginWBC",
]
