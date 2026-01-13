"""WebSocket event models for real-time updates."""

from datetime import datetime
from pydantic import BaseModel
from typing import Any, Literal


class WebSocketMessage(BaseModel):
    """Base WebSocket message format."""

    event: str
    data: dict[str, Any]
    timestamp: datetime


class LibraryUpdatedEvent(BaseModel):
    """Event when library changes."""

    action: Literal["added", "removed", "updated"]
    track_ids: list[int]


class QueueUpdatedEvent(BaseModel):
    """Event when queue changes."""

    action: Literal["added", "removed", "reordered", "cleared", "shuffled"]
    positions: list[int] | None = None
    queue_length: int


class FavoritesUpdatedEvent(BaseModel):
    """Event when favorites change."""

    action: Literal["added", "removed"]
    track_id: int


class PlaylistsUpdatedEvent(BaseModel):
    """Event when playlists change."""

    action: Literal["created", "updated", "deleted", "track_added", "track_removed", "reordered"]
    playlist_id: int
    track_ids: list[int] | None = None


class SettingsUpdatedEvent(BaseModel):
    """Event when settings change."""

    key: str
    value: Any
    previous_value: Any | None = None
