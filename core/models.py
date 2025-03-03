#!/usr/bin/env python

import mutagen
import os
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from utils.common import get_db_instance
from utils.files import find_audio_files


@dataclass
class Track:
    """
    Data model representing a music track with its metadata.

    This class stores all relevant information about a music track including
    its file path, metadata, and playback information.
    """
    id: str
    title: str
    artist: str
    album: str
    path: str
    duration: int = 0
    year: str = ""
    genre: str = ""
    track_number: int = 0

    @property
    def duration_str(self) -> str:
        """
        Format the duration in minutes and seconds.

        Returns:
            str: Formatted duration string in the format "minutes:seconds"
        """
        minutes, seconds = divmod(self.duration, 60)
        return f"{minutes}:{seconds:02d}"


class MusicLibrary:
    """
    Container class for managing a collection of music tracks and playlists.

    This class provides methods for adding, retrieving, and organizing tracks
    into playlists, as well as scanning directories for music files.
    """
    def __init__(self):
        self.tracks: list[Track] = []
        self.playlists: dict[str, list[Track]] = {
            "Recently Added": [],
            "Recently Played": [],
            "Top 25 Most Played": [],
        }

    def add_track(self, track: Track):
        """
        Add a track to the library.

        Args:
            track: The Track object to add to the library
        """
        self.tracks.append(track)

    def get_tracks(self) -> list[Track]:
        """
        Get all tracks in the library.

        Returns:
            list[Track]: All tracks in the library
        """
        return self.tracks

    def scan_directory(self, directory: str):
        """
        Scan a directory for music files and add them to the library.

        This method scans the specified directory for audio files and
        adds them to the library with metadata.

        Args:
            directory: Path to the directory to scan
        """
        try:
            # Expand the path if it contains a tilde
            expanded_dir = os.path.expanduser(directory)
            expanded_dir = os.path.abspath(expanded_dir)  # Ensure absolute path
            print(f"Scanning directory: {expanded_dir}")

            # Find audio files with max depth of 1 (don't traverse subdirectories)
            audio_files = find_audio_files(expanded_dir, max_depth=1)
            print(f"Found {len(audio_files)} audio files")

            # Process each file
            for file_path in audio_files:
                try:
                    # Make sure we use absolute paths consistently
                    abs_file_path = os.path.abspath(file_path)

                    # Extract metadata using mutagen
                    audio = mutagen.File(abs_file_path)
                    if audio is None:
                        continue

                    # Create track ID based on file path
                    track_id = str(len(self.tracks) + 1)

                    # Extract basic metadata
                    title = Path(abs_file_path).stem  # Default to filename
                    artist = ""
                    album = ""
                    year = ""
                    genre = ""
                    track_number = 0
                    duration = int(audio.info.length) if hasattr(audio, 'info') else 0

                    # Extract metadata based on file type
                    if hasattr(audio, 'tags'):
                        tags = audio.tags
                        if tags:
                            # Handle ID3 tags (MP3)
                            if isinstance(tags, mutagen.id3.ID3):
                                if 'TIT2' in tags and tags['TIT2'].text:
                                    title = str(tags['TIT2'].text[0])
                                if 'TPE1' in tags and tags['TPE1'].text:
                                    artist = str(tags['TPE1'].text[0])
                                if 'TALB' in tags and tags['TALB'].text:
                                    album = str(tags['TALB'].text[0])
                                if 'TDRC' in tags and tags['TDRC'].text:
                                    year = str(tags['TDRC'].text[0])
                                if 'TCON' in tags and tags['TCON'].text:
                                    genre = str(tags['TCON'].text[0])
                                if 'TRCK' in tags and tags['TRCK'].text:
                                    track_number_str = str(tags['TRCK'].text[0])
                                    # Handle "track/total" format
                                    if '/' in track_number_str:
                                        track_number_str = track_number_str.split('/')[0]
                                    try:
                                        track_number = int(track_number_str)
                                    except ValueError:
                                        track_number = 0
                            # Handle other tag formats (FLAC, OGG, etc.)
                            else:
                                if 'title' in tags:
                                    title = str(tags['title'][0])
                                if 'artist' in tags:
                                    artist = str(tags['artist'][0])
                                if 'album' in tags:
                                    album = str(tags['album'][0])
                                if 'date' in tags:
                                    year = str(tags['date'][0])
                                if 'genre' in tags:
                                    genre = str(tags['genre'][0])
                                if 'tracknumber' in tags:
                                    track_number_str = str(tags['tracknumber'][0])
                                    # Handle "track/total" format
                                    if '/' in track_number_str:
                                        track_number_str = track_number_str.split('/')[0]
                                    try:
                                        track_number = int(track_number_str)
                                    except ValueError:
                                        track_number = 0

                    # Create Track object
                    track = Track(
                        id=track_id,
                        title=title,
                        artist=artist,
                        album=album,
                        path=abs_file_path,
                        duration=duration,
                        year=year,
                        genre=genre,
                        track_number=track_number
                    )

                    # Add track to library
                    self.add_track(track)

                    # Add track to database for proper lookup
                    self._add_track_to_database(track)

                except Exception as e:
                    print(f"Error processing file {abs_file_path}: {e}")
                    traceback.print_exc()

            print(f"Added {len(self.tracks)} tracks to the library")
        except Exception as e:
            print(f"Error scanning directory: {e}")
            traceback.print_exc()

    def _add_track_to_database(self, track: Track):
        """
        Helper method to add track to database.

        Args:
            track: The Track object to add to the database
        """
        try:
            db = get_db_instance()
            if db:
                # Add to library table with metadata
                metadata = {
                    'title': track.title,
                    'artist': track.artist,
                    'album': track.album,
                    'track_number': str(track.track_number),
                    'date': track.year,
                    'duration': track.duration,
                }

                # Only add if filepath doesn't exist already
                existing = db.get_existing_files()
                if track.path not in existing:
                    db.add_to_library(track.path, metadata)
                    # Also add to queue for now playing
                    db.add_to_queue(track.path)
                    print(f"Added track to database and queue: {track.title}")
                else:
                    # Even if the track exists in the library, ensure it's in the queue
                    # This helps with navigation between tracks
                    queue_items = db.get_queue_items()
                    queue_paths = [os.path.abspath(item[0]) for item in queue_items]
                    if os.path.abspath(track.path) not in queue_paths:
                        db.add_to_queue(track.path)
                        print(f"Added existing track to queue: {track.title}")
        except Exception as e:
            print(f"Error adding track to database: {e}")
            traceback.print_exc()
