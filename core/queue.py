import os
from core.db import MusicDatabase
from pathlib import Path
from utils.files import normalize_path


class QueueManager:
    def __init__(self, db: MusicDatabase):
        self.db = db

    def add_to_queue(self, filepath: str) -> None:
        """Add a file to the queue."""
        self.db.add_to_queue(filepath)

    def remove_from_queue(self, title: str, artist: str = None, album: str = None, track_num: str = None) -> None:
        """Remove a song from the queue based on its metadata."""
        self.db.remove_from_queue(title, artist, album, track_num)

    def get_queue_items(self) -> list[tuple]:
        """Get all items in the queue with their metadata."""
        return self.db.get_queue_items()

    def find_file_in_queue(self, title: str, artist: str = None) -> str | None:
        """Find a file in the queue based on its metadata."""
        return self.db.find_file_in_queue(title, artist)

    def process_dropped_files(self, paths: list[str | Path]) -> None:
        """Process dropped files and add them to the queue."""
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
