import base64
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cbz_tagger.entities.plugins.plugin_entity import ChapterPluginEntity

APPLICATION_MAJOR_VERSION = 4


class Urls:
    MDX = base64.b64decode("bWFuZ2FkZXgub3Jn").decode("utf-8")


class Plugins:
    DEFAULT = "mdx"
    TITLE_URLS = {}

    # Plugin registry - populated by @Plugins.register() decorator
    _REGISTRY: dict[str, type["ChapterPluginEntity"]] = {}

    @classmethod
    def to_api(cls):
        return {
            "DEFAULT": cls.DEFAULT,
            "all": cls.all(),
        }

    @classmethod
    def all(cls):
        return list(cls._REGISTRY.keys())

    @classmethod
    def register(cls, plugin_type: str):
        """Decorator to register a plugin class.

        Usage:
            @Plugins.register("abc")  # Registers the plugin with type "abc"
            class ChapterPluginABC(ChapterPluginEntity):
                # Plugin implementation...
                BASE_URL = "http://abc.com"
                TITLE_URL = "http://abc.com/title/"
                ...
        """

        def decorator(plugin_cls: type["ChapterPluginEntity"]) -> type["ChapterPluginEntity"]:
            plugin_cls.PLUGIN_TYPE = plugin_type
            cls._REGISTRY[plugin_type] = plugin_cls
            if plugin_cls.TITLE_URL:
                cls.TITLE_URLS[plugin_type] = plugin_cls.TITLE_URL
            return plugin_cls

        return decorator

    @classmethod
    def get_plugin(cls, plugin_type: str) -> type["ChapterPluginEntity"]:
        """Get a registered plugin class by type.

        Args:
            plugin_type: The plugin type constant (e.g., Plugins.DEFAULT)

        Returns:
            The plugin class

        Raises:
            KeyError: If plugin type is not registered
        """
        if plugin_type not in cls._REGISTRY:
            raise KeyError(f"Plugin '{plugin_type}' not registered. Available: {list(cls._REGISTRY.keys())}")
        return cls._REGISTRY[plugin_type]


class Status:
    ONGOING = "ongoing"
    COMPLETED = "completed"
    HIATUS = "hiatus"
    CANCELLED = "cancelled"
    DROPPED = "dropped"


class Emoji:
    CIRCLE_GREEN = "🟢"
    CIRCLE_YELLOW = "🟡"
    CIRCLE_RED = "🔴"
    CIRCLE_BROWN = "🟤"
    CHECK_GREEN = "✅"
    QUESTION_MARK = "❓"
    SQUARE_GREEN = "🟩"
    SQUARE_RED = "🟥"
    SQUARE_ORANGE = "🟧"

    @classmethod
    def to_api(cls):
        return {
            "CIRCLE_GREEN": cls.CIRCLE_GREEN,
            "CIRCLE_YELLOW": cls.CIRCLE_YELLOW,
            "CIRCLE_RED": cls.CIRCLE_RED,
            "CIRCLE_BROWN": cls.CIRCLE_BROWN,
            "CHECK_GREEN": cls.CHECK_GREEN,
            "QUESTION_MARK": cls.QUESTION_MARK,
            "SQUARE_GREEN": cls.SQUARE_GREEN,
            "SQUARE_RED": cls.SQUARE_RED,
            "SQUARE_ORANGE": cls.SQUARE_ORANGE,
        }


IgnoredTags = {
    "ddefd648-5140-4e5f-ba18-4eca4071d19b",
    "2d1f5d56-a1e5-4d0d-a961-2193588b08ec",
}
