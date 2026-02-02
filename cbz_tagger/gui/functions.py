import logging
from datetime import datetime

from nicegui import ui

logger = logging.getLogger()


def notify_and_log(msg):
    """Helper function to show UI notification and log message."""
    ui.notify(msg)
    logger.info("%s %s", datetime.now(), msg)
