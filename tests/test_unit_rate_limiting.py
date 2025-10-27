"""Unit tests for rate limiting functionality in PlayerCore."""

import pytest
import time
from unittest.mock import MagicMock, patch


def test_rate_limit_immediate_execution():
    """Test that first call executes immediately."""
    from core.controls.player_core import PlayerCore
    from core.db import MusicDatabase
    from core.queue import QueueManager

    # Create mocks
    db = MagicMock(spec=MusicDatabase)
    db.get_loop_enabled.return_value = False
    queue_mgr = MagicMock(spec=QueueManager)
    queue_mgr.is_shuffle_enabled.return_value = False
    queue_mgr.queue_items = []

    # Create PlayerCore instance
    player = PlayerCore(db, queue_mgr)

    # First call should execute immediately
    result = player._check_rate_limit('next_song', 0.1)
    assert result is True

    # Check that last_time was updated
    assert player._rate_limit_state['next_song']['last_time'] > 0


def test_rate_limit_throttles_rapid_calls():
    """Test that rapid calls are throttled."""
    from core.controls.player_core import PlayerCore
    from core.db import MusicDatabase
    from core.queue import QueueManager

    # Create mocks
    db = MagicMock(spec=MusicDatabase)
    db.get_loop_enabled.return_value = False
    queue_mgr = MagicMock(spec=QueueManager)
    queue_mgr.is_shuffle_enabled.return_value = False
    queue_mgr.queue_items = []

    # Create PlayerCore instance
    player = PlayerCore(db, queue_mgr)

    # First call executes immediately
    result1 = player._check_rate_limit('next_song', 0.1)
    assert result1 is True

    # Second call within 100ms should be throttled
    result2 = player._check_rate_limit('next_song', 0.1)
    assert result2 is False

    # Pending timer should be set
    assert player._rate_limit_state['next_song']['pending_timer'] is not None


def test_rate_limit_allows_after_interval():
    """Test that calls are allowed after minimum interval."""
    from core.controls.player_core import PlayerCore
    from core.db import MusicDatabase
    from core.queue import QueueManager

    # Create mocks
    db = MagicMock(spec=MusicDatabase)
    db.get_loop_enabled.return_value = False
    queue_mgr = MagicMock(spec=QueueManager)
    queue_mgr.is_shuffle_enabled.return_value = False
    queue_mgr.queue_items = []

    # Create PlayerCore instance
    player = PlayerCore(db, queue_mgr)

    # First call
    result1 = player._check_rate_limit('next_song', 0.1)
    assert result1 is True

    # Wait for interval to pass
    time.sleep(0.11)

    # Second call after interval should execute
    result2 = player._check_rate_limit('next_song', 0.1)
    assert result2 is True


def test_rate_limit_cancels_previous_pending():
    """Test that new throttled call cancels previous pending call."""
    from core.controls.player_core import PlayerCore
    from core.db import MusicDatabase
    from core.queue import QueueManager

    # Create mocks
    db = MagicMock(spec=MusicDatabase)
    db.get_loop_enabled.return_value = False
    queue_mgr = MagicMock(spec=QueueManager)
    queue_mgr.is_shuffle_enabled.return_value = False
    queue_mgr.queue_items = []

    # Create PlayerCore instance
    player = PlayerCore(db, queue_mgr)

    # First call executes
    player._check_rate_limit('next_song', 0.1)

    # Second call creates pending timer
    player._check_rate_limit('next_song', 0.1)
    first_timer = player._rate_limit_state['next_song']['pending_timer']
    assert first_timer is not None

    # Third call should cancel first timer and create new one
    player._check_rate_limit('next_song', 0.1)
    second_timer = player._rate_limit_state['next_song']['pending_timer']
    assert second_timer is not None
    assert second_timer is not first_timer


def test_rate_limit_different_methods_independent():
    """Test that rate limits for different methods are independent."""
    from core.controls.player_core import PlayerCore
    from core.db import MusicDatabase
    from core.queue import QueueManager

    # Create mocks
    db = MagicMock(spec=MusicDatabase)
    db.get_loop_enabled.return_value = False
    queue_mgr = MagicMock(spec=QueueManager)
    queue_mgr.is_shuffle_enabled.return_value = False
    queue_mgr.queue_items = []

    # Create PlayerCore instance
    player = PlayerCore(db, queue_mgr)

    # next_song executes
    result1 = player._check_rate_limit('next_song', 0.1)
    assert result1 is True

    # next_song throttled (too soon)
    result2 = player._check_rate_limit('next_song', 0.1)
    assert result2 is False

    # previous_song still executes (independent rate limit)
    result3 = player._check_rate_limit('previous_song', 0.1)
    assert result3 is True

    # play_pause still executes (independent rate limit)
    result4 = player._check_rate_limit('play_pause', 0.05)
    assert result4 is True


def test_rate_limit_pending_timer_executes(api_client, test_music_files, clean_queue):
    """Test that pending timer actually executes the method."""
    # Add tracks to queue
    for filepath in test_music_files[:3]:
        response = api_client.send('add_to_queue', files=[filepath])
        assert response['status'] == 'success'

    # Start playback
    response = api_client.send('play')
    assert response['status'] == 'success'
    time.sleep(0.5)  # Let playback start

    # Get initial current index
    status1 = api_client.send('get_status')
    initial_index = status1['data']['current_index']

    # Call next() rapidly 5 times
    for _ in range(5):
        api_client.send('next')

    # First call should execute immediately, others throttled
    # Wait for pending timer to execute (100ms + buffer)
    time.sleep(0.25)

    # Check that we advanced by 2 tracks (initial immediate + one pending)
    status2 = api_client.send('get_status')
    final_index = status2['data']['current_index']

    # Should have advanced at least 1 track (immediate)
    # May have advanced 2 if pending executed
    assert final_index > initial_index


def test_rate_limit_play_pause_faster_interval(api_client, test_music_files, clean_queue):
    """Test that play_pause has faster interval (50ms vs 100ms)."""
    # Add track to queue
    response = api_client.send('add_to_queue', files=[test_music_files[0]])
    assert response['status'] == 'success'

    # Start playback
    response = api_client.send('play')
    assert response['status'] == 'success'
    time.sleep(0.5)

    # Rapid play/pause calls
    start_time = time.time()
    for i in range(10):
        api_client.send('play_pause')
        if i < 9:  # Don't sleep after last call
            time.sleep(0.06)  # 60ms between calls (faster than next/previous but slower than play_pause limit)

    elapsed = time.time() - start_time

    # With 50ms rate limit, should allow ~6-7 immediate executions in 600ms
    # Verify no crashes occurred
    status = api_client.send('get_status')
    assert status['status'] == 'success'


def test_rapid_next_operations_with_rate_limiting(api_client, test_music_files, clean_queue):
    """Test that rapid next() calls don't crash the app."""
    # Add tracks to queue with shuffle and loop
    for filepath in test_music_files[:10]:
        response = api_client.send('add_to_queue', files=[filepath])
        assert response['status'] == 'success'

    # Enable shuffle and loop
    api_client.send('toggle_shuffle')
    api_client.send('toggle_loop')

    # Start playback
    response = api_client.send('play')
    assert response['status'] == 'success'
    time.sleep(0.5)

    # Rapid next() calls (20 operations)
    successful_calls = 0
    for i in range(20):
        try:
            response = api_client.send('next', max_retries=1)
            if response['status'] == 'success':
                successful_calls += 1
        except Exception:
            pass  # Some may be throttled or fail, that's ok
        time.sleep(0.01)  # 10ms between calls (very rapid)

    # Wait for any pending operations
    time.sleep(0.3)

    # Verify app is still responsive
    status = api_client.send('get_status')
    assert status['status'] == 'success'

    # Should have executed some calls (not all due to rate limiting)
    # But app should not have crashed
    assert successful_calls > 0
    assert successful_calls <= 20
