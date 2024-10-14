import argparse
import os

from cbz_tagger.common.enums import ContainerMode
from cbz_tagger.common.env import AppEnv
from cbz_tagger.container.manual_container import ManualContainer
from cbz_tagger.container.timer_container import TimerContainer


def get_arg_parser():
    """Argparse for the container"""
    parser = argparse.ArgumentParser(description="Manga Tagger")
    parser.add_argument("--entrymode", help="Container Entrymode Start", action="store_true")
    parser.add_argument("--manual", help="Manual Mode", action="store_true")
    parser.add_argument("--refresh", help="Refresh Mode", action="store_true")
    parser.add_argument("--add", help="Add Tracked Mode", action="store_true")
    parser.add_argument("--remove", help="Remove Tracked Mode", action="store_true")
    kwargs = vars(parser.parse_args())
    return kwargs


def get_environment_variables():
    """Collect the environment variables and paths required for the containers
    to determine the runtime modes

    Returns
    -------
    env_vars : dict
            Environment variables as a dictionary
    """
    env = AppEnv()
    env_vars = {
        "config_path": os.path.abspath(env.CONFIG_PATH),
        "scan_path": os.path.abspath(env.SCAN_PATH),
        "storage_path": os.path.abspath(env.STORAGE_PATH),
        "timer_delay": env.TIMER_DELAY,
        "environment": env.get_user_environment(),
    }

    print("Environment Variables:")
    print(env_vars)
    print(f"proxy_url: {env.PROXY_URL}")

    return env_vars


def run_container(**kwargs):
    """Execute the internal container as timer or manual after collecting the environment
    variables and parsing the arguments.

    Parameters
    ----------
    kwargs : dict
        Dictionary from get_arg_parser() containing command line inputs
    """

    print("CBZ Tagger v2.0")
    print("----------------------")

    env_vars = get_environment_variables()

    if kwargs.get("entrymode"):
        container_mode = AppEnv.CONTAINER_MODE
        if container_mode == ContainerMode.TIMER:
            container = TimerContainer(**env_vars)
        else:
            container = ManualContainer(**env_vars)
        container.run()
    else:
        container = ManualContainer(**env_vars)
        if kwargs.get("add"):
            container.scanner.add_tracked_entity()
        if kwargs.get("remove"):
            container.scanner.remove_tracked_entity()
        if kwargs.get("delete"):
            container.scanner.delete_entity()
        elif kwargs.get("refresh"):
            container.scanner.refresh()
        else:
            container.scanner.run()
