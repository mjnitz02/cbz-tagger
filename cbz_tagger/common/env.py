import getpass
import logging
import os
import platform
import pwd

from cbz_tagger.common.enums import ContainerMode
from cbz_tagger.common.version import extract_version


class AppEnv:
    VERSION = extract_version()

    if os.getenv("GUI_MODE") == "true":
        CONTAINER_MODE = ContainerMode.GUI
    elif os.getenv("TIMER_MODE") == "true":
        CONTAINER_MODE = ContainerMode.TIMER
    else:
        CONTAINER_MODE = ContainerMode.MANUAL

    if platform.system() == "Darwin":
        PUID = os.getenv("PUID", pwd.getpwnam(getpass.getuser()).pw_uid)
        PGID = os.getenv("PGID", pwd.getpwnam(getpass.getuser()).pw_gid)
    else:
        PUID = os.getenv("PUID", 99)
        PGID = os.getenv("PGID", 100)

    UMASK: str = os.getenv("UMASK", "022")
    CONFIG_PATH: str = str(os.getenv("CONFIG_PATH", "\\config"))
    SCAN_PATH: str = str(os.getenv("SCAN_PATH", "\\scan"))
    STORAGE_PATH: str = str(os.getenv("STORAGE_PATH", "\\storage"))
    LOG_PATH: str = str(os.getenv("LOG_PATH", os.path.join(CONFIG_PATH, "logs", "cbz_tagger.log")))
    TIMER_DELAY: int = int(os.getenv("TIMER_DELAY", 6000))
    PROXY_URL: str | None = os.getenv("PROXY_URL", None)
    DELAY_PER_REQUEST: float = float(os.getenv("DELAY_PER_REQUEST", 0.5))

    if os.getenv("LOG_LEVEL") is None:
        LOG_LEVEL = logging.INFO
    else:
        level = os.getenv("LOG_LEVEL")
        if level == "DEBUG":
            LOG_LEVEL = logging.DEBUG
        elif level == "INFO":
            LOG_LEVEL = logging.INFO
        elif level == "WARNING":
            LOG_LEVEL = logging.WARNING
        elif level == "ERROR":
            LOG_LEVEL = logging.ERROR
        else:
            LOG_LEVEL = logging.INFO

    def get_user_environment(self):
        return {
            "PUID": self.PUID,
            "PGID": self.PGID,
            "UMASK": self.UMASK,
        }
