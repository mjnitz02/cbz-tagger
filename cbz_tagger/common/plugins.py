from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cbz_tagger.entities.plugins.plugin_entity import ChapterPluginEntity


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
