"""Pydantic models for the mt music player API."""

from backend.models.events import (
    FavoritesUpdatedEvent,
    LibraryUpdatedEvent,
    PlaylistsUpdatedEvent,
    QueueUpdatedEvent,
    SettingsUpdatedEvent,
    WebSocketMessage,
)
from backend.models.favorites import FavoriteAddResponse, FavoriteStatus
from backend.models.playlist import (
    Playlist,
    PlaylistAddTracksRequest,
    PlaylistCreate,
    PlaylistReorderRequest,
    PlaylistTrack,
    PlaylistUpdate,
    PlaylistWithTracks,
)
from backend.models.queue import (
    QueueAddFilesRequest,
    QueueAddRequest,
    QueueItem,
    QueueReorderRequest,
    QueueShuffleRequest,
)
from backend.models.responses import (
    ErrorResponse,
    FavoritesResponse,
    HealthResponse,
    LibraryResponse,
    LibraryStats,
    PlaylistAddTracksResponse,
    PlaylistsResponse,
    QueueAddFilesResponse,
    QueueAddResponse,
    QueueResponse,
    ScanCompleteEvent,
    ScanProgressEvent,
    ScanResponse,
    SettingsResponse,
)
from backend.models.settings import AllSettings, Setting, SettingsUpdate
from backend.models.track import Track, TrackCreate, TrackUpdate, TrackWithFavorite, TrackWithPlayCount

__all__ = [
    # Track models
    "Track",
    "TrackCreate",
    "TrackUpdate",
    "TrackWithFavorite",
    "TrackWithPlayCount",
    # Queue models
    "QueueItem",
    "QueueAddRequest",
    "QueueAddFilesRequest",
    "QueueReorderRequest",
    "QueueShuffleRequest",
    # Playlist models
    "Playlist",
    "PlaylistCreate",
    "PlaylistUpdate",
    "PlaylistTrack",
    "PlaylistWithTracks",
    "PlaylistAddTracksRequest",
    "PlaylistReorderRequest",
    # Favorites models
    "FavoriteStatus",
    "FavoriteAddResponse",
    # Settings models
    "Setting",
    "SettingsUpdate",
    "AllSettings",
    # Response models
    "LibraryResponse",
    "LibraryStats",
    "QueueResponse",
    "QueueAddResponse",
    "QueueAddFilesResponse",
    "PlaylistsResponse",
    "PlaylistAddTracksResponse",
    "FavoritesResponse",
    "SettingsResponse",
    "ScanResponse",
    "ScanProgressEvent",
    "ScanCompleteEvent",
    "ErrorResponse",
    "HealthResponse",
    # Event models
    "WebSocketMessage",
    "LibraryUpdatedEvent",
    "QueueUpdatedEvent",
    "FavoritesUpdatedEvent",
    "PlaylistsUpdatedEvent",
    "SettingsUpdatedEvent",
]
