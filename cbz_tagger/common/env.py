import os

from cbz_tagger.common.enums import ContainerMode


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
    else:
        CONTAINER_MODE = ContainerMode.MANUAL

    if os.getenv("TIMER_MODE_DELAY") is None:
        TIMER_DELAY = 600
    else:
        TIMER_DELAY = int(os.getenv("TIMER_MODE_DELAY"))
