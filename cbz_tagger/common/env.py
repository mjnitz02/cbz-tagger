import os

from cbz_tagger.common.enums import ContainerMode


class AppEnv:
    if os.getenv("PUID") is not None:
        PUID = os.getenv("PUID")
    else:
        PUID = "99"

    if os.getenv("PGID") is not None:
        PGID = os.getenv("PGID")
    else:
        PGID = "100"

    if os.getenv("UMASK") is not None:
        UMASK = os.getenv("UMASK")
    else:
        UMASK = "022"

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
        TIMER_DELAY = 6000
    else:
        TIMER_DELAY = int(os.getenv("TIMER_DELAY"))

    def get_user_environment(self):
        return {
            "PUID": self.PUID,
            "PGID": self.PGID,
            "UMASK": self.UMASK,
        }
