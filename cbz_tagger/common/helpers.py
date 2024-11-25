import logging
import os
import shutil

from cbz_tagger.common.env import AppEnv

logger = logging.getLogger()


def set_file_ownership(file_path):
    env = AppEnv()
    try:
        os.chown(file_path, int(env.PUID), int(env.PGID))
    except PermissionError as err:
        logger.error("ERROR >> Unable to set permissions on %s, %s, %s, %s", file_path, env.PUID, env.PGID, err)


def make_directory_with_ownership(directory_path):
    env = AppEnv()
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        # Attempt to fix permissions on the directory if newly created
        try:
            shutil.chown(directory_path, user=env.PUID, group=env.PGID)
        except PermissionError as err:
            logger.error("ERROR >> Unable to create directory %s, %s", directory_path, err)
