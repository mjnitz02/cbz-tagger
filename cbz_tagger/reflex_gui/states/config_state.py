"""Config state for displaying server configuration."""

import logging

from cbz_tagger.common.env import AppEnv
from cbz_tagger.reflex_gui.states.base_state import BaseState

logger = logging.getLogger()


class ConfigState(BaseState):
    """State for the config page.

    Manages:
    - Display of server configuration
    """

    config_data: list[dict] = []
    is_loaded: bool = False

    async def load_config(self):
        """Load configuration from environment."""
        env = AppEnv()

        self.config_data = [
            {"property": "container_mode", "value": str(env.CONTAINER_MODE)},
            {"property": "config_path", "value": str(env.CONFIG_PATH)},
            {"property": "scan_path", "value": str(env.SCAN_PATH)},
            {"property": "storage_path", "value": str(env.STORAGE_PATH)},
            {"property": "timer_delay", "value": str(env.TIMER_DELAY)},
            {"property": "proxy_url", "value": str(env.PROXY_URL)},
            {"property": "PUID", "value": str(env.PUID)},
            {"property": "PGID", "value": str(env.PGID)},
            {"property": "UMASK", "value": str(env.UMASK)},
            {"property": "LOG_LEVEL", "value": str(env.LOG_LEVEL)},
        ]

        logger.debug("Config loaded: %d items", len(self.config_data))
        for item in self.config_data:
            logger.debug("Config item: %s = %s", item["property"], item["value"])

        self.is_loaded = True
