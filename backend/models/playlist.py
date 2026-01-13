"""Playlist models for custom playlist management."""

from backend.models.track import Track
from datetime import datetime
from pydantic import BaseModel, Field


class PlaylistBase(BaseModel):
    """Base playlist model."""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class Playlist(PlaylistBase):
    """Full playlist model with database fields."""

    id: int
    created_date: datetime
    modified_date: datetime
    track_count: int = 0

    class Config:
        from_attributes = True


class PlaylistCreate(PlaylistBase):
    """Model for creating a new playlist."""

    pass


class PlaylistUpdate(BaseModel):
    """Model for updating playlist metadata."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None


class PlaylistTrack(BaseModel):
    """A track in a playlist with position and added date."""

    position: int = Field(ge=0, description="0-indexed position in playlist")
    track: Track
    added_date: datetime


class PlaylistWithTracks(Playlist):
    """Playlist with its tracks included."""

    tracks: list[PlaylistTrack] = []


class PlaylistAddTracksRequest(BaseModel):
    """Request to add tracks to a playlist."""

    track_ids: list[int] = Field(min_length=1, description="Track IDs to add")
    position: int | None = Field(None, ge=0, description="Insert position (null = end)")


class PlaylistReorderRequest(BaseModel):
    """Request to reorder tracks within a playlist."""

    from_position: int = Field(ge=0, description="Current position of track")
    to_position: int = Field(ge=0, description="New position for track")
