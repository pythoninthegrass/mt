"""Queue model for playback queue management."""

from app.core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class QueueEntry(Base):
    """Queue entry model for playback queue."""

    __tablename__ = "queue_entries"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    position = Column(Integer, nullable=False, index=True)
    queue_name = Column(String, default="default", index=True)  # Support multiple queues
    
    # Timestamps
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    track = relationship("Track", back_populates="queue_entries")
    
    def to_dict(self) -> dict:
        """Convert queue entry to dictionary."""
        return {
            "id": self.id,
            "position": self.position,
            "queue_name": self.queue_name,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "track": self.track.to_dict() if self.track else None,
        }


class PlaybackState(Base):
    """Playback state model for persisting player state."""

    __tablename__ = "playback_state"

    id = Column(Integer, primary_key=True)
    queue_name = Column(String, unique=True, nullable=False, index=True)
    current_track_id = Column(Integer, ForeignKey("tracks.id"))
    current_position = Column(Integer, default=0)  # Position in queue
    seek_position = Column(Integer, default=0)  # Seek position in seconds
    volume = Column(Integer, default=70)
    is_playing = Column(Integer, default=0)  # SQLite doesn't have native Boolean
    repeat_mode = Column(String, default="none")  # none, one, all
    shuffle = Column(Integer, default=0)
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    current_track = relationship("Track", foreign_keys=[current_track_id])
    
    def to_dict(self) -> dict:
        """Convert playback state to dictionary."""
        return {
            "queue_name": self.queue_name,
            "current_track_id": self.current_track_id,
            "current_position": self.current_position,
            "seek_position": self.seek_position,
            "volume": self.volume,
            "is_playing": bool(self.is_playing),
            "repeat_mode": self.repeat_mode,
            "shuffle": bool(self.shuffle),
            "current_track": self.current_track.to_dict() if self.current_track else None,
        }