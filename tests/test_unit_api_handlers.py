"""Unit tests for API server command handlers.

These tests directly test the handler methods without the threading complexity
of _execute_command, providing good coverage of the API server logic.
"""

import pytest
from api import APIServer
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_player():
    """Create a mock MusicPlayer with all required attributes."""
    player = MagicMock()
    player.player_core.is_playing = False
    player.player_core.loop_enabled = False
    player.player_core.shuffle_enabled = False
    player.player_core.get_volume.return_value = 80
    player.player_core.get_current_time.return_value = 30000  # milliseconds
    player.player_core.get_duration.return_value = 180000  # milliseconds
    player.player_core._get_current_track_info.return_value = None
    player.queue_manager.get_queue_count.return_value = 0
    player.queue_manager.get_queue_items.return_value = []
    player.queue_manager.get_current_track.return_value = None
    player.queue_manager.is_shuffle_enabled.return_value = False
    player._current_view = 'queue'
    return player


@pytest.fixture
def api_server(mock_player):
    """Create an APIServer instance with mock player."""
    return APIServer(mock_player, port=5555)


class TestPlaybackHandlers:
    """Test playback control handlers."""

    def test_handle_play_pause(self, api_server, mock_player):
        """Test play_pause handler."""
        result = api_server._handle_play_pause({})
        assert result['status'] == 'success'
        mock_player.play_pause.assert_called_once()

    def test_handle_play(self, api_server, mock_player):
        """Test play handler."""
        mock_player.player_core.is_playing = False
        result = api_server._handle_play({})
        assert result['status'] == 'success'
        assert result['is_playing'] is True

    def test_handle_pause(self, api_server, mock_player):
        """Test pause handler."""
        mock_player.player_core.is_playing = True
        result = api_server._handle_pause({})
        assert result['status'] == 'success'
        assert result['is_playing'] is False

    def test_handle_stop(self, api_server, mock_player):
        """Test stop handler."""
        result = api_server._handle_stop({})
        assert result['status'] == 'success'
        mock_player.player_core.stop.assert_called_once()

    def test_handle_next(self, api_server, mock_player):
        """Test next handler."""
        result = api_server._handle_next({})
        assert result['status'] == 'success'
        mock_player.player_core.next_song.assert_called_once()

    def test_handle_previous(self, api_server, mock_player):
        """Test previous handler."""
        result = api_server._handle_previous({})
        assert result['status'] == 'success'
        mock_player.player_core.previous_song.assert_called_once()


class TestTrackSelectionHandlers:
    """Test track selection handlers."""

    def test_select_track_no_filepath(self, api_server):
        """Test select_track without filepath."""
        result = api_server._handle_select_track({})
        assert result['status'] == 'error'
        assert 'filepath' in result['message'].lower()

    def test_select_track_with_filepath(self, api_server, mock_player):
        """Test select_track with valid filepath."""
        result = api_server._handle_select_track({'filepath': '/path/to/track.mp3'})
        assert result['status'] == 'success'

    def test_play_track_at_index_no_index(self, api_server):
        """Test play_track_at_index without index."""
        result = api_server._handle_play_track_at_index({})
        assert result['status'] == 'error'
        assert 'index' in result['message'].lower()

    def test_play_track_at_index_invalid(self, api_server, mock_player):
        """Test play_track_at_index with invalid index."""
        mock_player.queue_manager.get_queue_items.return_value = [{'filepath': '/track1.mp3'}]
        result = api_server._handle_play_track_at_index({'index': 10})
        assert result['status'] == 'error'
        assert 'out of range' in result['message'].lower()

    def test_play_track_at_index_valid(self, api_server, mock_player):
        """Test play_track_at_index with valid index."""
        mock_player.queue_manager.get_queue_items.return_value = [
            ('track1.mp3', 'Artist 1', 'Title 1', 'Album 1', 1, '2024'),
            ('track2.mp3', 'Artist 2', 'Title 2', 'Album 2', 2, '2024'),
        ]
        result = api_server._handle_play_track_at_index({'index': 1})
        assert result['status'] == 'success'


class TestQueueHandlers:
    """Test queue management handlers."""

    def test_add_to_queue_no_files(self, api_server):
        """Test add_to_queue without files."""
        result = api_server._handle_add_to_queue({})
        assert result['status'] == 'error'
        assert 'files' in result['message'].lower()

    def test_add_to_queue_with_files(self, api_server, mock_player):
        """Test add_to_queue with valid files."""
        result = api_server._handle_add_to_queue({'files': ['/track1.mp3', '/track2.mp3']})
        assert result['status'] == 'success'
        assert result['added'] == 2

    def test_clear_queue(self, api_server, mock_player):
        """Test clear_queue handler."""
        result = api_server._handle_clear_queue({})
        assert result['status'] == 'success'
        mock_player.queue_manager.clear_queue.assert_called_once()

    def test_remove_from_queue_no_index(self, api_server):
        """Test remove_from_queue without index."""
        result = api_server._handle_remove_from_queue({})
        assert result['status'] == 'error'
        assert 'index' in result['message'].lower()

    def test_remove_from_queue_with_index(self, api_server, mock_player):
        """Test remove_from_queue with valid index."""
        # Mock get_queue_items to return tuple format
        mock_player.queue_manager.get_queue_items.return_value = [
            ('/track1.mp3', 'Artist 1', 'Title 1', 'Album 1', 1, '2024'),
            ('/track2.mp3', 'Artist 2', 'Title 2', 'Album 2', 2, '2024'),
            ('/track3.mp3', 'Artist 3', 'Title 3', 'Album 3', 3, '2024'),
        ]
        mock_player.active_view = 'queue'  # Not 'now_playing' to avoid refresh call
        result = api_server._handle_remove_from_queue({'index': 2})
        assert result['status'] == 'success'
        # Verify remove_from_queue was called with metadata (not index)
        mock_player.queue_manager.remove_from_queue.assert_called_once_with('Title 3', 'Artist 3', 'Album 3', 3)


class TestViewHandlers:
    """Test view/navigation handlers."""

    def test_switch_view_no_view(self, api_server):
        """Test switch_view without view parameter."""
        result = api_server._handle_switch_view({})
        assert result['status'] == 'error'
        assert 'view' in result['message'].lower()

    def test_switch_view_with_view(self, api_server, mock_player):
        """Test switch_view with valid view."""
        result = api_server._handle_switch_view({'view': 'library'})
        assert result['status'] == 'success'

    def test_select_library_item_no_index(self, api_server):
        """Test select_library_item without index."""
        result = api_server._handle_select_library_item({})
        assert result['status'] == 'error'
        assert 'index' in result['message'].lower()

    def test_select_library_item_with_index(self, api_server, mock_player):
        """Test select_library_item with valid index."""
        # Mock the queue_view.queue widget with children
        mock_player.queue_view.queue.get_children.return_value = ['item0', 'item1', 'item2', 'item3', 'item4', 'item5']
        result = api_server._handle_select_library_item({'index': 5})
        assert result['status'] == 'success'
        mock_player.queue_view.queue.selection_set.assert_called_once_with('item5')
        mock_player.queue_view.queue.focus.assert_called_once_with('item5')

    def test_select_queue_item_no_index(self, api_server):
        """Test select_queue_item without index."""
        result = api_server._handle_select_queue_item({})
        assert result['status'] == 'error'
        assert 'index' in result['message'].lower()

    def test_select_queue_item_invalid(self, api_server, mock_player):
        """Test select_queue_item with invalid index."""
        mock_player.queue_manager.get_queue_items.return_value = []
        result = api_server._handle_select_queue_item({'index': 10})
        assert result['status'] == 'error'

    def test_select_queue_item_valid(self, api_server, mock_player):
        """Test select_queue_item with valid index."""
        mock_player.queue_manager.get_queue_items.return_value = [
            ('track1.mp3', 'Artist 1', 'Title 1', 'Album 1', 1, '2024'),
            ('track2.mp3', 'Artist 2', 'Title 2', 'Album 2', 2, '2024'),
        ]
        # Mock the UI queue widget with matching children
        mock_player.queue_view.queue.get_children.return_value = ['item0', 'item1']
        mock_player.active_view = 'queue'  # Not 'now_playing' to avoid refresh call
        result = api_server._handle_select_queue_item({'index': 1})
        assert result['status'] == 'success'
        mock_player.queue_view.queue.selection_set.assert_called_once_with('item1')
        mock_player.queue_view.queue.focus.assert_called_once_with('item1')


class TestVolumeSeekHandlers:
    """Test volume and seek handlers."""

    def test_set_volume_no_parameter(self, api_server):
        """Test set_volume without volume parameter."""
        result = api_server._handle_set_volume({})
        assert result['status'] == 'error'
        assert 'volume' in result['message'].lower()

    def test_set_volume_invalid_type(self, api_server):
        """Test set_volume with invalid type."""
        result = api_server._handle_set_volume({'volume': 'loud'})
        assert result['status'] == 'error'
        assert 'invalid' in result['message'].lower()

    def test_set_volume_out_of_range_low(self, api_server):
        """Test set_volume below 0."""
        result = api_server._handle_set_volume({'volume': -10})
        assert result['status'] == 'error'
        assert 'between 0 and 100' in result['message'].lower()

    def test_set_volume_out_of_range_high(self, api_server):
        """Test set_volume above 100."""
        result = api_server._handle_set_volume({'volume': 150})
        assert result['status'] == 'error'
        assert 'between 0 and 100' in result['message'].lower()

    def test_set_volume_valid(self, api_server, mock_player):
        """Test set_volume with valid volume."""
        result = api_server._handle_set_volume({'volume': 75})
        assert result['status'] == 'success'
        mock_player.player_core.set_volume.assert_called_once_with(75)

    def test_seek_relative(self, api_server, mock_player):
        """Test relative seek."""
        mock_player.player_core.get_current_time.return_value = 30000  # 30 seconds in ms
        mock_player.player_core.seek_to_time.return_value = True
        result = api_server._handle_seek({'offset': 10})
        assert result['status'] == 'success'
        mock_player.player_core.seek_to_time.assert_called()

    def test_seek_to_position_no_position(self, api_server):
        """Test seek_to_position without position."""
        result = api_server._handle_seek_to_position({})
        assert result['status'] == 'error'
        assert 'position' in result['message'].lower()

    def test_seek_to_position_valid(self, api_server, mock_player):
        """Test seek_to_position with valid position."""
        mock_player.player_core.seek_to_time.return_value = True
        result = api_server._handle_seek_to_position({'position': 120})
        assert result['status'] == 'success'


class TestToggleHandlers:
    """Test toggle handlers."""

    def test_toggle_loop(self, api_server, mock_player):
        """Test toggle_loop handler."""
        mock_player.player_core.loop_enabled = False
        result = api_server._handle_toggle_loop({})
        assert result['status'] == 'success'
        mock_player.player_core.toggle_loop.assert_called_once()

    def test_toggle_shuffle(self, api_server, mock_player):
        """Test toggle_shuffle handler."""
        mock_player.player_core.shuffle_enabled = False
        result = api_server._handle_toggle_shuffle({})
        assert result['status'] == 'success'
        mock_player.player_core.toggle_shuffle.assert_called_once()

    def test_toggle_favorite(self, api_server, mock_player):
        """Test toggle_favorite handler."""
        result = api_server._handle_toggle_favorite({})
        assert result['status'] == 'success'
        mock_player.toggle_favorite.assert_called_once()


class TestMediaKeyHandlers:
    """Test media key handlers."""

    def test_media_key_no_key(self, api_server):
        """Test media_key without key parameter."""
        result = api_server._handle_media_key({})
        assert result['status'] == 'error'
        assert 'key' in result['message'].lower()

    def test_media_key_invalid(self, api_server):
        """Test media_key with invalid key."""
        result = api_server._handle_media_key({'key': 'invalid'})
        assert result['status'] == 'error'
        assert 'invalid' in result['message'].lower()

    def test_media_key_play_pause(self, api_server, mock_player):
        """Test media_key play_pause."""
        result = api_server._handle_media_key({'key': 'play_pause'})
        assert result['status'] == 'success'
        mock_player.play_pause.assert_called_once()

    def test_media_key_next(self, api_server, mock_player):
        """Test media_key next."""
        result = api_server._handle_media_key({'key': 'next'})
        assert result['status'] == 'success'
        mock_player.player_core.next_song.assert_called_once()

    def test_media_key_previous(self, api_server, mock_player):
        """Test media_key previous."""
        result = api_server._handle_media_key({'key': 'previous'})
        assert result['status'] == 'success'
        mock_player.player_core.previous_song.assert_called_once()


class TestSearchHandlers:
    """Test search handlers."""

    def test_search_with_query(self, api_server, mock_player):
        """Test search with query."""
        mock_player.search_bar.search_var = MagicMock()
        result = api_server._handle_search({'query': 'test'})
        assert result['status'] == 'success'
        assert result['query'] == 'test'

    def test_search_empty_query(self, api_server, mock_player):
        """Test search with empty query."""
        mock_player.search_bar.search_var = MagicMock()
        result = api_server._handle_search({})
        assert result['status'] == 'success'
        assert result['query'] == ''

    def test_clear_search(self, api_server, mock_player):
        """Test clear_search handler."""
        result = api_server._handle_clear_search({})
        assert result['status'] == 'success'
        mock_player.clear_search.assert_called_once()


class TestInfoHandlers:
    """Test information query handlers."""

    def test_get_status(self, api_server, mock_player):
        """Test get_status handler."""
        mock_player.player_core.is_playing = True
        mock_player.player_core.loop_enabled = True
        mock_player.player_core.shuffle_enabled = True
        result = api_server._handle_get_status({})
        assert result['status'] == 'success'
        assert 'data' in result
        assert result['data']['is_playing'] is True
        assert result['data']['loop_enabled'] is True
        assert result['data']['shuffle_enabled'] is True

    def test_get_current_track_none(self, api_server, mock_player):
        """Test get_current_track when no track playing."""
        mock_player.player_core._get_current_track_info.return_value = None
        result = api_server._handle_get_current_track({})
        assert result['status'] == 'success'
        assert result['data'] is None

    def test_get_current_track_with_track(self, api_server, mock_player):
        """Test get_current_track with track playing."""
        mock_player.player_core._get_current_track_info.return_value = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'track': 'Test Song',
        }
        mock_player.player_core.current_file = '/path/to/track.mp3'
        result = api_server._handle_get_current_track({})
        assert result['status'] == 'success'
        assert result['data'] is not None
        assert result['data']['title'] == 'Test Song'

    def test_get_queue(self, api_server, mock_player):
        """Test get_queue handler."""
        mock_player.queue_manager.get_queue_items.return_value = [
            ('track1.mp3', 'Artist 1', 'Title 1', 'Album 1', 1, '2024'),
            ('track2.mp3', 'Artist 2', 'Title 2', 'Album 2', 2, '2024'),
        ]
        result = api_server._handle_get_queue({})
        assert result['status'] == 'success'
        assert result['count'] == 2
        assert len(result['data']) == 2

    def test_get_library(self, api_server, mock_player):
        """Test get_library handler."""
        # Mock the queue_view widget - get_children returns list of item IDs
        mock_player.queue_view.queue.get_children.return_value = ['item1', 'item2']
        # Mock item() method to return dict with 'values' key containing tuple
        def mock_item(item_id, key):
            if key == 'values':
                if item_id == 'item1':
                    return ('1', 'Title 1', 'Artist 1', 'Album 1')
                elif item_id == 'item2':
                    return ('2', 'Title 2', 'Artist 2', 'Album 2')
            return ()
        mock_player.queue_view.queue.item = mock_item

        result = api_server._handle_get_library({})
        assert result['status'] == 'success'
        assert result['count'] == 2
        assert len(result['data']) == 2
        assert result['total'] == 2


class TestCommandExecution:
    """Test command execution routing."""

    def test_execute_missing_action(self, api_server):
        """Test execute with missing action."""
        result = api_server._execute_command({})
        assert result['status'] == 'error'
        assert 'no action' in result['message'].lower()

    def test_execute_unknown_action(self, api_server):
        """Test execute with unknown action."""
        result = api_server._execute_command({'action': 'nonexistent'})
        assert result['status'] == 'error'
        assert 'unknown' in result['message'].lower()
