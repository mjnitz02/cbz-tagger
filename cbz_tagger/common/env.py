import os

from cbz_tagger.container.enums import ContainerMode


class AppEnv:
    if os.getenv("CONFIG_PATH") is not None:
        CONFIG = os.getenv("CONFIG_PATH")
    else:
        CONFIG = "\\config"

    if os.getenv("DOWNLOADS_PATH") is not None:
        DOWNLOADS = str(os.getenv("DOWNLOADS_PATH"))
    else:
        DOWNLOADS = "\\downloads"

    if os.getenv("STORAGE_PATH") is not None:
        STORAGE = str(os.getenv("STORAGE_PATH"))
    else:
        STORAGE = "\\storage"

    if os.getenv("IMPORT") is not None:
        IMPORT = str(os.getenv("IMPORT"))
    else:
        IMPORT = "\\import"

    if os.getenv("EXPORT") is not None:
        EXPORT = str(os.getenv("EXPORT"))
    else:
        EXPORT = "\\export"

    if os.getenv("ENABLE_TIMER_MODE") == "true":
        CONTAINER_MODE = ContainerMode.TIMER
    elif os.getenv("ENABLE_CONTINUOUS_MODE") == "true":
        CONTAINER_MODE = ContainerMode.CONTINUOUS
    else:
        CONTAINER_MODE = ContainerMode.MANUAL

    if os.getenv("TIMER_MODE_DELAY") is None:
        TIMER_DELAY = 600
    else:
        TIMER_DELAY = int(os.getenv("TIMER_MODE_DELAY"))

    if os.getenv("MOVE_FILES") is None:
        MOVE_FILES = False
    else:
        MOVE_FILES = os.getenv("MOVE_FILES") == "true"
