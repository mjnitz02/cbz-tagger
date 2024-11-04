import logging

from nicegui import ui

from cbz_tagger.common.log_element_handler import LogElementHandler

logger = logging.getLogger()


def ui_logger():
    log = ui.log(max_lines=1000).classes("w-full").style("height: 70vh")
    handler = LogElementHandler(log)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    return log
