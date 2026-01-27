import contextlib
import random
import threading
from core.db import MusicDatabase
from core.logging import log_queue_operation, queue_logger
from pathlib import Path
from utils.files import normalize_path


class QueueManager:
    """Manages the playback queue in-memory (session-only, not persisted)."""

    def __init__(self, db: MusicDatabase):
        self.db = db
        self.queue_items = []  # In-memory list of filepaths
        self.current_index = 0  # Current playback position
        self.shuffle_enabled = False
        self._original_order = []
        self._shuffled_order = []
        self._shuffle_generated = False
        self._current_shuffle_pos = 0
        self._lock = threading.RLock()  # Reentrant lock for thread-safe operations

    def populate_and_play(self, filepaths: list[str], start_index: int = 0) -> str | None:
        """Replace queue with new tracks and set current position.

        Args:
            filepaths: List of file paths to add to queue
            start_index: Index to start playback from (in original order)

        Returns:
            Filepath of track to play, or None if empty
        """
        try:
            from core.logging import log_queue_operation

            log_queue_operation("populate_and_play", count=len(filepaths), start_index=start_index, shuffle_enabled=self.shuffle_enabled)
        except ImportError:
            pass

        if not filepaths:
            return None

        # Store the track we want to play (before any shuffling)
        start_index = start_index if 0 <= start_index < len(filepaths) else 0
        track_to_play = filepaths[start_index]

        self.queue_items = filepaths.copy()

        # If shuffle is enabled, apply shuffle immediately
        if self.shuffle_enabled:
            # Generate new shuffle order
            self._original_order = list(range(len(self.queue_items)))
            self._shuffled_order = self._original_order.copy()
            random.shuffle(self._shuffled_order)
            self._shuffle_generated = True

            # Shuffle the queue items in place
            shuffled_items = [self.queue_items[i] for i in self._shuffled_order]
            self.queue_items = shuffled_items

            # Find where the track we want to play ended up after shuffle
            with contextlib.suppress(ValueError):
                self.current_index = self.queue_items.index(track_to_play)
                self._current_shuffle_pos = self.current_index
        else:
            # No shuffle - just use the provided index
            self.current_index = start_index
            self._shuffle_generated = False

        return self.queue_items[self.current_index] if self.queue_items else None

    def insert_after_current(self, filepaths: list[str]) -> None:
        """Insert tracks after currently playing track.

        Args:
            filepaths: List of file paths to insert
        """
        if not filepaths:
            return

        try:
            from core.logging import log_queue_operation

            log_queue_operation("insert_after_current", count=len(filepaths), current_index=self.current_index)
        except ImportError:
            pass

        insert_pos = self.current_index + 1
        for i, filepath in enumerate(filepaths):
            self.queue_items.insert(insert_pos + i, filepath)

        # Invalidate shuffle when queue is modified
        self._shuffle_generated = False


    def prepend_track(self, filepath: str) -> None:
        """Prepend a track to the beginning of the queue (next to play).

        Used for repeat-one mode to make current track play again next.

        Args:
            filepath: File path to prepend
        """
        if not filepath:
            return

        try:
            from core.logging import log_queue_operation

            log_queue_operation("prepend_track", filepath=filepath, queue_size=len(self.queue_items))
        except ImportError:
            pass

        # Insert at the beginning (index 0)
        self.queue_items.insert(0, filepath)

        # Adjust current_index since we inserted before it
        if self.current_index >= 0:
            self.current_index += 1

        # Invalidate shuffle when queue is modified
        self._shuffle_generated = False

    def add_to_queue_end(self, filepaths: list[str]) -> None:
        """Append tracks to end of queue.

        Args:
            filepaths: List of file paths to append
        """
        if not filepaths:
            return

        try:
            from core.logging import log_queue_operation

            log_queue_operation("add_to_queue_end", count=len(filepaths))
        except ImportError:
            pass

        self.queue_items.extend(filepaths)

        # Invalidate shuffle when queue is modified
        self._shuffle_generated = False

    def add_to_queue(self, filepath: str) -> None:
        """Add a single file to the end of queue (legacy compatibility).

        Args:
            filepath: File path to add
        """
        self.add_to_queue_end([filepath])

    def reorder_queue(self, from_index: int, to_index: int) -> None:
        """Move track from one position to another.

        Args:
            from_index: Current position of track
            to_index: Target position for track
        """
        if not (0 <= from_index < len(self.queue_items)) or not (0 <= to_index < len(self.queue_items)):
            return

        if from_index == to_index:
            return

        try:
            from core.logging import log_queue_operation

            log_queue_operation("reorder", from_index=from_index, to_index=to_index, current_index=self.current_index)
        except ImportError:
            pass

        # Remove item from original position
        item = self.queue_items.pop(from_index)
        # Insert at new position
        self.queue_items.insert(to_index, item)

        # Adjust current_index if affected
        if from_index == self.current_index:
            # Currently playing track was moved
            self.current_index = to_index
        elif from_index < self.current_index <= to_index:
            # Track moved from before to after current
            self.current_index -= 1
        elif to_index <= self.current_index < from_index:
            # Track moved from after to before current
            self.current_index += 1

        # Invalidate shuffle when queue is reordered
        self._shuffle_generated = False

    def move_current_to_end(self) -> None:
        """Move the currently playing track to the end of the queue (carousel mode).

        Used in loop mode to create a carousel effect where played tracks
        move to the end, keeping upcoming tracks near the top.
        """
        with self._lock:
            if not self.queue_items or len(self.queue_items) <= 1:
                return

            if self.current_index >= len(self.queue_items):
                return

            try:
                from core.logging import log_queue_operation

                log_queue_operation("carousel_move", from_index=self.current_index, to_index=len(self.queue_items) - 1)
            except ImportError:
                pass

            # Remove current track and append to end
            track = self.queue_items.pop(self.current_index)
            self.queue_items.append(track)

            # Stay at index 0 for carousel mode - always play from the top
            self.current_index = 0

            # Invalidate shuffle when queue order changes
            self._shuffle_generated = False

    def move_current_to_end_and_get_next(self) -> str | None:
        """Atomically move current track to end and return next filepath.

        This is a thread-safe version of move_current_to_end() that also returns
        the next track to play, preventing race conditions.

        Returns:
            Filepath of next track to play, or None if queue is empty
        """
        with self._lock:
            if not self.queue_items or len(self.queue_items) <= 1:
                return self.queue_items[0] if self.queue_items else None

            if self.current_index >= len(self.queue_items):
                return None

            try:
                from core.logging import log_queue_operation

                log_queue_operation("carousel_move", from_index=self.current_index, to_index=len(self.queue_items) - 1)
            except ImportError:
                pass

            # Remove current track and append to end
            track = self.queue_items.pop(self.current_index)
            self.queue_items.append(track)

            # Stay at index 0 for carousel mode - always play from the top
            self.current_index = 0

            # Invalidate shuffle when queue order changes
            self._shuffle_generated = False

            # Return the track now at current_index (guaranteed to be within bounds)
            return self.queue_items[self.current_index] if self.queue_items else None


    def move_current_to_beginning(self) -> None:
        """Move the currently playing track to the beginning of the queue.

        Used for repeat-one mode to queue current track for immediate replay.
        The track is moved (not copied), avoiding duplicates.
        """
        with self._lock:
            if not self.queue_items or len(self.queue_items) <= 1:
                return

            if self.current_index < 0 or self.current_index >= len(self.queue_items):
                return

            # If already at index 0, nothing to do
            if self.current_index == 0:
                return

            try:
                from core.logging import log_queue_operation

                log_queue_operation("move_to_beginning", from_index=self.current_index, to_index=0)
            except ImportError:
                pass

            # Remove current track and insert at beginning
            track = self.queue_items.pop(self.current_index)
            self.queue_items.insert(0, track)

            # Current index stays the same because we removed one item before it
            # Actually, current track moved from current_index to 0
            # So the track that was at current_index is now gone
            # The track that was at current_index-1 is now at current_index-1
            # The track that was at current_index+1 is now at current_index
            # So current_index doesn't need to change - it now points to what was next

            # Invalidate shuffle when queue order changes
            self._shuffle_generated = False

    def move_last_to_beginning(self) -> None:
        """Move the last track to the beginning of the queue (reverse carousel mode).

        Used in loop mode when going backwards to create a carousel effect
        where the previous track comes back to the top.
        """
        if not self.queue_items or len(self.queue_items) <= 1:
            return

        try:
            from core.logging import log_queue_operation

            log_queue_operation("carousel_move_reverse", from_index=len(self.queue_items) - 1, to_index=0)
        except ImportError:
            pass

        # Remove last track and insert at beginning
        track = self.queue_items.pop()
        self.queue_items.insert(0, track)

        # Current track is now at index 0
        self.current_index = 0

        # Invalidate shuffle when queue order changes
        self._shuffle_generated = False

    def remove_from_queue_at_index(self, index: int) -> None:
        """Remove track at specific index.

        Args:
            index: Index of track to remove
        """
        if not (0 <= index < len(self.queue_items)):
            return

        try:
            from core.logging import log_queue_operation

            filepath = self.queue_items[index]
            log_queue_operation("remove", index=index, filepath=filepath)
        except ImportError:
            pass

        self.queue_items.pop(index)

        # Adjust current_index if needed
        if index < self.current_index:
            self.current_index -= 1
        elif index == self.current_index:
            # Removed currently playing track
            if len(self.queue_items) == 0:
                # Queue is now empty - reset to 0
                self.current_index = 0
            elif self.current_index >= len(self.queue_items):
                # Removed last track but queue not empty - point to now-last track
                self.current_index = len(self.queue_items) - 1

        # Invalidate shuffle when queue is modified
        self._shuffle_generated = False

    def remove_from_queue(self, title: str, artist: str = None, album: str = None, track_num: str = None) -> None:
        """Remove a song from the queue based on its metadata (legacy compatibility)."""
        # Find matching track in queue and remove it
        for i, filepath in enumerate(self.queue_items):
            metadata = self.db.get_track_by_filepath(filepath)
            if metadata and metadata[1] == title:  # metadata[1] is title
                if artist is None or metadata[0] == artist:  # metadata[0] is artist
                    self.remove_from_queue_at_index(i)
                    return

    def clear_queue(self) -> None:
        """Clear all items from the queue."""
        try:
            from core.logging import log_queue_operation

            log_queue_operation("clear", count=len(self.queue_items))
        except ImportError:
            pass

        self.queue_items = []
        self.current_index = 0
        self._shuffle_generated = False

    def get_queue_items(self) -> list[tuple]:
        """Get all items in the queue with their metadata.

        Returns:
            List of tuples: (filepath, artist, title, album, track_number, date)
        """
        items = []
        for filepath in self.queue_items:
            metadata = self.db.get_track_by_filepath(filepath)
            if metadata:
                # metadata is (artist, title, album, track_number, date)
                items.append((filepath, *metadata))
            else:
                # Fallback if metadata not found
                items.append((filepath, "", Path(filepath).stem, "", "", ""))
        return items

    def get_current_track(self) -> str | None:
        """Get currently playing track filepath.

        Returns:
            Filepath of current track, or None if queue empty
        """
        if 0 <= self.current_index < len(self.queue_items):
            return self.queue_items[self.current_index]
        return None

    def get_queue_count(self) -> int:
        """Get the number of items in the queue.

        Returns:
            Number of tracks in queue
        """
        return len(self.queue_items)

    def find_file_in_queue(self, title: str, artist: str = None) -> str | None:
        """Find a file in the queue based on its metadata."""
        for filepath in self.queue_items:
            metadata = self.db.get_track_by_filepath(filepath)
            if metadata and metadata[1] == title:  # metadata[1] is title
                if artist is None or metadata[0] == artist:  # metadata[0] is artist
                    return filepath
        return None

    def search_queue(self, search_text: str) -> list[tuple]:
        """Search queue items by text across artist, title, and album.

        Args:
            search_text: Text to search for

        Returns:
            List of matching queue items
        """
        if not search_text:
            return self.get_queue_items()

        search_lower = search_text.lower()
        results = []

        for filepath in self.queue_items:
            metadata = self.db.get_track_by_filepath(filepath)
            if metadata:
                artist, title, album, *_ = metadata
                if search_lower in artist.lower() or search_lower in title.lower() or search_lower in album.lower():
                    results.append((filepath, *metadata))

        return results

    def process_dropped_files(self, paths: list[str | Path]) -> None:
        """Process dropped files and add them to the queue.

        Args:
            paths: List of file paths to add
        """
        filepaths = []
        for path in paths:
            if path is None:
                continue

            try:
                normalized_path = normalize_path(path)
                if Path(normalized_path).exists():
                    filepaths.append(str(normalized_path))
            except (OSError, PermissionError) as e:
                print(f"Error accessing path {path}: {e}")
                continue

        if filepaths:
            self.add_to_queue_end(filepaths)

    def toggle_shuffle(self) -> bool:
        """Toggle shuffle mode on/off and return new state.

        When enabling shuffle with an existing queue, generates a new shuffle
        order immediately so that next/previous navigation works correctly.

        Returns:
            New shuffle state (True if enabled)
        """
        self.shuffle_enabled = not self.shuffle_enabled

        # If enabling shuffle and we have items in queue, generate shuffle order immediately
        if self.shuffle_enabled and self.queue_items:
            # Generate new shuffle order
            self._original_order = list(range(len(self.queue_items)))
            self._shuffled_order = self._original_order.copy()
            random.shuffle(self._shuffled_order)
            self._shuffle_generated = True

            # Find where the current track is in the new shuffle order
            with contextlib.suppress(ValueError):
                self._current_shuffle_pos = self._shuffled_order.index(self.current_index)
        else:
            # Invalidate shuffled order so it gets regenerated or disabled
            self._shuffle_generated = False
            self._current_shuffle_pos = 0

        return self.shuffle_enabled

    def is_shuffle_enabled(self) -> bool:
        """Return current shuffle state.

        Returns:
            True if shuffle is enabled
        """
        return self.shuffle_enabled

    def get_shuffled_queue_items(self) -> list[tuple]:
        """Get queue items in shuffled or original order based on shuffle state.

        Returns:
            List of queue items (possibly shuffled)
        """
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

    def next_track(self) -> str | None:
        """Advance to next track in queue.

        Returns:
            Filepath of next track, or None if at end
        """
        with self._lock:
            if not self.queue_items:
                return None

            total_items = len(self.queue_items)
            next_index = self.get_next_track_index(self.current_index, total_items)

            if next_index is not None:
                self.current_index = next_index
                return self.queue_items[self.current_index]

            return None

    def previous_track(self) -> str | None:
        """Go to previous track in queue.

        Returns:
            Filepath of previous track, or None if at beginning
        """
        with self._lock:
            if not self.queue_items:
                return None

            total_items = len(self.queue_items)
            prev_index = self.get_previous_track_index(self.current_index, total_items)

            if prev_index is not None:
                self.current_index = prev_index
                return self.queue_items[self.current_index]

            return None

    def get_next_track_index(self, current_index: int, total_items: int) -> int | None:
        """Get the index of the next track considering shuffle state.

        Args:
            current_index: Current track index
            total_items: Total number of items in queue

        Returns:
            Index of next track, or None if none available
        """
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
            with contextlib.suppress(ValueError, IndexError):
                # Try to find current position in shuffle sequence
                current_pos = self._shuffled_order.index(current_index)
                self._current_shuffle_pos = current_pos

            # Move to next position in shuffle sequence
            self._current_shuffle_pos = (self._current_shuffle_pos + 1) % len(self._shuffled_order)
            next_track = self._shuffled_order[self._current_shuffle_pos]

            return next_track
        else:
            # In normal mode, just go to next track
            if current_index < total_items - 1:
                return current_index + 1
            return None  # At end of queue

    def get_previous_track_index(self, current_index: int, total_items: int) -> int | None:
        """Get the index of the previous track considering shuffle state.

        Args:
            current_index: Current track index
            total_items: Total number of items in queue

        Returns:
            Index of previous track, or None if none available
        """
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
            with contextlib.suppress(ValueError, IndexError):
                # Try to find current position in shuffle sequence
                current_pos = self._shuffled_order.index(current_index)
                self._current_shuffle_pos = current_pos

            # Move to previous position in shuffle sequence
            self._current_shuffle_pos = (self._current_shuffle_pos - 1) % len(self._shuffled_order)
            prev_track = self._shuffled_order[self._current_shuffle_pos]
            return prev_track
        else:
            # In normal mode, just go to previous track
            if current_index > 0:
                return current_index - 1
            return None  # At beginning of queue
