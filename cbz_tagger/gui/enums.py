class EmojiNamespace:
    """Namespace for Emoji constants fetched from the API."""

    CIRCLE_GREEN: str
    CIRCLE_YELLOW: str
    CIRCLE_RED: str
    CIRCLE_BROWN: str
    CHECK_GREEN: str
    QUESTION_MARK: str
    SQUARE_GREEN: str
    SQUARE_RED: str
    SQUARE_ORANGE: str

    def __init__(self, data: dict[str, str]) -> None:
        for key, value in data.items():
            setattr(self, key, value)


class PluginsNamespace:
    """Namespace for Plugins constants and methods fetched from the API."""

    MDX: str
    CMK: str
    WBC: str
    KAL: str
    _all: list[str]

    def __init__(self, data: dict[str, str | list[str]]) -> None:
        all_plugins = data.pop("all", [])
        if isinstance(all_plugins, list):
            self._all = all_plugins
        for key, value in data.items():
            if isinstance(value, str):
                setattr(self, key, value)

    def all(self) -> list[str]:
        return self._all


class EnvNamespace:
    """Namespace for AppEnv configuration fetched from the API."""

    VERSION: str
    CONTAINER_MODE: str
    PUID: int | str
    PGID: int | str
    DEBUG_MODE: bool
    UMASK: str
    CONFIG_PATH: str
    SCAN_PATH: str
    STORAGE_PATH: str
    LOG_PATH: str
    TIMER_DELAY: int
    PROXY_URL: str | None
    DELAY_PER_REQUEST: float
    LOG_LEVEL: int

    def __init__(self, data: dict[str, str | int | float | bool | None]) -> None:
        for key, value in data.items():
            setattr(self, key, value)
