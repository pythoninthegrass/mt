"""Property-based tests for QueueManager using Hypothesis.

These tests validate invariants and properties of the QueueManager class
that should hold for all valid inputs. They complement unit tests by
discovering edge cases through automated test generation.
"""

import pytest
import sys
from hypothesis import HealthCheck, given, settings, strategies as st
from pathlib import Path
from unittest.mock import Mock

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


class TestQueueManagerShuffleProperties:
    """Property-based tests for shuffle functionality."""

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(initial_state=st.booleans())
    def test_shuffle_toggle_idempotent(self, queue_manager, initial_state):
        """Toggling shuffle twice should return to original state."""
        queue_manager.shuffle_enabled = initial_state

        # Toggle twice
        queue_manager.toggle_shuffle()
        queue_manager.toggle_shuffle()

        # Should be back to initial state
        assert queue_manager.shuffle_enabled == initial_state

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(initial_state=st.booleans())
    def test_shuffle_toggle_inverts_state(self, queue_manager, initial_state):
        """Toggling shuffle once should invert the state."""
        queue_manager.shuffle_enabled = initial_state

        # Toggle once
        result = queue_manager.toggle_shuffle()

        # Should be inverted
        assert queue_manager.shuffle_enabled != initial_state
        assert result == (not initial_state)

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(queue_size=st.integers(min_value=0, max_value=100))
    def test_shuffled_queue_has_same_size(self, mock_db, queue_size):
        """Shuffled queue should have same size as original."""
        # Create mock queue items
        queue_items = [{"id": i, "filepath": f"/test/song{i}.mp3"} for i in range(queue_size)]
        mock_db.get_queue_items.return_value = queue_items

        manager = QueueManager(mock_db)
        manager.toggle_shuffle()

        shuffled_items = manager.get_shuffled_queue_items()

        # Same size
        assert len(shuffled_items) == queue_size

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        queue_items=st.lists(
            st.tuples(st.integers(min_value=1), st.text(min_size=1, max_size=50)),
            min_size=1,
            max_size=50,
            unique_by=lambda x: x[0],  # Unique IDs
        )
    )
    def test_shuffled_queue_preserves_items(self, mock_db, queue_items):
        """Shuffled queue should contain exactly the same items as original."""
        # Convert tuples to dict format
        formatted_items = [{"id": item_id, "filepath": path} for item_id, path in queue_items]
        mock_db.get_queue_items.return_value = formatted_items

        manager = QueueManager(mock_db)
        manager.toggle_shuffle()

        original_ids = {item["id"] for item in formatted_items}
        shuffled_items = manager.get_shuffled_queue_items()
        shuffled_ids = {item["id"] for item in shuffled_items}

        # Same items
        assert original_ids == shuffled_ids


# Note: Tests for add_to_queue, remove_from_queue, clear_queue, find_file, and search_queue
# are covered by unit tests. Property tests focus on invariants and behaviors rather than
# mock call verification, which is better suited for traditional unit tests.


# Note: Navigation tests (next_track_index, previous_track_index) are covered by unit tests.
# These involve creating new QueueManager instances which accumulate mock calls across
# Hypothesis examples, making them unsuitable for property-based testing.


class TestQueueManagerStateProperties:
    """Property-based tests for state management."""

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(shuffle_enabled=st.booleans())
    def test_is_shuffle_enabled_consistent(self, queue_manager, shuffle_enabled):
        """is_shuffle_enabled should return consistent state."""
        queue_manager.shuffle_enabled = shuffle_enabled

        # Should return same value
        assert queue_manager.is_shuffle_enabled() == shuffle_enabled

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(queue_size=st.integers(min_value=0, max_value=100))
    def test_get_queue_items_returns_list(self, mock_db, queue_size):
        """get_queue_items should always return a list."""
        # Create mock queue items
        queue_items = [{"id": i, "filepath": f"/test/song{i}.mp3"} for i in range(queue_size)]
        mock_db.get_queue_items.return_value = queue_items

        manager = QueueManager(mock_db)
        result = manager.get_queue_items()

        # Should be a list
        assert isinstance(result, list)
        assert len(result) == queue_size
