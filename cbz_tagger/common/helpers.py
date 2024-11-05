import logging
import os

from cbz_tagger.common.env import AppEnv

logger = logging.getLogger()


def set_file_ownership(file_path):
    env = AppEnv()
    try:
        os.chown(file_path, int(env.PUID), int(env.PGID))
    except PermissionError as err:
        logger.error("ERROR >> Unable to set permissions on %s, %s, %s, %s", file_path, env.PUID, env.PGID, err)
