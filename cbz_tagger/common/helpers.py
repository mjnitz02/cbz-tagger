import os

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


def set_file_ownership(file_path):
    env = AppEnv()
    try:
        os.chown(file_path, int(env.PUID), int(env.PGID))
    except PermissionError as err:
        print(f"ERROR >> Unable to set permissions on {file_path}, {env.PUID}, {env.PGID}", err)
