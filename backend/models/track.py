"""Track models for the music library."""

from datetime import datetime
from pydantic import BaseModel, Field


class TrackBase(BaseModel):
    """Base track model with common fields."""

    filepath: str
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    album_artist: str | None = None
    track_number: str | None = None
    track_total: str | None = None
    date: str | None = None
    duration: float | None = None
    file_size: int = 0


class Track(TrackBase):
    """Full track model with database fields."""

    id: int
    play_count: int = 0
    last_played: datetime | None = None
    added_date: datetime

    class Config:
        from_attributes = True


class TrackCreate(TrackBase):
    """Model for creating a new track."""

    pass


class TrackUpdate(BaseModel):
    """Model for updating track metadata."""

    title: str | None = None
    artist: str | None = None
    album: str | None = None
    album_artist: str | None = None
    track_number: str | None = None
    date: str | None = None


class TrackWithFavorite(Track):
    """Track with favorited date for favorites list."""

    favorited_date: datetime | None = None


class TrackWithPlayCount(Track):
    """Track with play count for top 25 list."""

    pass  # play_count is already in Track
