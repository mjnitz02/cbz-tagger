"""FastAPI backend server entry point."""

import logging

import uvicorn

from cbz_tagger.common.env import AppEnv

logger = logging.getLogger()


def main():
    """Run the FastAPI server."""
    env = AppEnv()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    logger.info("Starting CBZ Tagger API Server")
    logger.info("Config Path: %s", env.CONFIG_PATH)
    logger.info("Scan Path: %s", env.SCAN_PATH)
    logger.info("Storage Path: %s", env.STORAGE_PATH)
    logger.info("Timer Delay: %s seconds", env.TIMER_DELAY)

    # Run uvicorn server
    uvicorn.run(
        "cbz_tagger.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True for development
        log_level="info",
    )


if __name__ == "__main__":
    main()
