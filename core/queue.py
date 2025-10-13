import random
from core.db import MusicDatabase
from core.logging import log_queue_operation, queue_logger
from pathlib import Path
from utils.files import normalize_path


class QueueManager:
    def __init__(self, db: MusicDatabase):
        self.db = db
        self.shuffle_enabled = self.db.get_shuffle_enabled()
        self._original_order = []
        self._shuffled_order = []
        self._shuffle_generated = False
        self._current_shuffle_pos = 0  # Track position in shuffle sequence

    def add_to_queue(self, filepath: str) -> None:
        """Add a file to the queue."""
        try:
            from core.logging import log_queue_operation

            log_queue_operation("add", filepath=filepath)
        except ImportError:
            pass

        self.db.add_to_queue(filepath)

        try:
            from core.logging import queue_logger
            from eliot import log_message

            log_message(message_type="queue_add_success", filepath=filepath, message="File added to queue successfully")
        except ImportError:
            pass

    def remove_from_queue(self, title: str, artist: str = None, album: str = None, track_num: str = None) -> None:
        """Remove a song from the queue based on its metadata."""
        self.db.remove_from_queue(title, artist, album, track_num)

    def clear_queue(self) -> None:
        """Clear all items from the queue."""
        self.db.clear_queue()

    def get_queue_items(self) -> list[tuple]:
        """Get all items in the queue with their metadata."""
        return self.db.get_queue_items()

    def find_file_in_queue(self, title: str, artist: str = None) -> str | None:
        """Find a file in the queue based on its metadata."""
        return self.db.find_file_in_queue(title, artist)

    def search_queue(self, search_text):
        """Search queue items by text across artist, title, and album."""
        return self.db.search_queue(search_text)

    def process_dropped_files(self, paths: list[str | Path]) -> None:
        """Process dropped files and add them to the queue."""
        for path in paths:
            if path is None:
                continue

            try:
                normalized_path = normalize_path(path)
                if Path(normalized_path).exists():
                    self.db.add_to_queue(str(normalized_path))
            except (OSError, PermissionError) as e:
                print(f"Error accessing path {path}: {e}")
                continue

    def toggle_shuffle(self) -> bool:
        """Toggle shuffle mode on/off and return new state."""
        self.shuffle_enabled = not self.shuffle_enabled
        self.db.set_shuffle_enabled(self.shuffle_enabled)

        # Invalidate shuffled order so it gets regenerated
        self._shuffle_generated = False
        self._current_shuffle_pos = 0

        return self.shuffle_enabled

    def is_shuffle_enabled(self) -> bool:
        """Return current shuffle state."""
        return self.shuffle_enabled

    def get_shuffled_queue_items(self) -> list[tuple]:
        """Get queue items in shuffled or original order based on shuffle state."""
        items = self.get_queue_items()

        if not self.shuffle_enabled:
            return items

        # Generate shuffled order if needed
        if not self._shuffle_generated or len(self._original_order) != len(items):
            self._original_order = list(range(len(items)))
            self._shuffled_order = self._original_order.copy()
            random.shuffle(self._shuffled_order)
            self._shuffle_generated = True

        # Return items in shuffled order
        return [items[i] for i in self._shuffled_order]

    def get_next_track_index(self, current_index: int, total_items: int) -> int | None:
        """Get the index of the next track considering shuffle state."""
        if total_items <= 0:
            return None

        if self.shuffle_enabled:
            # Ensure shuffle order is generated
            if not self._shuffle_generated or len(self._shuffled_order) != total_items:
                self._original_order = list(range(total_items))
                self._shuffled_order = self._original_order.copy()
                random.shuffle(self._shuffled_order)
                self._shuffle_generated = True
                self._current_shuffle_pos = 0
                print(
                    f"Generated new shuffle order: {self._shuffled_order[:10]}... (total: {len(self._shuffled_order)})"
                )  # Debug

            # In shuffle mode, we need to find where we are in the sequence
            try:
                # Try to find current position in shuffle sequence
                current_pos = self._shuffled_order.index(current_index)
                self._current_shuffle_pos = current_pos
            except (ValueError, IndexError):
                # If current index not found, use current position or random start
                pass

            # Move to next position in shuffle sequence
            self._current_shuffle_pos = (self._current_shuffle_pos + 1) % len(self._shuffled_order)
            next_track = self._shuffled_order[self._current_shuffle_pos]
            print(
                f"Shuffle: current_index={current_index}, shuffle_pos={self._current_shuffle_pos}, next_track={next_track}"
            )  # Debug
            return next_track
        else:
            # In normal mode, just go to next track
            return (current_index + 1) % total_items

    def get_previous_track_index(self, current_index: int, total_items: int) -> int | None:
        """Get the index of the previous track considering shuffle state."""
        if total_items <= 0:
            return None

        if self.shuffle_enabled:
            # Ensure shuffle order is generated
            if not self._shuffle_generated or len(self._shuffled_order) != total_items:
                self._original_order = list(range(total_items))
                self._shuffled_order = self._original_order.copy()
                random.shuffle(self._shuffled_order)
                self._shuffle_generated = True
                self._current_shuffle_pos = 0

            # In shuffle mode, we need to find where we are in the sequence
            try:
                # Try to find current position in shuffle sequence
                current_pos = self._shuffled_order.index(current_index)
                self._current_shuffle_pos = current_pos
            except (ValueError, IndexError):
                # If current index not found, use current position
                pass

            # Move to previous position in shuffle sequence
            self._current_shuffle_pos = (self._current_shuffle_pos - 1) % len(self._shuffled_order)
            prev_track = self._shuffled_order[self._current_shuffle_pos]
            print(
                f"Shuffle previous: current_index={current_index}, shuffle_pos={self._current_shuffle_pos}, prev_track={prev_track}"
            )  # Debug
            return prev_track
        else:
            # In normal mode, just go to previous track
            return (current_index - 1) % total_items
