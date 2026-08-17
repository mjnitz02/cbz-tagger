import os
import stat
from unittest.mock import patch

import pytest

from cbz_tagger.common import permissions
from cbz_tagger.common.permissions import get_directory_mode
from cbz_tagger.common.permissions import get_file_mode
from cbz_tagger.common.permissions import get_umask
from cbz_tagger.common.permissions import make_directory_with_ownership
from cbz_tagger.common.permissions import set_file_ownership


def mode_of(path):
    return stat.S_IMODE(os.stat(path).st_mode)


@pytest.fixture
def umask(request):
    """Run the permissions module as if UMASK were set to the given octal string."""
    with patch.object(permissions.AppEnv, "UMASK", request.param):
        yield request.param


@pytest.fixture
def storage(tmp_path):
    """Point STORAGE_PATH at a temp dir and neuter chown, which needs root."""
    root = tmp_path / "storage"
    root.mkdir()
    with patch.object(permissions.AppEnv, "STORAGE_PATH", str(root)):
        # chown to an arbitrary uid/gid is not permitted for a normal test user,
        # so the ownership half is asserted via the call and the mode half for real.
        with patch("cbz_tagger.common.permissions.os.chown") as chown:
            yield root, chown


@pytest.mark.parametrize("umask", ["022"], indirect=True)
def test_umask_is_parsed_as_octal_not_decimal(umask):
    # "022" read as decimal would be 22 (0o26) and produce nonsense modes.
    assert get_umask() == 0o022
    assert get_directory_mode() == 0o755
    assert get_file_mode() == 0o644


@pytest.mark.parametrize("umask", ["002"], indirect=True)
def test_group_writable_umask_produces_group_writable_modes(umask):
    assert get_directory_mode() == 0o775
    assert get_file_mode() == 0o664


@pytest.mark.parametrize("umask", ["nonsense"], indirect=True)
def test_invalid_umask_falls_back_to_default(umask):
    assert get_umask() == 0o022


@pytest.mark.parametrize("umask", ["002"], indirect=True)
def test_directory_is_created_with_mode_and_ownership(umask, storage):
    root, chown = storage
    target = root / "Series Name"

    make_directory_with_ownership(str(target))

    assert target.is_dir()
    assert mode_of(target) == 0o775
    chown.assert_called()


@pytest.mark.parametrize("umask", ["002"], indirect=True)
def test_existing_directory_with_wrong_mode_is_repaired(umask, storage):
    """The regression that forced a manual chown -R across /storage.

    Older versions only applied ownership when they created the directory, so a
    folder that was once wrong stayed wrong for every chapter written into it.
    """
    root, _ = storage
    target = root / "Series Name"
    target.mkdir()
    os.chmod(target, 0o700)

    make_directory_with_ownership(str(target))

    assert mode_of(target) == 0o775


@pytest.mark.parametrize("umask", ["002"], indirect=True)
def test_ancestors_inside_storage_are_repaired_but_the_mount_is_not(umask, storage):
    root, _ = storage
    series = root / "Series Name"
    series.mkdir()
    os.chmod(series, 0o700)
    os.chmod(root, 0o700)

    make_directory_with_ownership(str(series / "Chapter 001"))

    assert mode_of(series / "Chapter 001") == 0o775
    # The intermediate series folder is healed on the way past.
    assert mode_of(series) == 0o775
    # The storage mount itself belongs to the user and is left alone.
    assert mode_of(root) == 0o700


@pytest.mark.parametrize("umask", ["002"], indirect=True)
def test_file_gets_file_mode_not_directory_mode(umask, storage):
    root, chown = storage
    target = root / "chapter.cbz"
    target.write_text("data")
    os.chmod(target, 0o600)

    set_file_ownership(str(target))

    # 0o664, not 0o775 — files must not come out executable.
    assert mode_of(target) == 0o664
    chown.assert_called_once()


@pytest.mark.parametrize("umask", ["002"], indirect=True)
def test_missing_path_is_logged_and_does_not_raise(umask, storage):
    root, _ = storage
    set_file_ownership(str(root / "does-not-exist.cbz"))
