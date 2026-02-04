"""Standalone FastAPI server for CBZ Tagger API."""

import logging
import os

from nicegui import app
from nicegui import ui

from cbz_tagger.common.env import AppEnv
from cbz_tagger.gui.gui import SimpleGui

logger = logging.getLogger(__name__)


def main():
    """Run the FastAPI server."""
    env = AppEnv()

    # Configure logging

    logging.basicConfig(level=env.LOG_LEVEL)

    logger.info("Starting CBZ Tagger NiceGUI server...")
    logger.info("Config path: %s", env.CONFIG_PATH)
    logger.info("Scan path: %s", env.SCAN_PATH)
    logger.info("Storage path: %s", env.STORAGE_PATH)

    # Run the server
    SimpleGui()
    root_path = os.path.dirname(os.path.abspath(__file__))
    static_path = os.path.join(root_path, "static")
    app.add_static_files("/static", static_path)
    ui.run(reload=env.DEBUG_MODE, favicon=os.path.join(static_path, "favicon.ico"))


if __name__ == "__main__":
    main()
