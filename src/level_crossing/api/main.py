"""FastAPI application factory and lifecycle coordinator."""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from level_crossing.common.config import SystemConfig
from level_crossing.common.logger import get_logger
from level_crossing.database.db import DatabaseManager
from level_crossing.api.services.safety_service import SafetyService
from level_crossing.api.websocket_manager import ws_manager
from level_crossing.api.routes import health, events, alerts, videos, system, telegram, evidence

logger = get_logger("api")


def create_app(config_dir: str = "configs", db_path: str = "data/level_crossing.sqlite3") -> FastAPI:
    """Creates and configures the FastAPI application instance."""

    db_manager = DatabaseManager(db_path=db_path)
    safety_service = SafetyService(db_manager=db_manager)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        logger.info("Initializing Level Crossing Safety System API...")
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

    # Initialize app.state immediately
    app.state.db_manager = db_manager
    app.state.safety_service = safety_service

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
    app.include_router(system.router, prefix="/api/v1")
    app.include_router(telegram.router, prefix="/api/v1")
    app.include_router(evidence.router, prefix="/api/v1")

    # Real-Time WebSocket Telemetry Gateway
    @app.websocket("/ws/live")
    async def websocket_telemetry_endpoint(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            while True:
                # Keep-alive receive loop
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
        except Exception as e:
            logger.warning(f"WebSocket client error: {e}")
            ws_manager.disconnect(websocket)

    # Production Frontend Static Serving
    dist_dir = Path("web/dist")
    if dist_dir.exists():
        if (dist_dir / "assets").exists():
            app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")
        app.mount("/app", StaticFiles(directory=str(dist_dir), html=True), name="frontend")

    return app


app = create_app()
