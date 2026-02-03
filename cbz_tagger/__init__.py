import logging
import os
from logging.handlers import RotatingFileHandler

from cbz_tagger.common.env import AppEnv

env = AppEnv()
logger = logging.getLogger()

# Configure console logging
logging.basicConfig(level=env.LOG_LEVEL)

# Configure file-based logging
log_dir = os.path.dirname(env.LOG_PATH)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

file_handler = RotatingFileHandler(
    env.LOG_PATH,
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=3,
)
file_handler.setLevel(env.LOG_LEVEL)
file_formatter = logging.Formatter(
    "%(asctime)s %(levelname)s:%(filename)s:%(funcName)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
