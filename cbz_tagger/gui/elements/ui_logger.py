import logging

from nicegui import ui

from cbz_tagger import AppEnv
from cbz_tagger.common.log_element_handler import LogElementHandler

logger = logging.getLogger()


def ui_logger():
    env = AppEnv()
    log = ui.log(max_lines=1000).classes("w-full").style("height: 70vh")
    handler = LogElementHandler(log, level=env.LOG_LEVEL)
    logger.addHandler(handler)

    return log
