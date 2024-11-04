from nicegui import ui

from cbz_tagger.common.env import AppEnv


def config_table():
    env = AppEnv()
    columns = [
        {
            "name": "property",
            "label": "property",
            "field": "property",
            "align": "left",
        },
        {
            "name": "value",
            "label": "value",
            "field": "value",
            "align": "left",
        },
    ]
    return ui.table(
        columns=columns,
        rows=[
            {"property": "container_mode", "value": env.CONTAINER_MODE},
            {"property": "config_path", "value": env.CONFIG_PATH},
            {"property": "scan_path", "value": env.SCAN_PATH},
            {"property": "storage_path", "value": env.STORAGE_PATH},
            {"property": "timer_delay", "value": env.TIMER_DELAY},
            {"property": "proxy_url", "value": env.PROXY_URL},
            {"property": "PUID", "value": env.PUID},
            {"property": "PGID", "value": env.PGID},
            {"property": "UMASK", "value": env.UMASK},
        ],
    )
