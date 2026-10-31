"""WebSocket Connection Manager for real-time telemetry, detection events, and alerts."""

import json
from typing import List, Dict, Any, Set
from fastapi import WebSocket, WebSocketDisconnect
from level_crossing.common.logger import get_logger

logger = get_logger("websocket_manager")


class WebSocketManager:
    """Manages active WebSocket connections and broadcasts telemetry events."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Active clients: {len(self.active_connections)}")
        # Send initial connection handshake
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to Level Crossing Safety OCC Telemetry Stream",
            "active_clients": len(self.active_connections),
        })

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Active clients: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcasts a JSON message to all connected clients."""
        if not self.active_connections:
            return

        payload = {"type": event_type, "data": data}
        dead_connections: List[WebSocket] = []

        for conn in list(self.active_connections):
            try:
                await conn.send_json(payload)
            except Exception as e:
                logger.warning(f"Error sending to WebSocket client: {e}")
                dead_connections.append(conn)

        for conn in dead_connections:
            self.disconnect(conn)

    def broadcast_sync(self, event_type: str, data: Dict[str, Any]) -> None:
        """Synchronous wrapper for broadcasting from background threads or synchronous callbacks."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(event_type, data), loop)
            else:
                loop.run_until_complete(self.broadcast(event_type, data))
        except RuntimeError:
            # Fallback if no event loop is running in thread
            pass


# Singleton instance
ws_manager = WebSocketManager()
