"""Playlist models."""

from app.core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class Playlist(Base):
    """Playlist model."""

    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entries = relationship("PlaylistEntry", back_populates="playlist", cascade="all, delete-orphan", order_by="PlaylistEntry.position")
    
    def to_dict(self) -> dict:
        """Convert playlist to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "track_count": len(self.entries) if self.entries else 0,
        }


class PlaylistEntry(Base):
    """Playlist entry model."""

    __tablename__ = "playlist_entries"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    position = Column(Integer, nullable=False)
    
    # Timestamps
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    playlist = relationship("Playlist", back_populates="entries")
    track = relationship("Track", back_populates="playlist_entries")
    
    def to_dict(self) -> dict:
        """Convert playlist entry to dictionary."""
        return {
            "id": self.id,
            "position": self.position,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "track": self.track.to_dict() if self.track else None,
        }