"""Unit tests for QueueManager with in-memory queue.

These tests use mocked database for metadata operations only.
They test the core in-memory queue logic deterministically.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.queue import QueueManager


@pytest.fixture
def mock_db():
    """Mock MusicDatabase for metadata operations."""
    db = Mock()
    db.get_shuffle_enabled.return_value = False
    db.get_track_by_filepath.return_value = None
    return db


@pytest.fixture
def queue_manager(mock_db):
    """Create QueueManager with mocked database."""
    return QueueManager(mock_db)


class TestQueueManagerInitialization:
    """Test QueueManager initialization."""

    def test_initialization(self, queue_manager, mock_db):
        """Test that QueueManager initializes with correct default values."""
        assert queue_manager.db == mock_db
        assert queue_manager.shuffle_enabled is False
        assert queue_manager.queue_items == []
        assert queue_manager.current_index == 0
        assert queue_manager._shuffled_order == []
        assert queue_manager._shuffle_generated is False

    def test_initialization_with_shuffle_enabled(self, mock_db):
        """Test initialization always starts with shuffle disabled."""
        # Note: shuffle state is not loaded from database on init
        # It's managed in-memory only during the session
        manager = QueueManager(mock_db)
        assert manager.shuffle_enabled is False


class TestQueueManagerBasicOperations:
    """Test basic queue operations."""

    def test_populate_and_play(self, queue_manager):
        """Test populating queue and starting playback."""
        filepaths = ["/test/song1.mp3", "/test/song2.mp3", "/test/song3.mp3"]

        result = queue_manager.populate_and_play(filepaths, start_index=1)

        assert queue_manager.queue_items == filepaths
        assert queue_manager.current_index == 1
        assert result == "/test/song2.mp3"
        assert queue_manager._shuffle_generated is False

    def test_populate_and_play_empty(self, queue_manager):
        """Test populating with empty list."""
        result = queue_manager.populate_and_play([])

        assert queue_manager.queue_items == []
        assert result is None

    def test_insert_after_current(self, queue_manager):
        """Test inserting tracks after current position."""
        # Setup initial queue
        queue_manager.queue_items = ["/test/song1.mp3", "/test/song2.mp3", "/test/song5.mp3"]
        queue_manager.current_index = 1

        # Insert new tracks after current
        queue_manager.insert_after_current(["/test/song3.mp3", "/test/song4.mp3"])

        expected = ["/test/song1.mp3", "/test/song2.mp3", "/test/song3.mp3", "/test/song4.mp3", "/test/song5.mp3"]
        assert queue_manager.queue_items == expected
        assert queue_manager.current_index == 1  # Should remain unchanged

    def test_insert_after_current_empty_queue(self, queue_manager):
        """Test inserting into empty queue."""
        queue_manager.insert_after_current(["/test/song1.mp3"])

        assert queue_manager.queue_items == ["/test/song1.mp3"]

    def test_add_to_queue_end(self, queue_manager):
        """Test adding tracks to end of queue."""
        queue_manager.queue_items = ["/test/song1.mp3"]

        queue_manager.add_to_queue_end(["/test/song2.mp3", "/test/song3.mp3"])

        assert queue_manager.queue_items == ["/test/song1.mp3", "/test/song2.mp3", "/test/song3.mp3"]

    def test_remove_from_queue_at_index(self, queue_manager):
        """Test removing track at specific index."""
        queue_manager.queue_items = ["/test/song1.mp3", "/test/song2.mp3", "/test/song3.mp3"]
        queue_manager.current_index = 1

        queue_manager.remove_from_queue_at_index(2)

        assert queue_manager.queue_items == ["/test/song1.mp3", "/test/song2.mp3"]
        assert queue_manager.current_index == 1  # Unchanged

    def test_remove_current_track(self, queue_manager):
        """Test removing the currently playing track."""
        queue_manager.queue_items = ["/test/song1.mp3", "/test/song2.mp3", "/test/song3.mp3"]
        queue_manager.current_index = 1

        queue_manager.remove_from_queue_at_index(1)

        assert queue_manager.queue_items == ["/test/song1.mp3", "/test/song3.mp3"]
        assert queue_manager.current_index == 1  # Adjusted to next track

    def test_get_queue_items(self, queue_manager, mock_db):
        """Test getting queue items."""
        # Setup queue
        queue_manager.queue_items = ["/test/song1.mp3", "/test/song2.mp3"]

        # Mock database to return metadata (without filepath)
        def get_track(filepath):
            if "song1" in filepath:
                return ("Artist 1", "Title 1", "Album 1", "01", "2024")
            if "song2" in filepath:
                return ("Artist 2", "Title 2", "Album 2", "02", "2024")
            return None

        mock_db.get_track_by_filepath.side_effect = get_track

        items = queue_manager.get_queue_items()

        assert len(items) == 2
        assert items[0] == ("/test/song1.mp3", "Artist 1", "Title 1", "Album 1", "01", "2024")
        assert items[1] == ("/test/song2.mp3", "Artist 2", "Title 2", "Album 2", "02", "2024")


class TestQueueManagerReordering:
    """Test queue reordering functionality."""

    def test_reorder_queue_basic(self, queue_manager):
        """Test moving track from one position to another."""
        queue_manager.queue_items = ["/test/song1.mp3", "/test/song2.mp3", "/test/song3.mp3", "/test/song4.mp3"]
        queue_manager.current_index = 0

        queue_manager.reorder_queue(from_index=1, to_index=3)

        # song2 should move from position 1 to position 3
        expected = ["/test/song1.mp3", "/test/song3.mp3", "/test/song4.mp3", "/test/song2.mp3"]
        assert queue_manager.queue_items == expected

    def test_reorder_adjusts_current_index(self, queue_manager):
        """Test that current_index adjusts when moving currently playing track."""
        queue_manager.queue_items = ["/test/song1.mp3", "/test/song2.mp3", "/test/song3.mp3"]
        queue_manager.current_index = 1

        queue_manager.reorder_queue(from_index=1, to_index=0)

        assert queue_manager.current_index == 0  # Moved with track

    def test_reorder_adjusts_index_when_moving_before(self, queue_manager):
        """Test current_index adjustment when moving track before current."""
        queue_manager.queue_items = ["/test/song1.mp3", "/test/song2.mp3", "/test/song3.mp3"]
        queue_manager.current_index = 2

        queue_manager.reorder_queue(from_index=0, to_index=1)

        assert queue_manager.current_index == 2  # Should remain at same track


class TestQueueManagerNavigation:
    """Test track navigation functionality."""

    def test_get_current_track(self, queue_manager):
        """Test getting current track."""
        queue_manager.queue_items = ["/test/song1.mp3", "/test/song2.mp3"]
        queue_manager.current_index = 1

        assert queue_manager.get_current_track() == "/test/song2.mp3"

    def test_get_current_track_empty_queue(self, queue_manager):
        """Test getting current track from empty queue."""
        assert queue_manager.get_current_track() is None

    def test_next_track(self, queue_manager):
        """Test moving to next track."""
        queue_manager.queue_items = ["/test/song1.mp3", "/test/song2.mp3", "/test/song3.mp3"]
        queue_manager.current_index = 0

        result = queue_manager.next_track()

        assert result == "/test/song2.mp3"
        assert queue_manager.current_index == 1

    def test_next_track_at_end_returns_none(self, queue_manager):
        """Test next track returns None when at end (no wrapping)."""
        queue_manager.queue_items = ["/test/song1.mp3", "/test/song2.mp3"]
        queue_manager.current_index = 1

        result = queue_manager.next_track()

        assert result is None
        assert queue_manager.current_index == 1  # Stays at same position

    def test_previous_track(self, queue_manager):
        """Test moving to previous track."""
        queue_manager.queue_items = ["/test/song1.mp3", "/test/song2.mp3", "/test/song3.mp3"]
        queue_manager.current_index = 2

        result = queue_manager.previous_track()

        assert result == "/test/song2.mp3"
        assert queue_manager.current_index == 1

    def test_previous_track_at_beginning_returns_none(self, queue_manager):
        """Test previous track returns None when at beginning (no wrapping)."""
        queue_manager.queue_items = ["/test/song1.mp3", "/test/song2.mp3"]
        queue_manager.current_index = 0

        result = queue_manager.previous_track()

        assert result is None
        assert queue_manager.current_index == 0  # Stays at same position


class TestQueueManagerShuffle:
    """Test shuffle functionality."""

    def test_toggle_shuffle_off_to_on(self, queue_manager):
        """Test enabling shuffle."""
        queue_manager.shuffle_enabled = False

        result = queue_manager.toggle_shuffle()

        assert result is True
        assert queue_manager.shuffle_enabled is True

    def test_toggle_shuffle_on_to_off(self, queue_manager):
        """Test disabling shuffle."""
        queue_manager.shuffle_enabled = True

        result = queue_manager.toggle_shuffle()

        assert result is False
        assert queue_manager.shuffle_enabled is False

    def test_toggle_shuffle_invalidates_shuffled_order(self, queue_manager):
        """Test that toggling shuffle invalidates the shuffled order."""
        queue_manager._shuffle_generated = True

        queue_manager.toggle_shuffle()

        assert queue_manager._shuffle_generated is False

    def test_is_shuffle_enabled(self, queue_manager):
        """Test checking shuffle state."""
        queue_manager.shuffle_enabled = True
        assert queue_manager.is_shuffle_enabled() is True

        queue_manager.shuffle_enabled = False
        assert queue_manager.is_shuffle_enabled() is False


class TestQueueManagerProcessDroppedFiles:
    """Test processing dropped files."""

    def test_process_dropped_files_adds_to_queue(self, queue_manager):
        """Test that valid dropped files are added to queue."""
        files = ["/test/song1.mp3", "/test/song2.mp3"]

        # Mock Path.exists to return True
        with patch.object(Path, "exists", return_value=True):
            queue_manager.process_dropped_files(files)

        # Should add files to end of queue
        assert len(queue_manager.queue_items) == 2
        assert "/test/song1.mp3" in queue_manager.queue_items
        assert "/test/song2.mp3" in queue_manager.queue_items

    def test_process_dropped_files_skips_none(self, queue_manager):
        """Test that None values in dropped files are skipped."""
        files = ["/test/song1.mp3", None, "/test/song2.mp3"]

        # Mock Path.exists to return True for valid paths
        with patch.object(Path, "exists", return_value=True):
            queue_manager.process_dropped_files(files)

        # Should only add the non-None files
        assert len(queue_manager.queue_items) == 2

    def test_process_dropped_files_skips_nonexistent(self, queue_manager):
        """Test that non-existent files are skipped."""
        files = ["/test/exists.mp3", "/test/does_not_exist.mp3"]

        # Mock Path.exists to return True for first file, False for second
        mock_exists = Mock(side_effect=[True, False])
        with patch.object(Path, "exists", mock_exists):
            queue_manager.process_dropped_files(files)

        # Should only add the existing file
        assert len(queue_manager.queue_items) == 1
        assert "/test/exists.mp3" in queue_manager.queue_items


class TestQueueManagerSearch:
    """Test queue search functionality."""

    def test_search_queue(self, queue_manager, mock_db):
        """Test searching queue."""
        # Setup queue
        queue_manager.queue_items = ["/test/song1.mp3", "/test/song2.mp3", "/test/other.mp3"]

        # Mock database to return metadata (without filepath)
        def get_track(filepath):
            if "song1" in filepath:
                return ("Test Artist", "Test Song 1", "Album", "01", "2024")
            if "song2" in filepath:
                return ("Test Artist", "Test Song 2", "Album", "02", "2024")
            if "other" in filepath:
                return ("Other Artist", "Other Song", "Album", "03", "2024")
            return None

        mock_db.get_track_by_filepath.side_effect = get_track

        # Search for "Test"
        results = queue_manager.search_queue("Test")

        # Should return tracks matching "Test"
        assert len(results) == 2
        assert all("Test" in str(result) for result in results)

    def test_search_queue_no_results(self, queue_manager, mock_db):
        """Test searching queue with no matches."""
        queue_manager.queue_items = ["/test/song1.mp3"]

        def get_track(filepath):
            return (filepath, "Artist", "Title", "Album", "01", "2024")

        mock_db.get_track_by_filepath.side_effect = get_track

        results = queue_manager.search_queue("NonExistent")

        assert len(results) == 0
