"""Queue models for playback queue management."""

from backend.models.track import Track
from pydantic import BaseModel, Field


class QueueItem(BaseModel):
    """A track in the playback queue with position."""

    position: int = Field(ge=0, description="0-indexed position in queue")
    track: Track


class QueueAddRequest(BaseModel):
    """Request to add tracks to the queue."""

    track_ids: list[int] = Field(min_length=1, description="Track IDs to add")
    position: int | None = Field(None, ge=0, description="Insert position (null = end)")


class QueueAddFilesRequest(BaseModel):
    """Request to add files directly to the queue (for drag-and-drop)."""

    filepaths: list[str] = Field(min_length=1, description="File paths to add")
    position: int | None = Field(None, ge=0, description="Insert position (null = end)")


class QueueReorderRequest(BaseModel):
    """Request to reorder tracks in the queue."""

    from_position: int = Field(ge=0, description="Current position of track")
    to_position: int = Field(ge=0, description="New position for track")


class QueueShuffleRequest(BaseModel):
    """Request to shuffle the queue."""

    keep_current: bool = Field(True, description="Keep current track at position 0")
