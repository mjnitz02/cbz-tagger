import logging
import os

from cbz_tagger.common.env import AppEnv

logger = logging.getLogger()


def get_input_from_list(desc, input_list, allow_negative_exit=False):
    print(desc)
    counter = 0
    items = list(input_list)
    for item in items:
        print(f"{counter + 1}. {item}")
        counter += 1
    choice = get_input(
        "Please select the local and storage name number: ", counter + 1, allow_negative_exit=allow_negative_exit
    )
    if choice <= 0:
        return None
    return choice - 1


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


def set_file_ownership(file_path):
    env = AppEnv()
    try:
        os.chown(file_path, int(env.PUID), int(env.PGID))
    except PermissionError as err:
        logger.error("ERROR >> Unable to set permissions on %s, %s, %s, %s", file_path, env.PUID, env.PGID, err)
