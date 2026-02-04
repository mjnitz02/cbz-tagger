"""Standalone FastAPI server for CBZ Tagger API."""

import logging

import uvicorn

from cbz_tagger.common.env import AppEnv

logger = logging.getLogger(__name__)


def main():
    """Run the FastAPI server."""
    env = AppEnv()

    # Configure logging

    logging.basicConfig(level=env.LOG_LEVEL)

    logger.info("Starting CBZ Tagger API server...")
    logger.info("Config path: %s", env.CONFIG_PATH)
    logger.info("Scan path: %s", env.SCAN_PATH)
    logger.info("Storage path: %s", env.STORAGE_PATH)

    # Run the server
    uvicorn.run(
        "cbz_tagger.web.api:app",
        host="0.0.0.0",
        port=8000,
        reload=env.DEBUG_MODE,  # Enable auto-reload for development
        log_level=env.LOG_LEVEL,
    )


if __name__ == "__main__":
    main()
