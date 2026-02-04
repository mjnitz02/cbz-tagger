"""Standalone FastAPI server for CBZ Tagger API."""

import logging
import os

from nicegui import app
from nicegui import ui

from cbz_tagger.gui.gui import setup_ui

logger = logging.getLogger(__name__)


def main():
    """Run the FastAPI server."""
    if os.getenv("LOG_LEVEL") is None:
        LOG_LEVEL = logging.INFO
    else:
        LOG_LEVEL = os.getenv("LOG_LEVEL")

    # Configure logging

    logging.basicConfig(level=LOG_LEVEL)
    logger.info("Starting CBZ Tagger NiceGUI server...")

    # Setup global UI configuration
    setup_ui()

    # Run the server
    root_path = os.path.dirname(os.path.abspath(__file__))
    static_path = os.path.join(root_path, "static")
    app.add_static_files("/static", static_path)
    ui.run(reload=False, favicon=os.path.join(static_path, "favicon.ico"))


if __name__ in {"__main__", "__mp_main__"}:
    main()
