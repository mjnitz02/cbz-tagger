import getpass
import logging
import os
import platform
import pwd

from cbz_tagger.common.enums import ContainerMode


class AppEnv:
    if os.getenv("PUID") is not None:
        PUID = os.getenv("PUID")
    elif platform.system() == "Darwin":
        PUID = pwd.getpwnam(getpass.getuser()).pw_uid
    else:
        PUID = 99

    if os.getenv("PGID") is not None:
        PGID = os.getenv("PGID")
    elif platform.system() == "Darwin":
        PGID = pwd.getpwnam(getpass.getuser()).pw_gid
    else:
        PGID = 100

    if os.getenv("UMASK") is not None:
        UMASK = os.getenv("UMASK")
    else:
        UMASK = "022"

    if os.getenv("CONFIG_PATH") is not None:
        CONFIG_PATH = str(os.getenv("CONFIG_PATH"))
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

    if os.getenv("GUI_MODE") == "true":
        CONTAINER_MODE = ContainerMode.GUI
    elif os.getenv("TIMER_MODE") == "true":
        CONTAINER_MODE = ContainerMode.TIMER
    else:
        CONTAINER_MODE = ContainerMode.MANUAL

    if os.getenv("TIMER_DELAY") is None:
        TIMER_DELAY = 6000
    else:
        TIMER_DELAY = int(os.getenv("TIMER_DELAY"))

    if os.getenv("PROXY_URL") is None:
        PROXY_URL = None
    else:
        PROXY_URL = os.getenv("PROXY_URL")

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
