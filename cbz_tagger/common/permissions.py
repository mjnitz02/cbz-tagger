"""Ownership and mode handling for files written into /storage.

/storage is user data: it is mounted from the host, shared with other
containers and readers, and the user must be able to move or delete anything in
it. So everything written there is chowned to PUID/PGID and chmoded from UMASK.

/config is the container's own appdata. Nothing in here touches it — whoever the
container runs as is the right owner for those files.
"""

import logging
import os

from cbz_tagger.common.env import AppEnv

logger = logging.getLogger()

DEFAULT_UMASK = 0o022


def get_umask() -> int:
    """UMASK as an int. The env var is an octal string ("022"), not decimal."""
    raw = str(AppEnv().UMASK)
    try:
        return int(raw, 8)
    except ValueError:
        logger.error("ERROR >> UMASK %s is not a valid octal mask, falling back to 022", raw)
        return DEFAULT_UMASK


def apply_process_umask() -> int:
    """Set the process umask from the UMASK env var.

    Called once at import time from cbz_tagger/__init__.py. Without this the
    process keeps the default umask it inherited and the UMASK setting does
    nothing at all, which is what shipped up to v5.2.0.
    """
    umask = get_umask()
    os.umask(umask)
    return umask


def get_file_mode() -> int:
    return 0o666 & ~get_umask()


def get_directory_mode() -> int:
    return 0o777 & ~get_umask()


def set_file_ownership(file_path: str) -> None:
    """Apply PUID/PGID ownership and the UMASK-derived mode to a single path."""
    env = AppEnv()
    mode = get_directory_mode() if os.path.isdir(file_path) else get_file_mode()
    try:
        os.chown(file_path, int(env.PUID), int(env.PGID))
        # chmod must follow chown: chown clears the setuid/setgid bits, so
        # doing it the other way round silently drops them again.
        os.chmod(file_path, mode)
    except (PermissionError, FileNotFoundError, OSError) as err:
        logger.error(
            "ERROR >> Unable to set permissions on %s, %s, %s, %o, %s", file_path, env.PUID, env.PGID, mode, err
        )


def _paths_to_own(directory_path: str) -> list[str]:
    """The directory plus every ancestor of it that lives inside /storage.

    Ancestors are included so a series folder gets repaired when a chapter
    folder underneath it is created. The storage mount point itself and
    anything above it are excluded — those belong to the user, not to us.

    Paths outside /storage fall back to just the directory itself.
    """
    path = os.path.abspath(directory_path)
    root = os.path.abspath(AppEnv().STORAGE_PATH)

    paths = []
    while path.startswith(root + os.sep):
        paths.append(path)
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent

    return paths or [os.path.abspath(directory_path)]


def make_directory_with_ownership(directory_path: str) -> None:
    """Create a directory under /storage and (re)apply ownership and mode.

    This runs on every call, not only when the directory is newly created. A
    folder that was made by an older version, by a different container, or by
    hand keeps its wrong mode forever otherwise — which is why libraries drifted
    into needing a manual chown -R across the whole mount.
    """
    os.makedirs(directory_path, exist_ok=True)

    for path in _paths_to_own(directory_path):
        set_file_ownership(path)
