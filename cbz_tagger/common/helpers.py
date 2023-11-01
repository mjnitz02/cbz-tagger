from time import sleep
from typing import Any
from typing import Dict
from typing import List

import requests


def get_input(desc, max_val):
    while True:
        user_input = input(desc)
        try:
            user_input = int(user_input)
            if user_input <= 0 or user_input > max_val:
                print("Your input is incorrect! Please try again!")
            else:
                return user_input

        except (TypeError, ValueError):
            print("Your input is incorrect! Please try again!")


def unpaginate_request(url, query_params=None, limit=50) -> List[Dict[str, Any]]:
    if query_params is None:
        query_params = {}

    response_content = []
    offset = 0
    while True:
        params = {"limit": limit, "offset": offset}
        params.update(query_params)

        response = requests.get(url, params=params, timeout=60).json()

        response_content.extend(response["data"])

        offset += limit
        if offset > response["total"]:
            return response_content

        # Only make 2 queries per second
        sleep(0.5)
