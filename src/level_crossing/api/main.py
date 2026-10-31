"""FastAPI application factory and lifecycle coordinator."""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from level_crossing.common.config import SystemConfig
from level_crossing.common.logger import get_logger
from level_crossing.database.db import DatabaseManager
from level_crossing.api.services.safety_service import SafetyService
from level_crossing.api.routes import health, events, alerts, videos

logger = get_logger("api")


def create_app(config_dir: str = "configs", db_path: str = "data/level_crossing.sqlite3") -> FastAPI:
    """Creates and configures the FastAPI application instance."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        logger.info("Initializing Level Crossing Safety System API...")
        db_manager = DatabaseManager(db_path=db_path)
        safety_service = SafetyService(db_manager=db_manager)
        app.state.db_manager = db_manager
        app.state.safety_service = safety_service
        logger.info("API initialized and operational.")
        yield
        # Shutdown
        logger.info("Shutting down API.")

    app = FastAPI(
        title="Level Crossing Safety Monitoring System API",
        version="3.1.0",
        description="Edge vision safety monitoring, intruder alerting, and telemetry API",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Root endpoint for discovery and probes
    @app.get("/", tags=["Root"])
    def get_root():
        return {
            "system": "Level Crossing Safety Monitoring System API",
            "version": "3.1.0",
            "docs_url": "/docs",
            "health_url": "/health",
            "api_v1_prefix": "/api/v1",
        }

    # Register Health router at both root (/health) and versioned (/api/v1/health)
    app.include_router(health.router)
    app.include_router(health.router, prefix="/api/v1")

    # Register API v1 resource routers
    app.include_router(events.router, prefix="/api/v1")
    app.include_router(alerts.router, prefix="/api/v1")
    app.include_router(videos.router, prefix="/api/v1")

    return app


app = create_app()
