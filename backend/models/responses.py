"""Response models for API endpoints."""

from backend.models.playlist import Playlist
from backend.models.settings import AllSettings
from backend.models.track import Track
from pydantic import BaseModel
from typing import Any


class LibraryResponse(BaseModel):
    """Response for library listing."""

    tracks: list[Track]
    total: int
    limit: int
    offset: int


class LibraryStats(BaseModel):
    """Library statistics."""

    total_tracks: int
    total_duration: int  # seconds
    total_artists: int
    total_albums: int


class QueueResponse(BaseModel):
    """Response for queue listing."""

    items: list[dict[str, Any]]  # QueueItem serialized
    count: int


class QueueAddResponse(BaseModel):
    """Response when adding tracks to queue."""

    added: int
    queue_length: int


class QueueAddFilesResponse(BaseModel):
    """Response when adding files to queue."""

    added: int
    queue_length: int
    tracks: list[Track]


class PlaylistsResponse(BaseModel):
    """Response for playlists listing."""

    playlists: list[Playlist]


class PlaylistAddTracksResponse(BaseModel):
    """Response when adding tracks to playlist."""

    added: int
    playlist_track_count: int


class FavoritesResponse(BaseModel):
    """Response for favorites listing."""

    tracks: list[Track]
    total: int
    limit: int
    offset: int


class SettingsResponse(BaseModel):
    """Response for settings."""

    settings: AllSettings


class ScanResponse(BaseModel):
    """Response when starting a library scan."""

    status: str
    job_id: str


class ScanProgressEvent(BaseModel):
    """WebSocket event for scan progress."""

    job_id: str
    status: str
    scanned: int
    found: int
    errors: int
    current_path: str | None = None


class ScanCompleteEvent(BaseModel):
    """WebSocket event when scan completes."""

    job_id: str
    added: int
    skipped: int
    errors: int
    duration_ms: int


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    database: str
    uptime_seconds: int
