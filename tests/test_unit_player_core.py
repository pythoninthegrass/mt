"""Unit tests for PlayerCore using mocked VLC.

These tests use mocked VLC to avoid timing issues and external dependencies.
They run fast (<1s total) and test core logic deterministically.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.mocks import MockEventType, MockInstance, MockMediaPlayer


@pytest.fixture
def mock_vlc():
    """Mock the VLC module at import time."""
    mock_vlc_module = Mock()
    mock_vlc_module.Instance = MockInstance
    mock_vlc_module.EventType = MockEventType
    return mock_vlc_module


@pytest.fixture
def mock_db():
    """Mock MusicDatabase."""
    db = Mock()
    db.get_loop_enabled.return_value = False
    return db


@pytest.fixture
def mock_queue_manager():
    """Mock QueueManager."""
    manager = Mock()
    manager.is_shuffle_enabled.return_value = False
    manager.get_current_track.return_value = None
    manager.get_next_track.return_value = None
    manager.get_previous_track.return_value = None
    return manager


@pytest.fixture
def mock_queue_view():
    """Mock QueueView."""
    view = Mock()
    # Make selection() return a list-like object
    view.selection.return_value = []
    # Make get_children() return a list
    view.get_children.return_value = []
    return view


@pytest.fixture
def player_core(mock_vlc, mock_db, mock_queue_manager, mock_queue_view):
    """Create PlayerCore with mocked dependencies."""
    # Import PlayerCore directly - it will use the real VLC module
    # but we'll mock the specific methods we need to test
    from core.controls import PlayerCore

    player = PlayerCore(mock_db, mock_queue_manager, mock_queue_view)

    # Replace the media_player with our mock for deterministic testing
    player.media_player = MockMediaPlayer()
    player.player = mock_vlc.Instance()

    return player


class TestPlayerCoreInitialization:
    """Test PlayerCore initialization."""

    def test_initialization(self, player_core, mock_db, mock_queue_manager):
        """Test that PlayerCore initializes with correct default values."""
        assert player_core.db == mock_db
        assert player_core.queue_manager == mock_queue_manager
        assert player_core.is_playing is False
        assert player_core.current_time == 0
        assert player_core.was_playing is False
        assert player_core.current_file is None

    def test_vlc_player_created(self, player_core):
        """Test that VLC media player is created."""
        assert player_core.player is not None
        assert player_core.media_player is not None


class TestPlayerCoreVolume:
    """Test volume control."""

    def test_get_volume(self, player_core):
        """Test getting volume."""
        player_core.media_player._volume = 75
        assert player_core.get_volume() == 75

    def test_set_volume(self, player_core):
        """Test setting volume."""
        player_core.set_volume(50)
        assert player_core.media_player.audio_get_volume() == 50

    def test_set_volume_clamps_to_max(self, player_core):
        """Test that volume is clamped to 100."""
        player_core.set_volume(150)
        assert player_core.media_player.audio_get_volume() == 100

    def test_set_volume_clamps_to_min(self, player_core):
        """Test that volume is clamped to 0."""
        player_core.set_volume(-10)
        assert player_core.media_player.audio_get_volume() == 0


class TestPlayerCoreTimeAndDuration:
    """Test time and duration methods."""

    def test_get_current_time(self, player_core):
        """Test getting current playback time."""
        player_core.media_player._time = 30000  # 30 seconds
        assert player_core.get_current_time() == 30000

    def test_get_duration(self, player_core):
        """Test getting media duration."""
        from tests.mocks import MockMedia

        # Need to set media for get_length() to return non-zero
        media = MockMedia("/test/file.mp3")
        player_core.media_player.set_media(media)
        player_core.media_player._length = 180000  # 3 minutes
        assert player_core.get_duration() == 180000

    def test_get_duration_no_media(self, player_core):
        """Test getting duration with no media loaded."""
        player_core.media_player.set_media(None)
        assert player_core.get_duration() == 0


class TestPlayerCoreSeek:
    """Test seeking functionality."""

    def test_seek_to_position(self, player_core, mock_queue_view):
        """Test seeking to a position (0.0-1.0)."""
        # Set up media with known length
        from tests.mocks import MockMedia

        media = MockMedia("/test/file.mp3")
        player_core.media_player.set_media(media)
        player_core.media_player._length = 180000  # 3 minutes

        # Mock queue view to have a selected item
        mock_queue_view.selection.return_value = ["item1"]
        mock_queue_view.item.return_value = {"values": ("Artist", "Title", "180000")}

        # Seek to 50%
        player_core.seek(0.5)

        # Should be at 90 seconds
        assert player_core.media_player.get_time() == 90000

    def test_seek_to_beginning(self, player_core, mock_queue_view):
        """Test seeking to beginning."""
        from tests.mocks import MockMedia

        media = MockMedia("/test/file.mp3")
        player_core.media_player.set_media(media)
        player_core.media_player._length = 180000
        player_core.media_player._time = 90000

        # Mock queue view
        mock_queue_view.selection.return_value = ["item1"]
        mock_queue_view.item.return_value = {"values": ("Artist", "Title", "180000")}

        # Seek to beginning
        player_core.seek(0.0)
        assert player_core.media_player.get_time() == 0

    def test_seek_to_end(self, player_core, mock_queue_view):
        """Test seeking to end."""
        from tests.mocks import MockMedia

        media = MockMedia("/test/file.mp3")
        player_core.media_player.set_media(media)
        player_core.media_player._length = 180000

        # Mock queue view
        mock_queue_view.selection.return_value = ["item1"]
        mock_queue_view.item.return_value = {"values": ("Artist", "Title", "180000")}

        # Seek to end
        player_core.seek(1.0)
        assert player_core.media_player.get_time() == 180000


class TestPlayerCoreLoop:
    """Test loop functionality with three-state cycle: OFF → LOOP ALL → REPEAT ONE → OFF."""

    def test_toggle_loop_off_to_loop_all(self, player_core, mock_db):
        """Test first toggle: OFF → LOOP ALL."""
        player_core.loop_enabled = False
        player_core.repeat_one = False
        player_core.toggle_loop()
        assert player_core.loop_enabled is True
        assert player_core.repeat_one is False
        mock_db.set_loop_enabled.assert_called_once_with(True)
        mock_db.set_repeat_one.assert_called_once_with(False)

    def test_toggle_loop_all_to_repeat_one(self, player_core, mock_db):
        """Test second toggle: LOOP ALL → REPEAT ONE."""
        player_core.loop_enabled = True
        player_core.repeat_one = False
        player_core.toggle_loop()
        assert player_core.loop_enabled is True
        assert player_core.repeat_one is True
        mock_db.set_loop_enabled.assert_called_once_with(True)
        mock_db.set_repeat_one.assert_called_once_with(True)

    def test_toggle_repeat_one_to_off(self, player_core, mock_db):
        """Test third toggle: REPEAT ONE → OFF."""
        player_core.loop_enabled = True
        player_core.repeat_one = True
        player_core.toggle_loop()
        assert player_core.loop_enabled is False
        assert player_core.repeat_one is False
        mock_db.set_loop_enabled.assert_called_once_with(False)
        mock_db.set_repeat_one.assert_called_once_with(False)

    def test_toggle_loop_full_cycle(self, player_core, mock_db):
        """Test complete cycle through all three states."""
        # Start: OFF
        player_core.loop_enabled = False
        player_core.repeat_one = False
        
        # First toggle: OFF → LOOP ALL
        player_core.toggle_loop()
        assert (player_core.loop_enabled, player_core.repeat_one) == (True, False)
        
        # Second toggle: LOOP ALL → REPEAT ONE
        player_core.toggle_loop()
        assert (player_core.loop_enabled, player_core.repeat_one) == (True, True)
        
        # Third toggle: REPEAT ONE → OFF
        player_core.toggle_loop()
        assert (player_core.loop_enabled, player_core.repeat_one) == (False, False)
        
        # Should cycle back: OFF → LOOP ALL
        player_core.toggle_loop()
        assert (player_core.loop_enabled, player_core.repeat_one) == (True, False)


class TestPlayerCoreRepeatOne:
    """Test repeat-one 'play once more' functionality."""

    def test_toggle_to_repeat_one_prepends_track(self, player_core, mock_db, monkeypatch):
        """Test that activating repeat-one immediately prepends current track to queue."""
        from unittest.mock import Mock
        # Start in loop ALL state
        player_core.loop_enabled = True
        player_core.repeat_one = False
        player_core.current_file = "/track1.mp3"

        # Set up queue
        player_core.queue_manager.queue_items = ["/track1.mp3", "/track2.mp3", "/track3.mp3"]
        player_core.queue_manager.current_index = 0

        # Mock prepend_track
        mock_prepend = Mock()
        monkeypatch.setattr(player_core.queue_manager, 'prepend_track', mock_prepend)

        # Toggle to repeat-one
        player_core.toggle_loop()

        # Verify prepend was called with current file
        assert player_core.repeat_one is True
        assert player_core.repeat_one_prepended_track == "/track1.mp3"
        assert player_core.repeat_one_pending_revert is False  # Not set until prepended track plays
        mock_prepend.assert_called_once_with("/track1.mp3")

    def test_repeat_one_auto_reverts_after_track_end(self, player_core, mock_db, monkeypatch):
        """Test that repeat-one auto-reverts to loop OFF after track ends."""
        player_core.repeat_one = True
        player_core.repeat_one_pending_revert = True
        player_core.loop_enabled = True
        player_core.is_playing = True

        # Set up queue (track was already prepended)
        player_core.queue_manager.queue_items = ["/track1.mp3", "/track2.mp3"]
        player_core.queue_manager.current_index = 0

        # Mock methods
        monkeypatch.setattr(player_core, '_is_last_song', lambda: False)
        monkeypatch.setattr(player_core, '_get_next_filepath', lambda: "/track2.mp3")
        monkeypatch.setattr(player_core, '_play_file', lambda fp: None)

        # Track end should auto-revert to loop OFF
        player_core._handle_track_end()

        # Verify auto-revert happened
        assert player_core.repeat_one is False
        assert player_core.loop_enabled is False
        assert player_core.repeat_one_pending_revert is False
        mock_db.set_repeat_one.assert_called_with(False)
        mock_db.set_loop_enabled.assert_called_with(False)

    def test_manual_next_cancels_repeat_one(self, player_core, mock_db, monkeypatch):
        """Test that manual next cancels repeat-one and reverts to loop ALL."""
        player_core.repeat_one = True
        player_core.repeat_one_pending_revert = True
        player_core.loop_enabled = True
        player_core.is_playing = True

        # Set up queue
        player_core.queue_manager.queue_items = ["/track1.mp3", "/track2.mp3"]
        player_core.queue_manager.current_index = 0

        # Mock necessary methods
        monkeypatch.setattr(player_core, '_check_rate_limit', lambda action, limit: True)
        monkeypatch.setattr(player_core, '_get_current_track_info', lambda: {"artist": "Test", "title": "Track"})
        monkeypatch.setattr(player_core, '_is_last_song', lambda: False)
        monkeypatch.setattr(player_core.queue_manager, 'move_current_to_end_and_get_next', lambda: "/track2.mp3")
        monkeypatch.setattr(player_core, '_play_file', lambda fp: None)
        monkeypatch.setattr(player_core, '_get_next_filepath', lambda: "/track2.mp3")
        import os
        monkeypatch.setattr(os.path, 'basename', lambda p: p)

        # Call next
        player_core.next_song()

        # Verify repeat-one was cancelled and reverted to loop ALL
        assert player_core.repeat_one is False
        assert player_core.loop_enabled is True
        assert player_core.repeat_one_pending_revert is False

    def test_manual_previous_cancels_repeat_one(self, player_core, mock_db, monkeypatch):
        """Test that manual previous cancels repeat-one and reverts to loop ALL."""
        player_core.repeat_one = True
        player_core.repeat_one_pending_revert = True
        player_core.loop_enabled = True
        player_core.is_playing = True

        # Set up queue
        player_core.queue_manager.queue_items = ["/track1.mp3", "/track2.mp3"]
        player_core.queue_manager.current_index = 1

        # Mock necessary methods
        monkeypatch.setattr(player_core, '_check_rate_limit', lambda action, limit: True)
        monkeypatch.setattr(player_core, '_get_current_track_info', lambda: {"artist": "Test", "title": "Track"})
        monkeypatch.setattr(player_core, '_get_previous_filepath', lambda: "/track1.mp3")
        monkeypatch.setattr(player_core, '_play_file', lambda fp: None)
        import os
        monkeypatch.setattr(os.path, 'basename', lambda p: p)

        # Call previous
        player_core.previous_song()

        # Verify repeat-one was cancelled and reverted to loop ALL
        assert player_core.repeat_one is False
        assert player_core.loop_enabled is True
        assert player_core.repeat_one_pending_revert is False

    def test_stop_after_current_takes_precedence_over_repeat_one(self, player_core, mock_db, monkeypatch):
        """Test that stop_after_current takes precedence over repeat-one."""
        player_core.repeat_one = True
        player_core.stop_after_current = True
        player_core.is_playing = True

        # Mock stop method
        stop_calls = []
        monkeypatch.setattr(player_core, 'stop', lambda reason: stop_calls.append(reason))

        player_core._handle_track_end()

        assert len(stop_calls) == 1
        assert stop_calls[0] == "stop_after_current"
        assert player_core.stop_after_current is False


class TestPlayerCoreShuffle:
    """Test shuffle functionality."""

    def test_toggle_shuffle_off_to_on(self, player_core, mock_queue_manager):
        """Test enabling shuffle."""
        player_core.shuffle_enabled = False
        # toggle_shuffle() returns the new state
        mock_queue_manager.toggle_shuffle.return_value = True
        player_core.toggle_shuffle()
        assert player_core.shuffle_enabled is True
        mock_queue_manager.toggle_shuffle.assert_called_once()

    def test_toggle_shuffle_on_to_off(self, player_core, mock_queue_manager):
        """Test disabling shuffle."""
        player_core.shuffle_enabled = True
        # toggle_shuffle() returns the new state
        mock_queue_manager.toggle_shuffle.return_value = False
        player_core.toggle_shuffle()
        assert player_core.shuffle_enabled is False
        mock_queue_manager.toggle_shuffle.assert_called_once()


class TestPlayerCoreStop:
    """Test stop functionality."""

    def test_stop_clears_playback_state(self, player_core):
        """Test that stop clears playback state."""
        # Set up playing state
        player_core.is_playing = True
        player_core.current_file = "/test/file.mp3"
        player_core.media_player._is_playing = True

        # Stop playback
        player_core.stop()

        assert player_core.is_playing is False
        assert player_core.current_file is None
        assert player_core.media_player.get_media() is None
        assert player_core.media_player.is_playing() is False


class TestPlayerCoreTrackNavigation:
    """Test track navigation functionality."""

    def test_is_last_song_true(self, player_core, mock_queue_manager, mock_queue_view):
        """Test detecting last song in queue."""
        # Mock in-memory queue with 5 items, currently at last one
        mock_queue_manager.queue_items = [f"/path/to/song{i}.mp3" for i in range(5)]
        mock_queue_manager.current_index = 4  # Last song
        player_core.loop_enabled = False

        assert player_core._is_last_song() is True

    def test_is_last_song_false(self, player_core, mock_queue_manager, mock_queue_view):
        """Test detecting not last song."""
        # Mock in-memory queue with 5 items, currently at third one
        mock_queue_manager.queue_items = [f"/path/to/song{i}.mp3" for i in range(5)]
        mock_queue_manager.current_index = 2  # Third song (index 2)
        player_core.loop_enabled = False

        assert player_core._is_last_song() is False

    def test_is_last_song_with_loop_enabled(self, player_core, mock_queue_manager, mock_queue_view):
        """Test that _is_last_song() checks position regardless of loop.

        Note: Loop is checked in _handle_track_end(), not in _is_last_song().
        """
        # Mock in-memory queue with 5 items, currently at last one
        mock_queue_manager.queue_items = [f"/path/to/song{i}.mp3" for i in range(5)]
        mock_queue_manager.current_index = 4  # Last song
        player_core.loop_enabled = True

        # _is_last_song() just checks position, doesn't care about loop
        assert player_core._is_last_song() is True
