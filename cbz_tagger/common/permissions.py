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


def make_directory_with_ownership(directory_path):
    if not os.path.exists(directory_path):
        # Walk up to find every directory that doesn't exist yet.
        # os.makedirs creates all intermediate dirs, but without this we'd
        # only chown the leaf and intermediate dirs would be owned by the
        # process user (e.g. root) instead of PUID/PGID.
        dirs_to_create = []
        path = os.path.abspath(directory_path)
        while path and not os.path.exists(path):
            dirs_to_create.append(path)
            parent = os.path.dirname(path)
            if parent == path:
                break
            path = parent

        os.makedirs(directory_path, exist_ok=True)

        for dir_path in dirs_to_create:
            set_file_ownership(dir_path)
