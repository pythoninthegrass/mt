#!/usr/bin/env python

import os
from core.db import MusicDatabase
from pathlib import Path
from utils.files import normalize_path


class QueueManager:
    """
    Manages the playback queue of media files.

    This class provides methods for adding, removing, and retrieving
    items in the playback queue, as well as processing dropped files.
    """

    def __init__(self, db: MusicDatabase):
        """
        Initialize the queue manager.

        Args:
            db: Database instance for queue operations
        """
        self.db = db

    def add_to_queue(self, filepath: str) -> None:
        """
        Add a file to the playback queue.

        Args:
            filepath: Path to the media file to add
        """
        self.db.add_to_queue(filepath)

    def remove_from_queue(self, title: str, artist: str = None, album: str = None, track_num: str = None) -> None:
        """
        Remove a song from the queue based on its metadata.

        Args:
            title: Title of the track to remove
            artist: Artist of the track to remove (optional)
            album: Album of the track to remove (optional)
            track_num: Track number of the track to remove (optional)
        """
        self.db.remove_from_queue(title, artist, album, track_num)

    def get_queue_items(self) -> list[tuple]:
        """
        Get all items in the queue with their metadata.

        Returns:
            list[tuple]: List of queue items with metadata
        """
        return self.db.get_queue_items()

    def find_file_in_queue(self, title: str, artist: str = None) -> str | None:
        """
        Find a file in the queue based on its metadata.

        Args:
            title: Title of the track to find
            artist: Artist of the track to find (optional)

        Returns:
            str | None: Path to the file if found, None otherwise
        """
        return self.db.find_file_in_queue(title, artist)

    def process_dropped_files(self, paths: list[str | Path]) -> None:
        """
        Process dropped files and add them to the queue.

        Args:
            paths: List of file paths to process
        """
        for path in paths:
            if path is None:
                continue

            try:
                normalized_path = str(normalize_path(path))
                if os.path.exists(normalized_path):
                    self.db.add_to_queue(normalized_path)
            except (OSError, PermissionError) as e:
                print(f"Error accessing path {path}: {e}")
                continue
