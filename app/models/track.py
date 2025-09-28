"""Track model for music files."""

from app.core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import relationship
from typing import Optional


class Track(Base):
    """Track model representing a music file."""

    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, unique=True, nullable=False, index=True)
    file_hash = Column(String, unique=True, nullable=False, index=True)
    
    # Metadata
    title = Column(String, nullable=False)
    artist = Column(String, index=True)
    album = Column(String, index=True)
    album_artist = Column(String)
    genre = Column(String, index=True)
    year = Column(Integer)
    track_number = Column(Integer)
    disc_number = Column(Integer)
    comment = Column(Text)
    
    # Audio properties
    duration = Column(Float)  # in seconds
    bitrate = Column(Integer)
    sample_rate = Column(Integer)
    channels = Column(Integer)
    
    # File properties
    file_size = Column(Integer)
    file_format = Column(String)
    
    # Playback statistics
    play_count = Column(Integer, default=0)
    skip_count = Column(Integer, default=0)
    last_played_at = Column(DateTime)
    rating = Column(Integer)  # 1-5 stars
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scanned_at = Column(DateTime, default=datetime.utcnow)
    
    # Status
    is_available = Column(Boolean, default=True)
    scan_error = Column(Text)
    
    # Relationships
    queue_entries = relationship("QueueEntry", back_populates="track", cascade="all, delete-orphan")
    playlist_entries = relationship("PlaylistEntry", back_populates="track", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Convert track to dictionary."""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "album_artist": self.album_artist,
            "genre": self.genre,
            "year": self.year,
            "track_number": self.track_number,
            "disc_number": self.disc_number,
            "duration": self.duration,
            "bitrate": self.bitrate,
            "file_format": self.file_format,
            "play_count": self.play_count,
            "rating": self.rating,
            "last_played_at": self.last_played_at.isoformat() if self.last_played_at else None,
            "is_available": self.is_available,
        }