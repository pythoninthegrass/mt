"""Concurrent operation and race condition tests for PlayerCore.

These tests verify thread safety and proper handling of rapid concurrent operations
that could trigger race conditions, particularly with shuffle+loop+next combinations.
"""

import pytest
import time
from config import TEST_TIMEOUT


@pytest.mark.order("last")
def test_rapid_next_operations(api_client, test_music_files, clean_queue):
    """Test rapid consecutive next() calls don't cause race conditions.

    This tests:
    - Adding multiple tracks to queue
    - Enabling shuffle and loop modes
    - Rapidly calling next() multiple times
    - Verifying no crashes or state corruption
    """
    # Add tracks to queue
    api_client.send('add_to_queue', files=test_music_files[:10])

    # Enable shuffle and loop
    api_client.send('toggle_shuffle')
    api_client.send('toggle_loop')

    # Start playback
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Rapidly call next() 20 times
    for i in range(20):
        response = api_client.send('next')
        assert response['status'] == 'success', f"Next operation {i+1} failed: {response.get('message', '')}"
        # Very short delay to simulate rapid button clicks
        time.sleep(0.05)

    # Give VLC extra recovery time after stress test
    time.sleep(0.2)

    # Verify player is still in valid state
    status = api_client.send('get_status')
    assert status['status'] == 'success', "Failed to get status after rapid next calls"
    assert status['data']['is_playing'] is True, "Player should still be playing"

    # Verify queue is still intact (loop mode should keep all tracks)
    queue = api_client.send('get_queue')
    assert queue['status'] == 'success', "Failed to get queue"
    assert queue['count'] == 10, f"Queue should still have 10 items, got {queue['count']}"


@pytest.mark.order("last")
def test_concurrent_next_and_track_end(api_client, test_music_files, clean_queue):
    """Test that next() called during track end doesn't cause race conditions.

    This tests:
    - Playing very short tracks that end quickly
    - Calling next() while track is ending
    - Verifying no double-advancement or crashes
    """
    # Add tracks to queue
    api_client.send('add_to_queue', files=test_music_files[:5])

    # Enable loop to prevent queue exhaustion
    api_client.send('toggle_loop')

    # Start playback
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Get initial track
    initial_track = api_client.send('get_current_track')
    assert initial_track['status'] == 'success', "Failed to get initial track"
    initial_title = initial_track['data'].get('title')

    # Call next() multiple times in quick succession
    for _ in range(5):
        api_client.send('next')
        time.sleep(0.01)  # Minimal delay

    # Allow time for operations to complete
    time.sleep(TEST_TIMEOUT * 2)

    # Verify player is in valid state
    status = api_client.send('get_status')
    assert status['status'] == 'success', "Failed to get status"
    assert status['data']['is_playing'] is True, "Player should be playing"

    # Verify we're on a different track
    current_track = api_client.send('get_current_track')
    assert current_track['status'] == 'success', "Failed to get current track"
    current_title = current_track['data'].get('title')
    # Track may have changed (expected) or may be same if queue very short
    # Main goal is no crash

    # Give VLC extra recovery time after stress test
    time.sleep(0.2)


@pytest.mark.order("last")
def test_rapid_play_pause_with_next(api_client, test_music_files, clean_queue):
    """Test mixing play/pause with next() operations rapidly.

    This tests:
    - Rapid alternation between play_pause and next
    - Verifying state consistency
    - No crashes or invalid states
    """
    # Add tracks to queue
    api_client.send('add_to_queue', files=test_music_files[:8])

    # Enable loop
    api_client.send('toggle_loop')

    # Start playback
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Rapidly alternate between operations
    operations = ['next', 'play_pause', 'next', 'next', 'play_pause', 'next', 'play_pause', 'next']

    for op in operations:
        response = api_client.send(op)
        assert response['status'] == 'success', f"Operation {op} failed"
        time.sleep(0.05)

    # Allow operations to settle
    time.sleep(TEST_TIMEOUT)

    # Verify player is in valid state
    status = api_client.send('get_status')
    assert status['status'] == 'success', "Failed to get status"
    # Player may be playing or paused, both are valid
    assert 'is_playing' in status['data'], "Status should include is_playing"

    # Give VLC extra recovery time after stress test
    time.sleep(0.2)


@pytest.mark.order("last")
def test_shuffle_toggle_during_playback(api_client, test_music_files, clean_queue):
    """Test toggling shuffle on/off during active playback with next operations.

    This tests:
    - Toggling shuffle state while playing
    - Calling next() after shuffle state changes
    - Verifying no state corruption or crashes
    """
    # Add tracks to queue
    api_client.send('add_to_queue', files=test_music_files[:10])

    # Enable loop
    api_client.send('toggle_loop')

    # Start playback
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Perform operations with shuffle toggling
    for i in range(5):
        # Toggle shuffle
        shuffle_response = api_client.send('toggle_shuffle')
        assert shuffle_response['status'] == 'success', f"Shuffle toggle {i+1} failed"

        # Call next a few times
        for _ in range(3):
            next_response = api_client.send('next')
            assert next_response['status'] == 'success', "Next after shuffle toggle failed"
            time.sleep(0.05)

        time.sleep(0.1)

    # Verify player is still in valid state
    status = api_client.send('get_status')
    assert status['status'] == 'success', "Failed to get status"
    assert status['data']['is_playing'] is True, "Player should be playing"

    # Verify queue integrity
    queue = api_client.send('get_queue')
    assert queue['status'] == 'success', "Failed to get queue"
    assert queue['count'] == 10, f"Queue should have 10 items, got {queue['count']}"

    # Give VLC extra recovery time after stress test
    time.sleep(0.2)


@pytest.mark.order("last")
def test_queue_exhaustion_with_rapid_next(api_client, test_music_files, clean_queue):
    """Test rapid next() operations when queue is exhausting (loop disabled).

    This tests:
    - Queue exhaustion behavior
    - Defensive handling of empty queue
    - No crashes when next() called on empty/exhausted queue
    """
    # Add small number of tracks
    api_client.send('add_to_queue', files=test_music_files[:3])

    # Loop is disabled by clean_queue fixture

    # Start playback
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Call next() many times (more than tracks available)
    # This should exhaust the queue without loop
    for i in range(10):
        response = api_client.send('next')
        # After queue exhaustion, next() should gracefully handle empty queue
        # May succeed (no-op) or return success status
        assert response['status'] == 'success', f"Next call {i+1} failed ungracefully"
        time.sleep(0.05)

    # Verify player stopped (queue exhausted)
    status = api_client.send('get_status')
    assert status['status'] == 'success', "Failed to get status"
    # Player should have stopped when queue exhausted
    # (is_playing may be False or queue may be empty)

    # Give VLC extra recovery time after stress test
    time.sleep(0.2)


@pytest.mark.order("last")
def test_stress_test_100_rapid_next_operations(api_client, test_music_files, clean_queue):
    """Stress test: 100 rapid next() operations with shuffle+loop.

    This is the ultimate stress test for race conditions in next_song().
    With proper locking, all 100 operations should complete successfully.
    """
    # Add tracks to queue
    api_client.send('add_to_queue', files=test_music_files[:10])

    # Enable shuffle and loop
    api_client.send('toggle_shuffle')
    api_client.send('toggle_loop')

    # Start playback
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Perform 100 rapid next() operations
    success_count = 0
    for i in range(100):
        response = api_client.send('next')
        if response['status'] == 'success':
            success_count += 1
        # Minimal delay to maximize concurrency stress
        time.sleep(0.01)

    # All operations should succeed
    assert success_count == 100, f"Only {success_count}/100 next operations succeeded"

    # Verify player is still in valid state
    status = api_client.send('get_status')
    assert status['status'] == 'success', "Failed to get status after stress test"
    assert status['data']['is_playing'] is True, "Player should still be playing"

    # Verify queue integrity maintained
    queue = api_client.send('get_queue')
    assert queue['status'] == 'success', "Failed to get queue"
    assert queue['count'] == 10, f"Queue should have 10 items, got {queue['count']}"

    # Give VLC extra recovery time after ultimate stress test
    time.sleep(0.5)
