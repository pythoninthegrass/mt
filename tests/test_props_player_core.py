"""Property-based tests for PlayerCore using Hypothesis.

These tests validate invariants and properties of the PlayerCore class
that should hold for all valid inputs. They complement unit tests by
discovering edge cases through automated test generation.
"""

import pytest
import sys
from hypothesis import HealthCheck, given, settings, strategies as st
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.mocks import MockEventType, MockInstance, MockMedia


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
    view.selection.return_value = []
    view.get_children.return_value = []
    return view


@pytest.fixture
def player_core(mock_vlc, mock_db, mock_queue_manager, mock_queue_view):
    """Create PlayerCore with mocked dependencies.

    This fixture ensures proper isolation even if VLC has been imported by E2E tests.
    It removes cached modules and re-imports them with mocked VLC to prevent
    contamination from real VLC instances.
    """
    # Store and remove any cached modules that import VLC
    cached_modules = {}
    modules_to_remove = [
        'core.controls.player_core',
        'core.controls',
    ]

    for module_name in modules_to_remove:
        if module_name in sys.modules:
            cached_modules[module_name] = sys.modules[module_name]
            del sys.modules[module_name]

    try:
        with patch.dict('sys.modules', {'vlc': mock_vlc}):
            from core.controls import PlayerCore

            player = PlayerCore(mock_db, mock_queue_manager, mock_queue_view)
            return player
    finally:
        # Restore cached modules after test
        for module_name, module in cached_modules.items():
            sys.modules[module_name] = module


class TestPlayerCoreVolumeProperties:
    """Property-based tests for volume control."""

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(volume=st.integers(min_value=-1000, max_value=1000))
    def test_volume_clamps_to_valid_range(self, player_core, volume):
        """Volume should always clamp to valid range [0, 100]."""
        player_core.set_volume(volume)
        actual = player_core.get_volume()
        assert 0 <= actual <= 100

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(volume=st.integers(min_value=0, max_value=100))
    def test_volume_roundtrip_within_bounds(self, player_core, volume):
        """Setting a valid volume should be retrievable unchanged."""
        player_core.set_volume(volume)
        actual = player_core.get_volume()
        assert actual == volume

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(volume=st.integers(min_value=101, max_value=10000))
    def test_volume_above_max_clamps_to_100(self, player_core, volume):
        """Any volume above 100 should clamp to exactly 100."""
        player_core.set_volume(volume)
        assert player_core.get_volume() == 100

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(volume=st.integers(min_value=-10000, max_value=-1))
    def test_volume_below_min_clamps_to_0(self, player_core, volume):
        """Any volume below 0 should clamp to exactly 0."""
        player_core.set_volume(volume)
        assert player_core.get_volume() == 0


class TestPlayerCoreSeekProperties:
    """Property-based tests for seeking functionality."""

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(position=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    def test_seek_position_stays_in_bounds(self, player_core, mock_queue_view, position):
        """Seek position should always result in time within [0, duration]."""
        # Set up media with known length
        media = MockMedia("/test/file.mp3")
        player_core.media_player.set_media(media)
        player_core.media_player._length = 180000  # 3 minutes

        # Mock queue view
        mock_queue_view.selection.return_value = ["item1"]
        mock_queue_view.item.return_value = {"values": ("Artist", "Title", "180000")}

        # Seek to position
        player_core.seek(position)

        # Get resulting time
        actual_time = player_core.media_player.get_time()

        # Should be within bounds
        assert 0 <= actual_time <= 180000

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        position=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        duration=st.integers(min_value=1000, max_value=600000),
    )
    def test_seek_position_proportional_to_duration(self, player_core, mock_queue_view, position, duration):
        """Seek position should be proportional to duration."""
        # Set up media with variable duration
        media = MockMedia("/test/file.mp3")
        player_core.media_player.set_media(media)
        player_core.media_player._length = duration

        # Mock queue view
        mock_queue_view.selection.return_value = ["item1"]
        mock_queue_view.item.return_value = {"values": ("Artist", "Title", str(duration))}

        # Seek to position
        player_core.seek(position)

        # Get resulting time
        actual_time = player_core.media_player.get_time()

        # Calculate expected time (with tolerance for floating point)
        expected_time = int(duration * position)

        # Should be very close to expected (within 1ms tolerance)
        assert abs(actual_time - expected_time) <= 1


class TestPlayerCoreToggleProperties:
    """Property-based tests for toggle operations."""

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(initial_loop=st.booleans())
    def test_loop_toggle_idempotent(self, player_core, mock_db, initial_loop):
        """Toggling loop twice should return to original state."""
        player_core.loop_enabled = initial_loop

        # Toggle twice
        player_core.toggle_loop()
        player_core.toggle_loop()

        # Should be back to initial state
        assert player_core.loop_enabled == initial_loop

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(initial_shuffle=st.booleans())
    def test_shuffle_toggle_idempotent(self, player_core, mock_queue_manager, initial_shuffle):
        """Toggling shuffle twice should return to original state."""
        player_core.shuffle_enabled = initial_shuffle

        # Configure mock to alternate returns
        mock_queue_manager.toggle_shuffle.side_effect = [
            not initial_shuffle,
            initial_shuffle,
        ]

        # Toggle twice
        player_core.toggle_shuffle()
        player_core.toggle_shuffle()

        # Should be back to initial state
        assert player_core.shuffle_enabled == initial_shuffle

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(initial_state=st.booleans())
    def test_loop_toggle_inverts_state(self, player_core, mock_db, initial_state):
        """Toggling loop once should invert the state."""
        player_core.loop_enabled = initial_state

        # Toggle once
        player_core.toggle_loop()

        # Should be inverted
        assert player_core.loop_enabled != initial_state
        assert player_core.loop_enabled == (not initial_state)


class TestPlayerCoreTimeProperties:
    """Property-based tests for time and duration."""

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(current_time=st.integers(min_value=0, max_value=1000000))
    def test_get_current_time_non_negative(self, player_core, current_time):
        """Current time should always be non-negative."""
        player_core.media_player._time = current_time
        actual = player_core.get_current_time()
        assert actual >= 0

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(duration=st.integers(min_value=0, max_value=1000000))
    def test_get_duration_non_negative(self, player_core, duration):
        """Duration should always be non-negative."""
        media = MockMedia("/test/file.mp3")
        player_core.media_player.set_media(media)
        player_core.media_player._length = duration

        actual = player_core.get_duration()
        assert actual >= 0

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(duration=st.integers(min_value=1, max_value=1000000))
    def test_get_duration_matches_media_length(self, player_core, duration):
        """Duration should match the media length."""
        media = MockMedia("/test/file.mp3")
        player_core.media_player.set_media(media)
        player_core.media_player._length = duration

        actual = player_core.get_duration()
        assert actual == duration
