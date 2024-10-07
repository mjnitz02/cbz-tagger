import os
from json import JSONDecodeError
from time import sleep
from typing import Any
from typing import Dict
from typing import List

import requests

from cbz_tagger.common.enums import MANGADEX_DELAY_PER_REQUEST
from cbz_tagger.common.env import AppEnv


def get_input(desc, max_val, allow_negative_exit=False):
    """Allow selection from a list of inputs"""
    while True:
        user_input = input(desc)
        try:
            user_input = int(user_input)
            if user_input > max_val:
                print("Your input is incorrect! Please try again!")
            elif not allow_negative_exit and user_input <= 0:
                print("Your input is incorrect! Please try again!")
            else:
                return user_input

        except (TypeError, ValueError):
            print("Your input is incorrect! Please try again!")


def get_raw_input(desc):
    """Allow input to be simply mapped in unit testing"""
    return input(desc)


def unpaginate_request(url, query_params=None, limit=50) -> List[Dict[str, Any]]:
    if query_params is None:
        query_params = {}

    response_content = []
    offset = 0
    try:
        while True:
            params = {"limit": limit, "offset": offset}
            params.update(query_params)

            response = requests.get(url, params=params, timeout=60).json()

            response_content.extend(response["data"])

            offset += limit
            if offset >= response["total"]:
                return response_content

            # Only make 2 queries per second
            sleep(MANGADEX_DELAY_PER_REQUEST)
    except JSONDecodeError as exc:
        raise EnvironmentError("Mangadex API is down! Please try again later!") from exc


def set_file_ownership(file_path):
    env = AppEnv()
    try:
        os.chown(file_path, env.PUID, env.PGID)
    except PermissionError:
        print(f"ERROR >> Unable to set permissions on {file_path}, {env.PUID}, {env.PGID}")
