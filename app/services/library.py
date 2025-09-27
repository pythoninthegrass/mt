"""Library service for music file scanning and management."""

import hashlib
import os
from app.core.config import settings
from app.models.track import Track
from app.websocket.manager import EventTypes, broadcast_library_event
from mutagen import File as MutagenFile
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional


class LibraryService:
    """Service for managing music library."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def scan_directory(self, path: str | None = None):
        """Scan a directory for music files."""
        scan_path = Path(path) if path else settings.MUSIC_LIBRARY_PATH
        
        if not scan_path.exists():
            await broadcast_library_event(EventTypes.ERROR, {
                "message": f"Path does not exist: {scan_path}"
            })
            return
        
        await broadcast_library_event(EventTypes.LIBRARY_SCAN_STARTED, {
            "path": str(scan_path)
        })
        
        music_extensions = {'.mp3', '.flac', '.ogg', '.m4a', '.mp4', '.wav', '.wma'}
        total_files = 0
        processed_files = 0
        new_tracks = 0
        
        # Collect all music files
        music_files = []
        for root, dirs, files in os.walk(scan_path):
            for file in files:
                if Path(file).suffix.lower() in music_extensions:
                    music_files.append(Path(root) / file)
        
        total_files = len(music_files)
        
        # Process files in chunks
        chunk_size = settings.SCAN_CHUNK_SIZE
        for i in range(0, total_files, chunk_size):
            chunk = music_files[i:i + chunk_size]
            
            for file_path in chunk:
                try:
                    track = await self.process_music_file(file_path)
                    if track:
                        new_tracks += 1
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                
                processed_files += 1
                
                # Send progress update
                if processed_files % 10 == 0:
                    await broadcast_library_event(EventTypes.LIBRARY_SCAN_PROGRESS, {
                        "processed": processed_files,
                        "total": total_files,
                        "progress": int((processed_files / total_files) * 100)
                    })
            
            await self.db.commit()
        
        await broadcast_library_event(EventTypes.LIBRARY_SCAN_COMPLETED, {
            "total_files": total_files,
            "processed_files": processed_files,
            "new_tracks": new_tracks
        })

    async def process_music_file(self, file_path: Path) -> Track | None:
        """Process a single music file and add to database."""
        # Calculate file hash
        file_hash = self.calculate_file_hash(file_path)
        
        # Check if track already exists
        query = select(Track).where(Track.file_hash == file_hash)
        result = await self.db.execute(query)
        existing_track = result.scalar_one_or_none()
        
        if existing_track:
            # Update file path if changed
            if existing_track.file_path != str(file_path):
                existing_track.file_path = str(file_path)
                existing_track.is_available = True
            return None
        
        # Extract metadata
        metadata = self.extract_metadata(file_path)
        if not metadata:
            return None
        
        # Create new track
        track = Track(
            file_path=str(file_path),
            file_hash=file_hash,
            title=metadata.get('title', file_path.stem),
            artist=metadata.get('artist'),
            album=metadata.get('album'),
            album_artist=metadata.get('albumartist'),
            genre=metadata.get('genre'),
            year=self.parse_year(metadata.get('date')),
            track_number=self.parse_int(metadata.get('tracknumber')),
            disc_number=self.parse_int(metadata.get('discnumber')),
            duration=metadata.get('length'),
            bitrate=metadata.get('bitrate'),
            sample_rate=metadata.get('sample_rate'),
            channels=metadata.get('channels'),
            file_size=file_path.stat().st_size,
            file_format=file_path.suffix[1:].upper(),
        )
        
        self.db.add(track)
        return track

    @staticmethod
    def calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    @staticmethod
    def extract_metadata(file_path: Path) -> dict:
        """Extract metadata from a music file using mutagen."""
        try:
            audio = MutagenFile(str(file_path))
            if audio is None:
                return {}
            
            metadata = {}
            
            # Get basic info
            if hasattr(audio.info, 'length'):
                metadata['length'] = audio.info.length
            if hasattr(audio.info, 'bitrate'):
                metadata['bitrate'] = audio.info.bitrate
            if hasattr(audio.info, 'sample_rate'):
                metadata['sample_rate'] = audio.info.sample_rate
            if hasattr(audio.info, 'channels'):
                metadata['channels'] = audio.info.channels
            
            # Get tags
            if audio.tags:
                tag_mapping = {
                    'title': ['TIT2', 'TITLE', '\xa9nam'],
                    'artist': ['TPE1', 'ARTIST', '\xa9ART'],
                    'album': ['TALB', 'ALBUM', '\xa9alb'],
                    'albumartist': ['TPE2', 'ALBUMARTIST', 'aART'],
                    'date': ['TDRC', 'DATE', '\xa9day'],
                    'genre': ['TCON', 'GENRE', '\xa9gen'],
                    'tracknumber': ['TRCK', 'TRACKNUMBER', 'trkn'],
                    'discnumber': ['TPOS', 'DISCNUMBER', 'disk'],
                }
                
                for key, tags in tag_mapping.items():
                    for tag in tags:
                        if tag in audio.tags:
                            value = audio.tags[tag]
                            if isinstance(value, list) and value:
                                metadata[key] = str(value[0])
                            else:
                                metadata[key] = str(value)
                            break
            
            return metadata
        except Exception as e:
            print(f"Error extracting metadata from {file_path}: {e}")
            return {}

    @staticmethod
    def parse_year(date_str: str | None) -> int | None:
        """Parse year from date string."""
        if not date_str:
            return None
        try:
            # Handle formats like "2021", "2021-01-01", etc.
            year_str = date_str.split('-')[0]
            return int(year_str)
        except:
            return None

    @staticmethod
    def parse_int(value: str | None) -> int | None:
        """Parse integer from string, handling track/disc number formats."""
        if not value:
            return None
        try:
            # Handle formats like "1/10"
            if '/' in str(value):
                return int(str(value).split('/')[0])
            return int(value)
        except:
            return None