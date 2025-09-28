"""Track schemas for API validation."""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class TrackBase(BaseModel):
    """Base track schema."""

    title: str
    artist: str | None = None
    album: str | None = None
    album_artist: str | None = None
    genre: str | None = None
    year: int | None = None
    track_number: int | None = None
    disc_number: int | None = None
    comment: str | None = None


class TrackCreate(TrackBase):
    """Schema for creating a track."""

    file_path: str
    file_hash: str
    duration: float | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    file_size: int | None = None
    file_format: str | None = None


class TrackUpdate(BaseModel):
    """Schema for updating a track."""

    title: str | None = None
    artist: str | None = None
    album: str | None = None
    album_artist: str | None = None
    genre: str | None = None
    year: int | None = None
    track_number: int | None = None
    disc_number: int | None = None
    comment: str | None = None
    rating: int | None = Field(None, ge=1, le=5)


class TrackResponse(TrackBase):
    """Schema for track response."""

    id: int
    file_path: str
    duration: float | None = None
    bitrate: int | None = None
    file_format: str | None = None
    play_count: int = 0
    skip_count: int = 0
    rating: int | None = None
    last_played_at: datetime | None = None
    is_available: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        
        from_attributes = True


class TrackPlaybackUpdate(BaseModel):
    """Schema for updating track playback statistics."""

    increment_play_count: bool = False
    increment_skip_count: bool = False
    last_played_at: datetime | None = None