import os

from cbz_tagger.common.env import AppEnv
from cbz_tagger.container.container import get_environment_variables


def test_get_environment_variables_defaults():
    """Test the get_environment_variables function with no arguments"""
    env_vars = get_environment_variables()
    assert env_vars["config_path"] == os.path.abspath(AppEnv().CONFIG_PATH)
    assert env_vars["scan_path"] == os.path.abspath(AppEnv().SCAN_PATH)
    assert env_vars["storage_path"] == os.path.abspath(AppEnv().STORAGE_PATH)
    assert env_vars["timer_delay"] == AppEnv().TIMER_DELAY
    assert env_vars["environment"] == AppEnv().get_user_environment()
