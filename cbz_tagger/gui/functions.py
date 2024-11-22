import logging
from datetime import datetime

from nicegui import ui

logger = logging.getLogger()


def refresh_scanner(scanner):
    scanner.run()
    return scanner


def add_new_to_scanner(scanner, entity_name, entity_id, backend, enable_tracking, mark_all_tracked):
    scanner.entity_database.add_entity(
        entity_name,
        entity_id,
        manga_name=None,
        backend=backend,
        update=True,
        track=enable_tracking,
        mark_as_tracked=mark_all_tracked,
    )
    return scanner


def notify_and_log(msg):
    ui.notify(msg)
    logger.info("%s %s", datetime.now(), msg)
