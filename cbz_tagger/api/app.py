"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cbz_tagger.api.entities_router import router as entities_router
from cbz_tagger.api.logs_router import router as logs_router
from cbz_tagger.api.scanner_router import router as scanner_router
from cbz_tagger.api.scheduler import scheduler
from cbz_tagger.api.state import app_state
from cbz_tagger.api.state_router import router as state_router
from cbz_tagger.common.env import AppEnv

logger = logging.getLogger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting CBZ Tagger API")
    env = AppEnv()

    # Initialize scanner if needed
    if env.TIMER_DELAY > 0:
        from cbz_tagger.database.file_scanner import FileScanner

        scanner = FileScanner(
            config_path=env.CONFIG_PATH,
            scan_path=env.SCAN_PATH,
            storage_path=env.STORAGE_PATH,
            add_missing=True,
            environment={
                "PROXY_URL": env.PROXY_URL or "",
                "USE_PROXY": str(env.USE_PROXY),
            },
        )
        app_state.initialize_scanner(scanner)

        # Start background scheduler
        scheduler.delay_seconds = env.TIMER_DELAY
        scheduler.start()
        logger.info("Background scheduler started with delay: %d seconds", env.TIMER_DELAY)

    logger.info("CBZ Tagger API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down CBZ Tagger API")
    await scheduler.stop()
    logger.info("CBZ Tagger API shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="CBZ Tagger API",
        description="Backend API for CBZ Tagger - Comic book file tagging and management",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(scanner_router)
    app.include_router(entities_router)
    app.include_router(logs_router)
    app.include_router(state_router)

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"name": "CBZ Tagger API", "version": "1.0.0", "status": "running"}

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "scanner_initialized": app_state.scanner is not None,
            "database_locked": app_state.scanning_state,
        }

    return app


# Create app instance
app = create_app()
