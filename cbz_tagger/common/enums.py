import base64
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cbz_tagger.entities.chapter_plugins.plugin import ChapterPluginEntity

APPLICATION_MAJOR_VERSION = 3


class Mode:
    AUTO = "auto"
    MANUAL = "manual"
    RETAG = "retag"
    UPDATE = "update"


class ContainerMode:
    TIMER: str = "timer"
    MANUAL: str = "manual"
    GUI: str = "gui"


class Urls:
    MDX = base64.b64decode("bWFuZ2FkZXgub3Jn").decode("utf-8")
    CMK = base64.b64decode("YXBpLmNvbWljay5mdW4=").decode("utf-8")
    CMK_TITLE = base64.b64decode("Y29taWNrLmlv").decode("utf-8")
    WBC = base64.b64decode("d2VlYmNlbnRyYWwuY29t").decode("utf-8")
    KAL = base64.b64decode("a2FsaXNjYW4uaW8=").decode("utf-8")


class Plugins:
    MDX = "mdx"
    CMK = "cmk"
    WBC = "wbc"
    KAL = "kal"

    TITLE_URLS = {
        MDX: f"https://{Urls.MDX}/title/",
        CMK: f"https://{Urls.CMK_TITLE}/comic/",
        WBC: f"https://{Urls.WBC}/series/",
        KAL: f"https://{Urls.KAL}/manga/",
    }

    # Plugin registry - populated by @Plugins.register() decorator
    _REGISTRY: dict[str, type["ChapterPluginEntity"]] = {}

    @classmethod
    def all(cls):
        return [cls.MDX, cls.WBC, cls.KAL]

    @classmethod
    def register(cls, plugin_type: str):
        """Decorator to register a plugin class.

        Usage:
            @Plugins.register(Plugins.ABC)
            class ChapterPluginABC(ChapterPluginEntity):
                PLUGIN_TYPE = Plugins.ABC
                ...
        """

        def decorator(plugin_cls: type["ChapterPluginEntity"]) -> type["ChapterPluginEntity"]:
            cls._REGISTRY[plugin_type] = plugin_cls
            return plugin_cls

        return decorator

    @classmethod
    def get_plugin(cls, plugin_type: str) -> type["ChapterPluginEntity"]:
        """Get a registered plugin class by type.

        Args:
            plugin_type: The plugin type constant (e.g., Plugins.MDX)

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


IgnoredTags = {
    "ddefd648-5140-4e5f-ba18-4eca4071d19b",
    "2d1f5d56-a1e5-4d0d-a961-2193588b08ec",
}
