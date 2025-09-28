"""Queue schemas for API validation."""

from app.schemas.track import TrackResponse
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class QueueEntryBase(BaseModel):
    """Base queue entry schema."""

    track_id: int
    position: int
    queue_name: str = "default"


class QueueEntryCreate(BaseModel):
    """Schema for adding tracks to queue."""

    track_ids: list[int]
    queue_name: str = "default"
    insert_position: int | None = None  # None means append to end


class QueueEntryUpdate(BaseModel):
    """Schema for updating queue entry."""

    position: int | None = None


class QueueEntryResponse(BaseModel):
    """Schema for queue entry response."""

    id: int
    position: int
    queue_name: str
    added_at: datetime
    track: TrackResponse | None = None

    class Config:
        """Pydantic config."""
        
        from_attributes = True


class QueueResponse(BaseModel):
    """Schema for complete queue response."""

    queue_name: str
    entries: list[QueueEntryResponse]
    total: int


class PlaybackStateBase(BaseModel):
    """Base playback state schema."""

    current_track_id: int | None = None
    current_position: int = 0
    seek_position: int = 0
    volume: int = 70
    is_playing: bool = False
    repeat_mode: str = "none"  # none, one, all
    shuffle: bool = False


class PlaybackStateUpdate(BaseModel):
    """Schema for updating playback state."""

    current_track_id: int | None = None
    current_position: int | None = None
    seek_position: int | None = None
    volume: int | None = None
    is_playing: bool | None = None
    repeat_mode: str | None = None
    shuffle: bool | None = None


class PlaybackStateResponse(PlaybackStateBase):
    """Schema for playback state response."""

    queue_name: str
    current_track: TrackResponse | None = None
    updated_at: datetime

    class Config:
        """Pydantic config."""
        
        from_attributes = True