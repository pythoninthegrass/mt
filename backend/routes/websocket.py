"""WebSocket endpoint for real-time events."""

import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Any

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections for broadcasting events."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event: str, data: dict[str, Any]):
        """Broadcast an event to all connected clients."""
        message = {
            "event": event,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        message_json = json.dumps(message)

        # Send to all connections, removing any that fail
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


# Global connection manager
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager."""
    return manager


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time events."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, handle any incoming messages
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo back for ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
            except TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({"event": "heartbeat", "timestamp": datetime.utcnow().isoformat() + "Z"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# Helper functions for broadcasting events from routes
async def emit_library_updated(action: str, track_ids: list[int]):
    """Emit library:updated event."""
    await manager.broadcast("library:updated", {"action": action, "track_ids": track_ids})


async def emit_queue_updated(action: str, positions: list[int] | None = None, queue_length: int = 0):
    """Emit queue:updated event."""
    await manager.broadcast(
        "queue:updated",
        {"action": action, "positions": positions, "queue_length": queue_length},
    )


async def emit_favorites_updated(action: str, track_id: int):
    """Emit favorites:updated event."""
    await manager.broadcast("favorites:updated", {"action": action, "track_id": track_id})


async def emit_playlists_updated(action: str, playlist_id: int, track_ids: list[int] | None = None):
    """Emit playlists:updated event."""
    await manager.broadcast(
        "playlists:updated",
        {"action": action, "playlist_id": playlist_id, "track_ids": track_ids},
    )


async def emit_settings_updated(key: str, value: Any, previous_value: Any = None):
    """Emit settings:updated event."""
    await manager.broadcast(
        "settings:updated",
        {"key": key, "value": value, "previous_value": previous_value},
    )


async def emit_scan_progress(job_id: str, status: str, scanned: int, found: int, errors: int, current_path: str | None = None):
    """Emit library:scan-progress event."""
    await manager.broadcast(
        "library:scan-progress",
        {
            "job_id": job_id,
            "status": status,
            "scanned": scanned,
            "found": found,
            "errors": errors,
            "current_path": current_path,
        },
    )


async def emit_scan_complete(job_id: str, added: int, skipped: int, errors: int, duration_ms: int):
    """Emit library:scan-complete event."""
    await manager.broadcast(
        "library:scan-complete",
        {
            "job_id": job_id,
            "added": added,
            "skipped": skipped,
            "errors": errors,
            "duration_ms": duration_ms,
        },
    )
