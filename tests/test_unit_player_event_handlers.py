"""Unit tests for PlayerEventHandlers class.

Tests user interaction handlers including delete, drag-drop, search, and favorites.
"""

import pytest
from core.player.handlers import PlayerEventHandlers
from unittest.mock import MagicMock, Mock, call, patch


@pytest.fixture
def mock_window():
    """Mock Tkinter window."""
    return Mock()


@pytest.fixture
def mock_db():
    """Mock database."""
    return Mock()


@pytest.fixture
def mock_player_core():
    """Mock PlayerCore."""
    player = Mock()
    player.media_player = Mock()
    player.is_playing = False
    player._get_current_track_info = Mock(return_value={
        'title': 'Test Track',
        'artist': 'Test Artist',
        'album': 'Test Album'
    })
    return player


@pytest.fixture
def mock_library_view():
    """Mock library view."""
    view = Mock()
    view.library_tree = Mock()
    view.library_tree.selection = Mock(return_value=[])
    return view


@pytest.fixture
def mock_queue_view():
    """Mock queue view."""
    view = Mock()
    view.queue = Mock()
    view.queue.selection = Mock(return_value=[])
    view.queue.get_children = Mock(return_value=[])
    view.queue.item = Mock(return_value={'values': []})
    view.current_view = 'now_playing'
    return view


@pytest.fixture
def mock_now_playing_view():
    """Mock now playing view."""
    view = Mock()
    view.refresh_from_queue = Mock()
    view.update_lyrics = Mock()
    return view


@pytest.fixture
def mock_library_manager():
    """Mock library manager."""
    manager = Mock()
    manager.find_file_by_metadata = Mock(return_value=None)
    manager.delete_from_library = Mock(return_value=True)
    manager.add_files_to_library = Mock()
    manager.get_library_items = Mock(return_value=[])
    manager.search_library = Mock(return_value=[])
    manager.get_track_by_filepath = Mock(return_value=None)
    return manager


@pytest.fixture
def mock_queue_manager():
    """Mock queue manager."""
    manager = Mock()
    manager.remove_from_queue = Mock()
    manager.process_dropped_files = Mock()
    manager.queue_items = []
    manager.current_index = 0
    return manager


@pytest.fixture
def mock_favorites_manager():
    """Mock favorites manager."""
    manager = Mock()
    manager.is_favorite = Mock(return_value=False)
    manager.toggle_favorite = Mock(return_value=True)
    return manager


@pytest.fixture
def mock_progress_bar():
    """Mock progress bar."""
    bar = Mock()
    bar.controls = Mock()
    bar.controls.update_favorite_button = Mock()
    return bar


@pytest.fixture
def mock_status_bar():
    """Mock status bar."""
    bar = Mock()
    bar.update_statistics = Mock()
    return bar


@pytest.fixture
def mock_callbacks():
    """Mock callback functions."""
    return {
        'load_library': Mock(),
        'load_liked_songs': Mock(),
        'load_recently_played': Mock(),
        'refresh_colors': Mock(),
    }


@pytest.fixture
def mock_library_handler():
    """Mock library handler."""
    handler = Mock()
    handler._populate_queue_view = Mock()
    return handler


@pytest.fixture
def event_handlers(
    mock_window,
    mock_db,
    mock_player_core,
    mock_library_view,
    mock_queue_view,
    mock_now_playing_view,
    mock_library_manager,
    mock_queue_manager,
    mock_favorites_manager,
    mock_progress_bar,
    mock_status_bar,
    mock_callbacks,
    mock_library_handler,
):
    """Create PlayerEventHandlers instance with mocked dependencies."""
    handlers = PlayerEventHandlers(
        window=mock_window,
        db=mock_db,
        player_core=mock_player_core,
        library_view=mock_library_view,
        queue_view=mock_queue_view,
        now_playing_view=mock_now_playing_view,
        library_manager=mock_library_manager,
        queue_manager=mock_queue_manager,
        favorites_manager=mock_favorites_manager,
        progress_bar=mock_progress_bar,
        status_bar=mock_status_bar,
        load_library_callback=mock_callbacks['load_library'],
        load_liked_songs_callback=mock_callbacks['load_liked_songs'],
        load_recently_played_callback=mock_callbacks['load_recently_played'],
        refresh_colors_callback=mock_callbacks['refresh_colors'],
        _item_filepath_map={},
        library_handler=mock_library_handler,
    )
    # Add attributes needed by methods
    handlers.load_library = mock_callbacks['load_library']
    handlers.load_liked_songs = mock_callbacks['load_liked_songs']
    handlers.refresh_colors = mock_callbacks['refresh_colors']
    handlers.active_view = 'now_playing'
    handlers.search_bar = Mock()
    handlers.search_bar.search_var = Mock()
    handlers.search_bar.search_var.set = Mock()
    return handlers


class TestHandleDelete:
    """Tests for handle_delete() method."""

    def test_handle_delete_no_selection(self, event_handlers, mock_queue_view):
        """Should return early if no items are selected."""
        mock_queue_view.queue.selection.return_value = []
        event = Mock()

        event_handlers.handle_delete(event)

        # Should not call any deletion methods
        assert not mock_queue_view.queue.delete.called

    def test_handle_delete_from_queue(self, event_handlers, mock_queue_view, mock_queue_manager):
        """Should delete from queue when in now_playing view."""
        # Setup selection
        item_id = 'item1'
        mock_queue_view.queue.selection.return_value = [item_id]
        mock_queue_view.queue.item.return_value = {
            'values': [1, 'Test Song', 'Test Artist', 'Test Album', '2024']
        }
        mock_queue_view.queue.get_children.return_value = [item_id, 'item2']
        mock_queue_view.current_view = 'now_playing'

        event = Mock()
        result = event_handlers.handle_delete(event)

        # Should remove from queue
        mock_queue_manager.remove_from_queue.assert_called_once_with(
            'Test Song', 'Test Artist', 'Test Album', 1
        )
        # Should delete from UI
        mock_queue_view.queue.delete.assert_called_once_with(item_id)
        # Should return "break"
        assert result == "break"

    def test_handle_delete_from_library(self, event_handlers, mock_queue_view, mock_library_manager, mock_queue_manager, mock_status_bar):
        """Should delete from library when in library view."""
        # Setup selection
        item_id = 'item1'
        mock_queue_view.queue.selection.return_value = [item_id]
        mock_queue_view.queue.item.return_value = {
            'values': [1, 'Test Song', 'Test Artist', 'Test Album', '2024']
        }
        mock_queue_view.current_view = 'music'
        mock_library_manager.find_file_by_metadata.return_value = '/path/to/file.mp3'
        mock_library_manager.delete_from_library.return_value = True

        event = Mock()
        result = event_handlers.handle_delete(event)

        # Should delete from library
        mock_library_manager.delete_from_library.assert_called_once_with('/path/to/file.mp3')
        # Should also remove from queue
        mock_queue_manager.remove_from_queue.assert_called_once()
        # Should update statistics
        mock_status_bar.update_statistics.assert_called_once()
        # Should delete from UI
        mock_queue_view.queue.delete.assert_called_once_with(item_id)
        assert result == "break"

    def test_handle_delete_multiple_items(self, event_handlers, mock_queue_view, mock_queue_manager):
        """Should handle deletion of multiple selected items."""
        # Setup multiple selections
        item_ids = ['item1', 'item2', 'item3']
        mock_queue_view.queue.selection.return_value = item_ids
        mock_queue_view.queue.item.side_effect = [
            {'values': [1, 'Song 1', 'Artist 1', 'Album 1', '2024']},
            {'values': [2, 'Song 2', 'Artist 2', 'Album 2', '2023']},
            {'values': [3, 'Song 3', 'Artist 3', 'Album 3', '2022']},
        ]
        mock_queue_view.current_view = 'now_playing'

        event = Mock()
        event_handlers.handle_delete(event)

        # Should delete all 3 items
        assert mock_queue_manager.remove_from_queue.call_count == 3
        assert mock_queue_view.queue.delete.call_count == 3

    def test_handle_delete_missing_filepath(self, event_handlers, mock_queue_view, mock_library_manager):
        """Should handle case where file path cannot be found."""
        item_id = 'item1'
        mock_queue_view.queue.selection.return_value = [item_id]
        mock_queue_view.queue.item.return_value = {
            'values': [1, 'Test Song', 'Test Artist', 'Test Album', '2024']
        }
        mock_queue_view.current_view = 'music'
        mock_library_manager.find_file_by_metadata.return_value = None

        event = Mock()
        result = event_handlers.handle_delete(event)

        # Should not attempt to delete from library
        assert not mock_library_manager.delete_from_library.called
        # Should still delete from UI
        mock_queue_view.queue.delete.assert_called_once_with(item_id)
        assert result == "break"


class TestHandleDrop:
    """Tests for handle_drop() drag-and-drop functionality."""

    @patch('os.path.exists')
    def test_handle_drop_macos_format(self, mock_exists, event_handlers, mock_library_view, mock_library_manager):
        """Should parse macOS drag-drop format correctly."""
        mock_exists.return_value = True
        mock_library_view.library_tree.selection.return_value = ['music_section']
        mock_library_view.library_tree.item.return_value = {'tags': ['music']}

        event = Mock()
        event.data = '{/path/to/file1.mp3} {/path/to/file2.mp3}'

        event_handlers.handle_drop(event)

        # Should add files to library
        mock_library_manager.add_files_to_library.assert_called_once()
        call_args = mock_library_manager.add_files_to_library.call_args[0][0]
        assert len(call_args) == 2
        assert '/path/to/file1.mp3' in call_args
        assert '/path/to/file2.mp3' in call_args

    @patch('os.path.exists')
    def test_handle_drop_to_music_section(self, mock_exists, event_handlers, mock_library_view, mock_library_manager, mock_status_bar, mock_callbacks):
        """Should add files to library when dropped on music section."""
        mock_exists.return_value = True
        mock_library_view.library_tree.selection.return_value = ['music_section']
        mock_library_view.library_tree.item.return_value = {'tags': ['music']}

        event = Mock()
        event.data = '{/path/to/file.mp3}'

        event_handlers.handle_drop(event)

        # Should add to library
        mock_library_manager.add_files_to_library.assert_called_once_with(['/path/to/file.mp3'])
        # Should update statistics
        mock_status_bar.update_statistics.assert_called_once()
        # Should reload library
        mock_callbacks['load_library'].assert_called_once()

    @patch('os.path.exists')
    def test_handle_drop_to_now_playing(self, mock_exists, event_handlers, mock_library_view, mock_library_manager, mock_queue_manager, mock_status_bar):
        """Should add to queue when dropped on now_playing section."""
        mock_exists.return_value = True
        event_handlers.active_view = 'now_playing'
        mock_library_view.library_tree.selection.return_value = ['queue_section']
        mock_library_view.library_tree.item.return_value = {'tags': ['now_playing']}

        event = Mock()
        event.data = '{/path/to/file.mp3}'

        event_handlers.handle_drop(event)

        # Should add to library and queue
        mock_library_manager.add_files_to_library.assert_called_once_with(['/path/to/file.mp3'])
        mock_queue_manager.process_dropped_files.assert_called_once_with(['/path/to/file.mp3'])
        mock_status_bar.update_statistics.assert_called_once()

    @patch('os.path.exists')
    def test_handle_drop_no_selection(self, mock_exists, event_handlers, mock_library_view, mock_library_manager):
        """Should not process files if no section is selected."""
        mock_exists.return_value = True
        mock_library_view.library_tree.selection.return_value = []

        event = Mock()
        event.data = '{/path/to/file.mp3}'

        event_handlers.handle_drop(event)

        # Should not add files
        assert not mock_library_manager.add_files_to_library.called

    @patch('os.path.exists')
    def test_handle_drop_invalid_files(self, mock_exists, event_handlers, mock_library_view, mock_library_manager):
        """Should filter out non-existent files."""
        mock_exists.side_effect = [True, False, True]  # First and third exist, second doesn't
        mock_library_view.library_tree.selection.return_value = ['music_section']
        mock_library_view.library_tree.item.return_value = {'tags': ['music']}

        event = Mock()
        event.data = '{/path/to/file1.mp3} {/path/to/nonexistent.mp3} {/path/to/file3.mp3}'

        event_handlers.handle_drop(event)

        # Should only add existing files
        mock_library_manager.add_files_to_library.assert_called_once()
        call_args = mock_library_manager.add_files_to_library.call_args[0][0]
        assert len(call_args) == 2
        assert '/path/to/file1.mp3' in call_args
        assert '/path/to/file3.mp3' in call_args
        assert '/path/to/nonexistent.mp3' not in call_args

    @patch('os.path.exists')
    def test_handle_drop_with_quotes(self, mock_exists, event_handlers, mock_library_view, mock_library_manager):
        """Should handle paths with quotes correctly."""
        mock_exists.return_value = True
        mock_library_view.library_tree.selection.return_value = ['music_section']
        mock_library_view.library_tree.item.return_value = {'tags': ['music']}

        event = Mock()
        event.data = '{"/path/to/file with spaces.mp3"}'

        event_handlers.handle_drop(event)

        # Should strip quotes
        call_args = mock_library_manager.add_files_to_library.call_args[0][0]
        assert call_args[0] == '/path/to/file with spaces.mp3'

    @patch('os.path.exists')
    def test_handle_drop_empty_data(self, mock_exists, event_handlers, mock_library_view, mock_library_manager):
        """Should handle empty drop data gracefully."""
        mock_library_view.library_tree.selection.return_value = ['music_section']
        mock_library_view.library_tree.item.return_value = {'tags': ['music']}

        event = Mock()
        event.data = ''

        event_handlers.handle_drop(event)

        # Should call add_files with empty list (doesn't filter empty before calling)
        mock_library_manager.add_files_to_library.assert_called_once_with([])


class TestToggleFavorite:
    """Tests for toggle_favorite() method."""

    @patch('os.path.exists')
    @patch('urllib.parse.unquote')
    def test_toggle_favorite_success(self, mock_unquote, mock_exists, event_handlers, mock_player_core, mock_favorites_manager, mock_progress_bar):
        """Should toggle favorite status for currently playing track."""
        # Setup
        mock_media = Mock()
        mock_media.get_mrl.return_value = 'file:///path/to/track.mp3'
        mock_player_core.media_player.get_media.return_value = mock_media
        mock_player_core.media_player.get_state.return_value = 3  # Playing state
        mock_player_core.is_playing = True
        mock_unquote.return_value = '/path/to/track.mp3'
        mock_exists.return_value = True
        mock_favorites_manager.is_favorite.return_value = False
        mock_favorites_manager.toggle_favorite.return_value = True

        event_handlers.toggle_favorite()

        # Should toggle favorite
        mock_favorites_manager.toggle_favorite.assert_called_once_with('/path/to/track.mp3')
        # Should update UI
        mock_progress_bar.controls.update_favorite_button.assert_called_once_with(True)

    def test_toggle_favorite_no_media_loaded(self, event_handlers, mock_player_core, mock_favorites_manager):
        """Should not toggle if no media is loaded."""
        mock_player_core.media_player.get_media.return_value = None

        event_handlers.toggle_favorite()

        # Should not toggle
        assert not mock_favorites_manager.toggle_favorite.called

    def test_toggle_favorite_not_playing(self, event_handlers, mock_player_core, mock_favorites_manager):
        """Should not toggle if track is not playing or paused."""
        mock_media = Mock()
        mock_player_core.media_player.get_media.return_value = mock_media
        mock_player_core.is_playing = False
        mock_player_core.media_player.get_state.return_value = 0  # NothingSpecial state

        event_handlers.toggle_favorite()

        # Should not toggle
        assert not mock_favorites_manager.toggle_favorite.called

    @patch('os.path.exists')
    @patch('urllib.parse.unquote')
    def test_toggle_favorite_paused_state(self, mock_unquote, mock_exists, event_handlers, mock_player_core, mock_favorites_manager):
        """Should allow toggling when track is paused."""
        mock_media = Mock()
        mock_media.get_mrl.return_value = 'file:///path/to/track.mp3'
        mock_player_core.media_player.get_media.return_value = mock_media
        mock_player_core.media_player.get_state.return_value = 4  # Paused state
        mock_player_core.is_playing = False
        mock_unquote.return_value = '/path/to/track.mp3'
        mock_exists.return_value = True

        event_handlers.toggle_favorite()

        # Should toggle favorite
        assert mock_favorites_manager.toggle_favorite.called

    @patch('os.path.exists')
    @patch('urllib.parse.unquote')
    def test_toggle_favorite_invalid_filepath(self, mock_unquote, mock_exists, event_handlers, mock_player_core, mock_favorites_manager):
        """Should not toggle if filepath doesn't exist."""
        mock_media = Mock()
        mock_media.get_mrl.return_value = 'file:///nonexistent/track.mp3'
        mock_player_core.media_player.get_media.return_value = mock_media
        mock_player_core.media_player.get_state.return_value = 3
        mock_player_core.is_playing = True
        mock_unquote.return_value = '/nonexistent/track.mp3'
        mock_exists.return_value = False

        event_handlers.toggle_favorite()

        # Should not toggle
        assert not mock_favorites_manager.toggle_favorite.called


class TestOnTrackChange:
    """Tests for on_track_change() callback."""

    def test_on_track_change_refreshes_view(self, event_handlers, mock_now_playing_view):
        """Should refresh Now Playing view when track changes."""
        event_handlers.on_track_change()

        # Should refresh view
        mock_now_playing_view.refresh_from_queue.assert_called_once()

    def test_on_track_change_updates_lyrics(self, event_handlers, mock_queue_manager, mock_library_manager, mock_now_playing_view):
        """Should update lyrics for new track."""
        # Setup
        mock_queue_manager.queue_items = ['/path/to/track.mp3']
        mock_queue_manager.current_index = 0
        mock_library_manager.get_track_by_filepath.return_value = {
            'artist': 'Test Artist',
            'title': 'Test Title',
            'album': 'Test Album'
        }

        event_handlers.on_track_change()

        # Should update lyrics
        mock_now_playing_view.update_lyrics.assert_called_once_with('Test Artist', 'Test Title', 'Test Album')

    def test_on_track_change_no_track_info(self, event_handlers, mock_queue_manager, mock_library_manager, mock_now_playing_view):
        """Should handle case where track info is not found."""
        mock_queue_manager.queue_items = ['/path/to/track.mp3']
        mock_queue_manager.current_index = 0
        mock_library_manager.get_track_by_filepath.return_value = None

        event_handlers.on_track_change()

        # Should refresh view but not update lyrics
        mock_now_playing_view.refresh_from_queue.assert_called_once()
        assert not mock_now_playing_view.update_lyrics.called

    def test_on_track_change_empty_queue(self, event_handlers, mock_queue_manager, mock_now_playing_view):
        """Should handle empty queue gracefully."""
        mock_queue_manager.queue_items = []

        event_handlers.on_track_change()

        # Should still refresh view
        mock_now_playing_view.refresh_from_queue.assert_called_once()


class TestSearchMethods:
    """Tests for perform_search() and clear_search() methods."""

    def test_perform_search_in_library(self, event_handlers, mock_library_view, mock_library_manager, mock_library_handler):
        """Should search library when in music view."""
        # Setup
        mock_library_view.library_tree.selection.return_value = ['music_section']
        mock_library_view.library_tree.item.return_value = {'tags': ['music']}
        mock_library_manager.search_library.return_value = [
            ('Artist 1', 'Album 1', 'Track 1', 1, '2024', '/path1.mp3'),
            ('Artist 2', 'Album 2', 'Track 2', 2, '2023', '/path2.mp3'),
        ]

        event_handlers.perform_search('test query')

        # Should search library
        mock_library_manager.search_library.assert_called_once_with('test query')
        # Should populate queue view with results
        mock_library_handler._populate_queue_view.assert_called_once()

    def test_perform_search_empty_query(self, event_handlers, mock_library_view, mock_library_manager):
        """Should show all items when search query is empty."""
        mock_library_view.library_tree.selection.return_value = ['music_section']
        mock_library_view.library_tree.item.return_value = {'tags': ['music']}

        event_handlers.perform_search('')

        # Should get all library items
        mock_library_manager.get_library_items.assert_called_once()

    def test_perform_search_now_playing_view(self, event_handlers, mock_library_view, mock_library_manager):
        """Should not search in Now Playing view."""
        mock_library_view.library_tree.selection.return_value = ['queue_section']
        mock_library_view.library_tree.item.return_value = {'tags': ['now_playing']}

        event_handlers.perform_search('test query')

        # Should not search
        assert not mock_library_manager.search_library.called

    def test_perform_search_no_selection(self, event_handlers, mock_library_view, mock_library_manager):
        """Should return early if no section is selected."""
        mock_library_view.library_tree.selection.return_value = []

        event_handlers.perform_search('test query')

        # Should not search
        assert not mock_library_manager.search_library.called

    def test_clear_search_in_library(self, event_handlers, mock_library_view, mock_callbacks):
        """Should clear search and reload library view."""
        mock_library_view.library_tree.selection.return_value = ['music_section']
        mock_library_view.library_tree.item.return_value = {'tags': ['music']}

        event_handlers.clear_search()

        # Should clear search bar
        event_handlers.search_bar.search_var.set.assert_called_once_with("")
        # Should reload library
        mock_callbacks['load_library'].assert_called_once()

    def test_clear_search_in_now_playing(self, event_handlers, mock_library_view, mock_now_playing_view):
        """Should refresh Now Playing view when clearing search there."""
        event_handlers.active_view = 'now_playing'
        mock_library_view.library_tree.selection.return_value = ['queue_section']
        mock_library_view.library_tree.item.return_value = {'tags': ['now_playing']}

        event_handlers.clear_search()

        # Should refresh Now Playing view
        mock_now_playing_view.refresh_from_queue.assert_called_once()


class TestOnFavoritesChanged:
    """Tests for on_favorites_changed() callback."""

    def test_on_favorites_changed_liked_songs_view(self, event_handlers, mock_library_view, mock_callbacks):
        """Should refresh liked songs view when favorites change."""
        mock_library_view.library_tree.selection.return_value = ['liked_section']
        mock_library_view.library_tree.item.return_value = {'tags': ['liked_songs']}

        event_handlers.on_favorites_changed()

        # Should reload liked songs
        mock_callbacks['load_liked_songs'].assert_called_once()

    def test_on_favorites_changed_other_view(self, event_handlers, mock_library_view, mock_callbacks):
        """Should not refresh if not in liked songs view."""
        mock_library_view.library_tree.selection.return_value = ['music_section']
        mock_library_view.library_tree.item.return_value = {'tags': ['music']}

        event_handlers.on_favorites_changed()

        # Should not reload
        assert not mock_callbacks['load_liked_songs'].called

    def test_on_favorites_changed_no_selection(self, event_handlers, mock_library_view, mock_callbacks):
        """Should return early if no section is selected."""
        mock_library_view.library_tree.selection.return_value = []

        event_handlers.on_favorites_changed()

        # Should not reload
        assert not mock_callbacks['load_liked_songs'].called


class TestToggleStopAfterCurrent:
    """Tests for toggle_stop_after_current() method."""

    def test_toggle_stop_after_current(self, event_handlers, mock_player_core):
        """Should delegate to player_core."""
        event_handlers.toggle_stop_after_current()

        # Should call player_core method
        mock_player_core.toggle_stop_after_current.assert_called_once()

    def test_toggle_stop_after_current_no_player_core(self, event_handlers):
        """Should handle missing player_core gracefully."""
        event_handlers.player_core = None

        # Should not crash
        event_handlers.toggle_stop_after_current()
