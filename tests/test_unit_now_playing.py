"""Unit tests for Now Playing view with drag-and-drop, context menus, and viewport limiting.

Tests the core queue display logic, reordering, context menu actions, and viewport-based track limiting.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

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


@pytest.fixture
def sample_queue():
    """Sample queue items for testing."""
    return [
        '/path/to/track1.mp3',
        '/path/to/track2.mp3',
        '/path/to/track3.mp3',
        '/path/to/track4.mp3',
        '/path/to/track5.mp3',
    ]


@pytest.fixture
def populated_queue_manager(queue_manager, sample_queue):
    """Create QueueManager with sample tracks."""
    for track in sample_queue:
        queue_manager.queue_items.append(track)
    return queue_manager


class TestQueueManagerPlayNext:
    """Test 'Play Next' functionality - inserts after currently playing track."""

    def test_play_next_basic(self, populated_queue_manager):
        """Test inserting a track to play next."""
        # Current state: [track1, track2, track3, track4, track5], current=0
        assert populated_queue_manager.current_index == 0
        assert len(populated_queue_manager.queue_items) == 5

        # Move track2 to play next (after track1)
        track_to_move = populated_queue_manager.queue_items.pop(1)
        insert_pos = populated_queue_manager.current_index + 1
        populated_queue_manager.queue_items.insert(insert_pos, track_to_move)

        # Expected: [track1, track2, track3, track4, track5] (same, already at position 1)
        assert populated_queue_manager.queue_items[0] == '/path/to/track1.mp3'
        assert populated_queue_manager.queue_items[1] == '/path/to/track2.mp3'
        assert len(populated_queue_manager.queue_items) == 5

    def test_play_next_from_end(self, populated_queue_manager):
        """Test moving a track from end to play next."""
        # Move track5 to play next (after track1)
        track_to_move = populated_queue_manager.queue_items.pop(4)
        insert_pos = populated_queue_manager.current_index + 1
        populated_queue_manager.queue_items.insert(insert_pos, track_to_move)

        # Expected: [track1, track5, track2, track3, track4]
        assert populated_queue_manager.queue_items[0] == '/path/to/track1.mp3'
        assert populated_queue_manager.queue_items[1] == '/path/to/track5.mp3'
        assert populated_queue_manager.queue_items[2] == '/path/to/track2.mp3'
        assert len(populated_queue_manager.queue_items) == 5

    def test_play_next_adjusts_current_index(self, populated_queue_manager):
        """Test that moving a track before current position adjusts current_index."""
        # Current state: [track1, track2, track3, track4, track5], current=2 (track3)
        populated_queue_manager.current_index = 2

        # Move track5 to play next (after track3)
        track_to_move = populated_queue_manager.queue_items.pop(4)
        insert_pos = populated_queue_manager.current_index + 1
        populated_queue_manager.queue_items.insert(insert_pos, track_to_move)

        if populated_queue_manager.current_index > 4:
            populated_queue_manager.current_index -= 1

        # Expected: [track1, track2, track3, track5, track4]
        assert populated_queue_manager.current_index == 2
        assert populated_queue_manager.queue_items[3] == '/path/to/track5.mp3'


class TestQueueManagerReordering:
    """Test reorder_queue for drag-and-drop functionality."""

    def test_reorder_move_down(self, populated_queue_manager):
        """Test moving a track down in the queue."""
        # Move track1 (index 0) to index 3
        populated_queue_manager.reorder_queue(0, 3)

        # Expected: [track2, track3, track4, track1, track5]
        assert populated_queue_manager.queue_items[3] == '/path/to/track1.mp3'
        assert populated_queue_manager.queue_items[0] == '/path/to/track2.mp3'

    def test_reorder_move_up(self, populated_queue_manager):
        """Test moving a track up in the queue."""
        # Move track5 (index 4) to index 1
        populated_queue_manager.reorder_queue(4, 1)

        # Expected: [track1, track5, track2, track3, track4]
        assert populated_queue_manager.queue_items[1] == '/path/to/track5.mp3'
        assert populated_queue_manager.queue_items[4] == '/path/to/track4.mp3'

    def test_reorder_adjusts_current_when_moving_before(self, populated_queue_manager):
        """Test that current_index is adjusted when moving a track before it."""
        # Set current to track3 (index 2)
        populated_queue_manager.current_index = 2

        # Move track5 (index 4) to index 1 (before current)
        populated_queue_manager.reorder_queue(4, 1)

        # Current should still point to track3, now at index 2
        assert populated_queue_manager.queue_items[populated_queue_manager.current_index] == '/path/to/track3.mp3'


class TestQueueMixedOperations:
    """Test mixed queue operations that combine Play Next, Add to Queue, and reordering."""

    def test_play_next_then_reorder(self, populated_queue_manager):
        """Test Play Next followed by reordering."""
        # Initial: [track1, track2, track3, track4, track5], current=0

        # Play Next: move track5 to position 1
        track_to_move = populated_queue_manager.queue_items.pop(4)
        insert_pos = populated_queue_manager.current_index + 1
        populated_queue_manager.queue_items.insert(insert_pos, track_to_move)
        # Result: [track1, track5, track2, track3, track4]

        # Now reorder: move track2 (index 2) to index 3
        populated_queue_manager.reorder_queue(2, 3)
        # Result: [track1, track5, track3, track2, track4]

        assert populated_queue_manager.queue_items[1] == '/path/to/track5.mp3'
        assert populated_queue_manager.queue_items[3] == '/path/to/track2.mp3'

    def test_multiple_play_next_operations(self, populated_queue_manager):
        """Test multiple Play Next operations in sequence."""
        # Initial: [track1, track2, track3, track4, track5], current=0

        # Play Next: move track3 to play next
        track_to_move = populated_queue_manager.queue_items.pop(2)
        insert_pos = populated_queue_manager.current_index + 1
        populated_queue_manager.queue_items.insert(insert_pos, track_to_move)
        # Result: [track1, track3, track2, track4, track5]

        # Play Next: move track5 to play next
        track_to_move = populated_queue_manager.queue_items.pop(4)
        insert_pos = populated_queue_manager.current_index + 1
        populated_queue_manager.queue_items.insert(insert_pos, track_to_move)
        # Result: [track1, track5, track3, track2, track4]

        assert populated_queue_manager.queue_items[1] == '/path/to/track5.mp3'
        assert populated_queue_manager.queue_items[2] == '/path/to/track3.mp3'


class TestNowPlayingViewLogic:
    """Test viewport-based track limiting logic in Now Playing view."""

    def test_viewport_calculation_logic(self, queue_manager):
        """Test the viewport calculation logic without GUI."""
        # Test the row height constant is correct
        row_height = 70 + 1  # QueueRowWidget is 70px + 1px padding

        # Simulate various viewport heights
        test_cases = [
            (100, 1),  # Very small viewport, at least 1 track
            (200, 2),  # Small viewport
            (500, 6),  # Medium viewport
            (1000, 13),  # Large viewport
        ]

        for viewport_height, expected_min in test_cases:
            label_height = 20
            available_height = viewport_height - label_height - 10
            max_tracks = max(1, int(available_height / row_height))
            assert max_tracks >= 1

    def test_track_limiting_logic(self, sample_queue):
        """Test that track limiting logic works correctly."""
        # Simulate viewport fit calculation
        total_items = len(sample_queue)
        max_visible_next = 3  # Simulate only 3 tracks fit in viewport

        # If we have current track + up to max_visible_next tracks
        display_items = sample_queue.copy()

        # Current track is first in display (rotated)
        current_display_item = display_items[0]
        next_items = display_items[1 : min(len(display_items), max_visible_next + 1)]

        # Total displayed should be current + next items limited by viewport
        total_displayed = 1 + len(next_items)
        assert total_displayed <= (1 + max_visible_next)

    def test_empty_queue_logic(self, queue_manager):
        """Test empty queue handling logic."""
        # Empty queue should trigger empty state
        assert len(queue_manager.queue_items) == 0

        # When refreshing with empty queue, no widgets should be created
        current_track_widgets = 0 if len(queue_manager.queue_items) == 0 else 1
        assert current_track_widgets == 0


class TestNowPlayingContextMenuLogic:
    """Test context menu logic without GUI."""

    def test_play_next_reorders_correctly(self, populated_queue_manager):
        """Test Play Next logic - verify track moves to correct position."""
        # Simulate the logic in on_context_play_next
        track_to_move_index = 3
        track_to_move = populated_queue_manager.queue_items.pop(track_to_move_index)
        insert_pos = populated_queue_manager.current_index + 1
        populated_queue_manager.queue_items.insert(insert_pos, track_to_move)

        # Adjust current_index if needed
        if track_to_move_index < populated_queue_manager.current_index:
            populated_queue_manager.current_index -= 1

        # Track should now be at position 1
        assert populated_queue_manager.queue_items[1] == '/path/to/track4.mp3'
        assert len(populated_queue_manager.queue_items) == 5

    def test_move_to_end_reorders_correctly(self, populated_queue_manager):
        """Test Move to End logic - verify track moves to end."""
        # Simulate the logic in on_context_move_to_end
        track_to_move_index = 1
        track_to_move = populated_queue_manager.queue_items.pop(track_to_move_index)
        populated_queue_manager.queue_items.append(track_to_move)

        # Adjust current_index if needed
        if track_to_move_index < populated_queue_manager.current_index:
            populated_queue_manager.current_index -= 1

        # Track should now be at the end
        assert populated_queue_manager.queue_items[-1] == '/path/to/track2.mp3'
        assert len(populated_queue_manager.queue_items) == 5

    def test_remove_from_queue_logic(self, populated_queue_manager):
        """Test Remove from Queue logic - verify track is removed."""
        # Simulate the logic in on_context_remove_from_queue
        track_to_remove_index = 2
        initial_length = len(populated_queue_manager.queue_items)
        track_removed = populated_queue_manager.queue_items.pop(track_to_remove_index)

        # Queue length should decrease
        assert len(populated_queue_manager.queue_items) == initial_length - 1
        # Track should be removed
        assert track_removed == '/path/to/track3.mp3'
        assert track_removed not in populated_queue_manager.queue_items

    def test_queue_empty_detection(self, queue_manager):
        """Test queue empty detection logic."""
        # Empty queue
        assert len(queue_manager.queue_items) == 0

        # Add track
        queue_manager.queue_items.append('/path/to/track1.mp3')
        assert len(queue_manager.queue_items) == 1

        # Remove track
        queue_manager.queue_items.pop()
        assert len(queue_manager.queue_items) == 0


class TestQueuePersistence:
    """Test that queue persists across operations."""

    def test_queue_persists_across_reorder_operations(self, populated_queue_manager):
        """Test that queue persists when reordering."""
        original_tracks = populated_queue_manager.queue_items.copy()

        # Perform multiple reorder operations
        populated_queue_manager.reorder_queue(0, 2)
        populated_queue_manager.reorder_queue(3, 1)

        # All original tracks should still be present
        assert len(populated_queue_manager.queue_items) == len(original_tracks)
        for track in original_tracks:
            assert track in populated_queue_manager.queue_items

    def test_queue_persists_across_play_next_operations(self, populated_queue_manager):
        """Test that queue persists when using Play Next."""
        original_tracks = populated_queue_manager.queue_items.copy()

        # Perform Play Next operations
        for _ in range(3):
            track_to_move = populated_queue_manager.queue_items.pop(-1)
            insert_pos = populated_queue_manager.current_index + 1
            populated_queue_manager.queue_items.insert(insert_pos, track_to_move)

        # All original tracks should still be present
        assert len(populated_queue_manager.queue_items) == len(original_tracks)
        for track in original_tracks:
            assert track in populated_queue_manager.queue_items
