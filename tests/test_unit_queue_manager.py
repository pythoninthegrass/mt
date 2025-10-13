"""Unit tests for QueueManager using mocked database.

These tests use mocked database to avoid external dependencies.
They run fast (<1s total) and test core logic deterministically.
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
    """Mock MusicDatabase."""
    db = Mock()
    db.get_shuffle_enabled.return_value = False
    db.get_queue_items.return_value = []
    db.add_to_queue.return_value = None
    db.remove_from_queue.return_value = None
    db.clear_queue.return_value = None
    db.find_file_in_queue.return_value = None
    db.search_queue.return_value = []
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
        assert queue_manager._original_order == []
        assert queue_manager._shuffled_order == []
        assert queue_manager._shuffle_generated is False
        assert queue_manager._current_shuffle_pos == 0

    def test_initialization_with_shuffle_enabled(self, mock_db):
        """Test initialization when shuffle is enabled in database."""
        mock_db.get_shuffle_enabled.return_value = True
        manager = QueueManager(mock_db)
        assert manager.shuffle_enabled is True


class TestQueueManagerBasicOperations:
    """Test basic queue operations."""

    def test_add_to_queue(self, queue_manager, mock_db):
        """Test adding a file to queue."""
        filepath = "/path/to/song1.mp3"
        queue_manager.add_to_queue(filepath)

        # Should call database add_to_queue with the filepath
        mock_db.add_to_queue.assert_called_once_with(filepath)

    def test_remove_from_queue(self, queue_manager, mock_db):
        """Test removing item from queue by metadata."""
        title = "Test Song"
        artist = "Test Artist"
        queue_manager.remove_from_queue(title, artist)

        mock_db.remove_from_queue.assert_called_once_with(title, artist, None, None)

    def test_clear_queue(self, queue_manager, mock_db):
        """Test clearing queue."""
        queue_manager.clear_queue()

        mock_db.clear_queue.assert_called_once()

    def test_get_queue_items(self, queue_manager, mock_db):
        """Test getting queue items."""
        expected_items = [
            {"id": 1, "filepath": "/test/song1.mp3"},
            {"id": 2, "filepath": "/test/song2.mp3"},
        ]
        mock_db.get_queue_items.return_value = expected_items

        items = queue_manager.get_queue_items()

        assert items == expected_items
        mock_db.get_queue_items.assert_called_once()


class TestQueueManagerSearch:
    """Test queue search functionality."""

    def test_find_file_in_queue(self, queue_manager, mock_db):
        """Test finding a file in queue by metadata."""
        title = "Test Song"
        artist = "Test Artist"
        expected_result = "/test/song.mp3"
        mock_db.find_file_in_queue.return_value = expected_result

        result = queue_manager.find_file_in_queue(title, artist)

        assert result == expected_result
        mock_db.find_file_in_queue.assert_called_once_with(title, artist)

    def test_search_queue(self, queue_manager, mock_db):
        """Test searching queue."""
        query = "test query"
        expected_results = [
            {"id": 1, "title": "Test Song 1"},
            {"id": 2, "title": "Test Song 2"},
        ]
        mock_db.search_queue.return_value = expected_results

        results = queue_manager.search_queue(query)

        assert results == expected_results
        mock_db.search_queue.assert_called_once_with(query)


class TestQueueManagerShuffle:
    """Test shuffle functionality."""

    def test_toggle_shuffle_off_to_on(self, queue_manager, mock_db):
        """Test enabling shuffle."""
        queue_manager.shuffle_enabled = False

        result = queue_manager.toggle_shuffle()

        assert result is True
        assert queue_manager.shuffle_enabled is True
        mock_db.set_shuffle_enabled.assert_called_once_with(True)

    def test_toggle_shuffle_on_to_off(self, queue_manager, mock_db):
        """Test disabling shuffle."""
        queue_manager.shuffle_enabled = True

        result = queue_manager.toggle_shuffle()

        assert result is False
        assert queue_manager.shuffle_enabled is False
        mock_db.set_shuffle_enabled.assert_called_once_with(False)

    def test_toggle_shuffle_invalidates_shuffled_order(self, queue_manager):
        """Test that toggling shuffle invalidates the shuffled order."""
        queue_manager._shuffle_generated = True
        queue_manager._current_shuffle_pos = 5

        queue_manager.toggle_shuffle()

        assert queue_manager._shuffle_generated is False
        assert queue_manager._current_shuffle_pos == 0

    def test_is_shuffle_enabled(self, queue_manager):
        """Test checking shuffle state."""
        queue_manager.shuffle_enabled = True
        assert queue_manager.is_shuffle_enabled() is True

        queue_manager.shuffle_enabled = False
        assert queue_manager.is_shuffle_enabled() is False

    def test_get_shuffled_queue_items_when_disabled(self, queue_manager, mock_db):
        """Test getting shuffled items when shuffle is disabled."""
        queue_manager.shuffle_enabled = False
        expected_items = [{"id": 1}, {"id": 2}, {"id": 3}]
        mock_db.get_queue_items.return_value = expected_items

        items = queue_manager.get_shuffled_queue_items()

        # Should return items in original order
        assert items == expected_items

    def test_get_shuffled_queue_items_when_enabled(self, queue_manager, mock_db):
        """Test getting shuffled items when shuffle is enabled."""
        queue_manager.shuffle_enabled = True
        original_items = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}]
        mock_db.get_queue_items.return_value = original_items

        items = queue_manager.get_shuffled_queue_items()

        # Should return same items but potentially in different order
        assert len(items) == len(original_items)
        assert set(item["id"] for item in items) == set(item["id"] for item in original_items)


class TestQueueManagerTrackNavigation:
    """Test track navigation (next/previous) functionality."""

    def test_get_next_track_index_sequential_mode(self, queue_manager, mock_db):
        """Test getting next track in sequential mode."""
        queue_manager.shuffle_enabled = False
        total_items = 3

        # Get next after first track
        next_index = queue_manager.get_next_track_index(current_index=0, total_items=total_items)
        assert next_index == 1

        # Get next after second track
        next_index = queue_manager.get_next_track_index(current_index=1, total_items=total_items)
        assert next_index == 2

    def test_get_next_track_index_at_end(self, queue_manager, mock_db):
        """Test getting next track when at end of queue (wraps in sequential mode)."""
        queue_manager.shuffle_enabled = False
        total_items = 2

        # In sequential mode, it wraps around using modulo
        next_index = queue_manager.get_next_track_index(current_index=1, total_items=total_items)
        assert next_index == 0  # Wraps to beginning

    def test_get_next_track_index_empty_queue(self, queue_manager):
        """Test getting next track with empty queue."""
        queue_manager.shuffle_enabled = False

        # Should return None when queue is empty
        next_index = queue_manager.get_next_track_index(current_index=0, total_items=0)
        assert next_index is None

    def test_get_previous_track_index_sequential_mode(self, queue_manager, mock_db):
        """Test getting previous track in sequential mode."""
        queue_manager.shuffle_enabled = False
        total_items = 3

        # Get previous from third track
        prev_index = queue_manager.get_previous_track_index(current_index=2, total_items=total_items)
        assert prev_index == 1

        # Get previous from second track
        prev_index = queue_manager.get_previous_track_index(current_index=1, total_items=total_items)
        assert prev_index == 0

    def test_get_previous_track_index_at_beginning(self, queue_manager, mock_db):
        """Test getting previous track when at beginning of queue (wraps in sequential mode)."""
        queue_manager.shuffle_enabled = False
        total_items = 2

        # In sequential mode, it wraps around using modulo
        prev_index = queue_manager.get_previous_track_index(current_index=0, total_items=total_items)
        assert prev_index == 1  # Wraps to end

    def test_get_previous_track_index_empty_queue(self, queue_manager):
        """Test getting previous track with empty queue."""
        queue_manager.shuffle_enabled = False

        # Should return None when queue is empty
        prev_index = queue_manager.get_previous_track_index(current_index=0, total_items=0)
        assert prev_index is None


class TestQueueManagerProcessDroppedFiles:
    """Test processing dropped files."""

    def test_process_dropped_files_skips_none(self, queue_manager, mock_db):
        """Test that None values in dropped files are skipped."""
        files = ["/test/song1.mp3", None, "/test/song2.mp3"]

        # Mock Path.exists to return True
        with patch.object(Path, "exists", return_value=True):
            queue_manager.process_dropped_files(files)

        # Should only add the non-None files
        assert mock_db.add_to_queue.call_count == 2

    def test_process_dropped_files_skips_nonexistent(self, queue_manager, mock_db):
        """Test that non-existent files are skipped."""
        files = ["/test/exists.mp3", "/test/does_not_exist.mp3"]

        # Mock Path.exists to return True for first file, False for second
        mock_exists = Mock(side_effect=[True, False])
        with patch.object(Path, "exists", mock_exists):
            queue_manager.process_dropped_files(files)

        # Should only add the existing file
        assert mock_db.add_to_queue.call_count == 1
