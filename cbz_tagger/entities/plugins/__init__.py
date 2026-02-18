# Import all plugins to trigger registration with @Plugins.register()
from cbz_tagger.entities.plugins.cmk import ChapterPluginCMK
from cbz_tagger.entities.plugins.kal import ChapterPluginKAL
from cbz_tagger.entities.plugins.mdx import ChapterPluginMDX
from cbz_tagger.entities.plugins.wbc import ChapterPluginWBC

__all__ = [
    "ChapterPluginCMK",
    "ChapterPluginKAL",
    "ChapterPluginMDX",
    "ChapterPluginWBC",
]
