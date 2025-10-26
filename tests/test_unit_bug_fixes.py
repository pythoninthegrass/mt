"""Unit tests for bug fixes from Python 3.12 migration.

These tests cover specific methods that were added or modified during bug fixes
and currently lack test coverage.
"""

import pytest
import sys
from pathlib import Path
from tkinter import Tk
from unittest.mock import MagicMock, Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestPlayerControlsUpdatePlayButton:
    """Test update_play_button() method icon changes.

    These tests verify the logic of update_play_button() by mocking the button
    widget and checking that it's configured correctly.
    """

    def test_update_play_button_when_playing(self):
        """Test that update_play_button shows pause symbol when playing."""
        from config import BUTTON_SYMBOLS
        from core.gui.player_controls import PlayerControls

        # Create a mock PlayerControls instance
        controls = Mock(spec=PlayerControls)
        controls.play_button = Mock()

        # Call the actual method
        PlayerControls.update_play_button(controls, True)

        # Verify the button.configure was called with pause symbol
        controls.play_button.configure.assert_called_once()
        call_kwargs = controls.play_button.configure.call_args[1]
        assert call_kwargs['text'] == BUTTON_SYMBOLS['pause']
        assert call_kwargs['fg'] == '#FFFFFF'  # Bright white when active

    def test_update_play_button_when_paused(self):
        """Test that update_play_button shows play symbol when paused."""
        from config import BUTTON_SYMBOLS
        from core.gui.player_controls import PlayerControls

        # Create a mock PlayerControls instance
        controls = Mock(spec=PlayerControls)
        controls.play_button = Mock()

        # Call the actual method
        PlayerControls.update_play_button(controls, False)

        # Verify the button.configure was called with play symbol
        controls.play_button.configure.assert_called_once()
        call_kwargs = controls.play_button.configure.call_args[1]
        assert call_kwargs['text'] == BUTTON_SYMBOLS['play']
        assert call_kwargs['fg'] == '#CCCCCC'  # Light gray when paused

    def test_update_play_button_toggle(self):
        """Test toggling play button between play and pause states."""
        from config import BUTTON_SYMBOLS
        from core.gui.player_controls import PlayerControls

        # Create a mock PlayerControls instance
        controls = Mock(spec=PlayerControls)
        controls.play_button = Mock()

        # Start paused
        PlayerControls.update_play_button(controls, False)
        call1_kwargs = controls.play_button.configure.call_args[1]
        assert call1_kwargs['text'] == BUTTON_SYMBOLS['play']

        # Reset mock to track next call
        controls.play_button.configure.reset_mock()

        # Toggle to playing
        PlayerControls.update_play_button(controls, True)
        call2_kwargs = controls.play_button.configure.call_args[1]
        assert call2_kwargs['text'] == BUTTON_SYMBOLS['pause']

        # Reset mock to track next call
        controls.play_button.configure.reset_mock()

        # Toggle back to paused
        PlayerControls.update_play_button(controls, False)
        call3_kwargs = controls.play_button.configure.call_args[1]
        assert call3_kwargs['text'] == BUTTON_SYMBOLS['play']


class TestGetAllFilepathsFromView:
    """Test _get_all_filepaths_from_view() filepath extraction."""

    @pytest.fixture
    def mock_queue_view(self):
        """Create a mock queue view."""
        queue_view = Mock()
        queue = Mock()

        # Mock the treeview with item IDs
        item_ids = ['item1', 'item2', 'item3', 'item4']
        queue.get_children.return_value = item_ids

        queue_view.queue = queue
        return queue_view, item_ids

    @pytest.fixture
    def library_manager(self, mock_queue_view):
        """Create PlayerLibraryManager instance with mocked dependencies."""
        from core.player.library import PlayerLibraryManager

        queue_view, item_ids = mock_queue_view

        # Create minimal mock dependencies
        window = Mock()
        db = Mock()
        library_mgr = Mock()
        favorites_mgr = Mock()
        library_view = Mock()
        status_bar = Mock()
        now_playing_view = Mock()
        refresh_callback = Mock()

        manager = PlayerLibraryManager(
            window=window,
            db=db,
            library_manager=library_mgr,
            favorites_manager=favorites_mgr,
            library_view=library_view,
            queue_view=queue_view,
            status_bar=status_bar,
            now_playing_view=now_playing_view,
            refresh_colors_callback=refresh_callback
        )

        return manager, item_ids

    def test_get_all_filepaths_from_view_in_order(self, library_manager):
        """Test that _get_all_filepaths_from_view extracts filepaths in correct order."""
        manager, item_ids = library_manager

        # Set up filepath mapping
        expected_filepaths = [
            '/path/to/song1.mp3',
            '/path/to/song2.mp3',
            '/path/to/song3.mp3',
            '/path/to/song4.mp3',
        ]

        for item_id, filepath in zip(item_ids, expected_filepaths):
            manager._item_filepath_map[item_id] = filepath

        # Call the method
        result = manager._get_all_filepaths_from_view()

        # Verify order is preserved
        assert result == expected_filepaths
        assert len(result) == 4

    def test_get_all_filepaths_from_view_with_missing_items(self, library_manager):
        """Test that method handles missing items in filepath map gracefully."""
        manager, item_ids = library_manager

        # Set up filepath mapping with some missing entries
        manager._item_filepath_map = {
            'item1': '/path/to/song1.mp3',
            'item3': '/path/to/song3.mp3',
            # item2 and item4 are missing
        }

        # Call the method
        result = manager._get_all_filepaths_from_view()

        # Should only include items that are in the map
        assert result == ['/path/to/song1.mp3', '/path/to/song3.mp3']
        assert len(result) == 2

    def test_get_all_filepaths_from_view_empty(self, library_manager):
        """Test that method returns empty list when no items."""
        manager, _ = library_manager

        # Set queue to have no children
        manager.queue_view.queue.get_children.return_value = []
        manager._item_filepath_map = {}

        # Call the method
        result = manager._get_all_filepaths_from_view()

        # Should return empty list
        assert result == []

    def test_get_all_filepaths_from_view_preserves_order_with_gaps(self, library_manager):
        """Test that order is preserved even when there are gaps in the mapping."""
        manager, item_ids = library_manager

        # Create a custom order with gaps
        custom_items = ['item5', 'item1', 'item7', 'item3']
        manager.queue_view.queue.get_children.return_value = custom_items

        # Set up filepath mapping (some items not mapped)
        manager._item_filepath_map = {
            'item5': '/path/to/song5.mp3',
            'item1': '/path/to/song1.mp3',
            'item3': '/path/to/song3.mp3',
            # item7 is missing
        }

        # Call the method
        result = manager._get_all_filepaths_from_view()

        # Should maintain order from get_children, excluding item7
        expected = ['/path/to/song5.mp3', '/path/to/song1.mp3', '/path/to/song3.mp3']
        assert result == expected


class TestQueueHandlerGetAllFilepathsFromView:
    """Test _get_all_filepaths_from_view() in PlayerQueueHandler."""

    @pytest.fixture
    def queue_handler(self):
        """Create PlayerQueueHandler instance with mocked dependencies."""
        from core.player.queue import PlayerQueueHandler

        # Create mock dependencies
        queue_manager = Mock()
        player_core = Mock()

        # Create mock queue view
        queue_view = Mock()
        queue = Mock()
        item_ids = ['item1', 'item2', 'item3']
        queue.get_children.return_value = item_ids
        queue_view.queue = queue

        now_playing_view = Mock()
        progress_bar = Mock()
        favorites_manager = Mock()
        refresh_callback = Mock()

        # Create item_filepath_map
        item_filepath_map = {
            'item1': '/path/to/track1.mp3',
            'item2': '/path/to/track2.mp3',
            'item3': '/path/to/track3.mp3',
        }

        handler = PlayerQueueHandler(
            queue_manager=queue_manager,
            player_core=player_core,
            queue_view=queue_view,
            now_playing_view=now_playing_view,
            progress_bar=progress_bar,
            favorites_manager=favorites_manager,
            refresh_colors_callback=refresh_callback,
            item_filepath_map=item_filepath_map
        )

        return handler, item_ids

    def test_queue_handler_get_all_filepaths_from_view(self, queue_handler):
        """Test that queue handler's _get_all_filepaths_from_view works correctly."""
        handler, item_ids = queue_handler

        # Call the method
        result = handler._get_all_filepaths_from_view()

        # Verify correct filepaths in order
        expected = [
            '/path/to/track1.mp3',
            '/path/to/track2.mp3',
            '/path/to/track3.mp3',
        ]
        assert result == expected

    def test_queue_handler_get_all_filepaths_with_empty_map(self, queue_handler):
        """Test queue handler handles empty filepath map."""
        handler, _ = queue_handler

        # Clear the map
        handler._item_filepath_map = {}

        # Call the method
        result = handler._get_all_filepaths_from_view()

        # Should return empty list
        assert result == []
