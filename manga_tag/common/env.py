import os

from manga_tag.container.enums import ContainerMode


class AppEnv(object):
    if os.getenv("CONFIG_PATH") is not None:
        config_path = os.getenv("CONFIG_PATH")
    else:
        config_path = "\\config"

    if os.getenv("DOWNLOADS_PATH") is not None:
        downloads_path = os.getenv("DOWNLOADS_PATH")
    else:
        downloads_path = "\\downloads"

    if os.getenv("STORAGE_PATH") is not None:
        downloads_path = os.getenv("STORAGE_PATH")
    else:
        downloads_path = "\\storage"

    if os.getenv("ENABLE_TIMER_MODE") == "true":
        container_mode = ContainerMode.TIMER
    elif os.getenv("ENABLE_CONTINUOUS_MODE") == "true":
        container_mode = ContainerMode.CONTINUOUS
    else:
        container_mode = ContainerMode.MANUAL

    if os.getenv("TIMER_MODE_DELAY") is None:
        timer_mode_delay = 600
    else:
        timer_mode_delay = int(os.getenv("TIMER_MODE_DELAY"))
