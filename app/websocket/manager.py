"""WebSocket connection manager for real-time updates."""

import json
from fastapi import WebSocket
from typing import Dict, List, Set


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.room_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str | None = None):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

        if room is not None:
            if room not in self.room_connections:
                self.room_connections[room] = set()
            self.room_connections[room].add(websocket)

    def disconnect(self, websocket: WebSocket, room: str | None = None):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        if room is not None and room in self.room_connections:
            self.room_connections[room].discard(websocket)
            if not self.room_connections[room]:
                del self.room_connections[room]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        await websocket.send_text(message)

    async def send_json(self, data: dict, websocket: WebSocket):
        """Send JSON data to a specific WebSocket."""
        await websocket.send_json(data)

    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection might be closed
                pass

    async def broadcast_json(self, data: dict):
        """Broadcast JSON data to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except:
                # Connection might be closed
                pass

    async def broadcast_to_room(self, room: str, message: str):
        """Broadcast a message to all clients in a specific room."""
        if room in self.room_connections:
            for connection in self.room_connections[room]:
                try:
                    await connection.send_text(message)
                except:
                    # Connection might be closed
                    pass

    async def broadcast_json_to_room(self, room: str, data: dict):
        """Broadcast JSON data to all clients in a specific room."""
        if room in self.room_connections:
            for connection in self.room_connections[room]:
                try:
                    await connection.send_json(data)
                except:
                    # Connection might be closed
                    pass


# Global connection manager instance
manager = ConnectionManager()


class EventTypes:
    """WebSocket event types."""

    # Player events
    PLAYBACK_STARTED = "playback_started"
    PLAYBACK_PAUSED = "playback_paused"
    PLAYBACK_STOPPED = "playback_stopped"
    TRACK_CHANGED = "track_changed"
    SEEK_UPDATED = "seek_updated"
    VOLUME_CHANGED = "volume_changed"

    # Queue events
    QUEUE_UPDATED = "queue_updated"
    QUEUE_CLEARED = "queue_cleared"
    TRACK_ADDED = "track_added"
    TRACK_REMOVED = "track_removed"

    # Library events
    LIBRARY_SCAN_STARTED = "library_scan_started"
    LIBRARY_SCAN_PROGRESS = "library_scan_progress"
    LIBRARY_SCAN_COMPLETED = "library_scan_completed"
    LIBRARY_UPDATED = "library_updated"

    # Error events
    ERROR = "error"


async def broadcast_player_event(event_type: str, data: dict):
    """Broadcast a player event to all connected clients."""
    await manager.broadcast_json({"type": event_type, "data": data})


async def broadcast_queue_event(event_type: str, queue_name: str, data: dict):
    """Broadcast a queue event to clients in the queue room."""
    await manager.broadcast_json_to_room(f"queue:{queue_name}", {"type": event_type, "queue": queue_name, "data": data})


async def broadcast_library_event(event_type: str, data: dict):
    """Broadcast a library event to all connected clients."""
    await manager.broadcast_json({"type": event_type, "data": data})
