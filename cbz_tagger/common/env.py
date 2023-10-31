import os

from cbz_tagger.common.enums import ContainerMode


class AppEnv:
    if os.getenv("CONFIG_PATH") is not None:
        CONFIG_PATH = os.getenv("CONFIG_PATH")
    else:
        CONFIG_PATH = "\\config"

    if os.getenv("SCAN_PATH") is not None:
        SCAN_PATH = str(os.getenv("SCAN_PATH"))
    else:
        SCAN_PATH = "\\scan"

    if os.getenv("STORAGE_PATH") is not None:
        STORAGE_PATH = str(os.getenv("STORAGE_PATH"))
    else:
        STORAGE_PATH = "\\storage"

    if os.getenv("TIMER_MODE") == "true":
        CONTAINER_MODE = ContainerMode.TIMER
    else:
        CONTAINER_MODE = ContainerMode.MANUAL

    if os.getenv("TIMER_DELAY") is None:
        TIMER_DELAY = 600
    else:
        TIMER_DELAY = int(os.getenv("TIMER_DELAY"))
