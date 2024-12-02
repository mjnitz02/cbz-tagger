import logging

from cbz_tagger.common.env import AppEnv

env = AppEnv()
logger = logging.getLogger()
logging.basicConfig(level=env.LOG_LEVEL)
