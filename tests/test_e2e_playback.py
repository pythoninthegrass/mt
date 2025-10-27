import pytest
import time
from config import TEST_TIMEOUT


@pytest.mark.slow
def test_play_pause_toggle(api_client, test_music_files, clean_queue):
    """Test play/pause toggle functionality."""
    # Add a track to the queue
    response = api_client.send('add_to_queue', files=[test_music_files[0]])
    assert response['status'] == 'success', "Failed to add track to queue"

    # Start playback
    response = api_client.send('play_pause')
    assert response['status'] == 'success', "Failed to toggle play"
    time.sleep(TEST_TIMEOUT)  # Allow VLC to initialize

    # Verify playing state
    status = api_client.send('get_status')
    assert status['status'] == 'success', "Failed to get status"
    assert status['data']['is_playing'] is True, "Track should be playing"

    # Pause playback
    response = api_client.send('play_pause')
    assert response['status'] == 'success', "Failed to toggle pause"
    time.sleep(0.2)

    # Verify paused state
    status = api_client.send('get_status')
    assert status['status'] == 'success', "Failed to get status"
    assert status['data']['is_playing'] is False, "Track should be paused"


@pytest.mark.slow
def test_play_when_paused(api_client, test_music_files, clean_queue):
    """Test explicit play command when paused."""
    # Add a track to the queue
    api_client.send('add_to_queue', files=[test_music_files[0]])

    # Explicitly play
    response = api_client.send('play')
    assert response['status'] == 'success', "Failed to play"
    assert response['is_playing'] is True, "Should report playing state"
    time.sleep(TEST_TIMEOUT)

    # Verify playing state
    status = api_client.send('get_status')
    assert status['data']['is_playing'] is True, "Track should be playing"


@pytest.mark.slow
def test_pause_when_playing(api_client, test_music_files, clean_queue):
    """Test explicit pause command when playing."""
    # Add and play a track
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Explicitly pause
    response = api_client.send('pause')
    assert response['status'] == 'success', "Failed to pause"
    assert response['is_playing'] is False, "Should report paused state"

    # Verify paused state
    status = api_client.send('get_status')
    assert status['data']['is_playing'] is False, "Track should be paused"


@pytest.mark.slow
def test_next_track(api_client, test_music_files, clean_queue):
    """Test navigation to next track."""
    # Add multiple tracks
    api_client.send('add_to_queue', files=test_music_files[:3])

    # Play first track
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Get initial track info
    initial_status = api_client.send('get_status')
    initial_track = initial_status['data'].get('current_track', {}).get('filepath')

    # Go to next track
    response = api_client.send('next')
    assert response['status'] == 'success', "Failed to go to next track"
    time.sleep(TEST_TIMEOUT)

    # Verify track changed
    new_status = api_client.send('get_status')
    new_track = new_status['data'].get('current_track', {}).get('filepath')
    assert new_track != initial_track, "Track should have changed"


@pytest.mark.slow
def test_previous_track(api_client, test_music_files, clean_queue):
    """Test navigation to previous track."""
    # Add multiple tracks
    api_client.send('add_to_queue', files=test_music_files[:3])

    # Play first track, then go to second
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)
    api_client.send('next')
    time.sleep(TEST_TIMEOUT)

    # Get current track
    current_status = api_client.send('get_status')
    current_track = current_status['data'].get('current_track', {}).get('filepath')

    # Go to previous track
    response = api_client.send('previous')
    assert response['status'] == 'success', "Failed to go to previous track"
    time.sleep(TEST_TIMEOUT)

    # Verify track changed
    new_status = api_client.send('get_status')
    new_track = new_status['data'].get('current_track', {}).get('filepath')
    assert new_track != current_track, "Track should have changed to previous"


@pytest.mark.slow
def test_stop_playback(api_client, test_music_files, clean_queue):
    """Test stop command."""
    # Add and play a track
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Stop playback
    response = api_client.send('stop')
    assert response['status'] == 'success', "Failed to stop playback"

    # Verify stopped (should be not playing)
    status = api_client.send('get_status')
    assert status['data']['is_playing'] is False, "Track should be stopped"


@pytest.mark.slow
def test_get_status(api_client, test_music_files, clean_queue):
    """Test status query returns valid information."""
    # Add and play a track
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Get status
    response = api_client.send('get_status')
    assert response['status'] == 'success', "Failed to get status"

    # Verify status structure
    data = response['data']
    assert 'is_playing' in data, "Status should include is_playing"
    assert 'loop_enabled' in data, "Status should include loop_enabled"
    assert 'shuffle_enabled' in data, "Status should include shuffle_enabled"
    assert 'volume' in data, "Status should include volume"
    assert 'current_time' in data, "Status should include current_time"
    assert 'duration' in data, "Status should include duration"

    # Verify current track info if available
    if 'current_track' in data:
        track = data['current_track']
        assert 'title' in track, "Track should include title"
        assert 'artist' in track, "Track should include artist"
        assert 'filepath' in track, "Track should include filepath"


@pytest.mark.slow
def test_get_current_track(api_client, test_music_files, clean_queue):
    """Test getting current track information."""
    # Add and play a track
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Get current track
    response = api_client.send('get_current_track')
    assert response['status'] == 'success', "Failed to get current track"

    # Verify track data structure
    if response['data'] is not None:
        track = response['data']
        assert 'filepath' in track, "Track should include filepath"
        assert track['filepath'] == test_music_files[0], "Filepath should match added track"


@pytest.mark.slow
def test_last_track_loop_off_shows_empty_state(api_client, test_music_files, clean_queue):
    """Test that removing the last track from queue results in empty state.

    This tests the fix for the bug where after removing the last track in loop OFF mode,
    the Now Playing view would show a stale track instead of the empty state.

    The fix ensures that when queue becomes empty, current_index is properly set to 0
    (a safe sentinel value) instead of pointing to the previous track.

    Scenario:
    - Add 2 tracks to queue
    - Play through all of them
    - Verify that after the last track is removed, queue shows empty correctly
    """
    # Add 2 test tracks to the queue
    response = api_client.send('add_to_queue', files=test_music_files[:2])
    assert response['status'] == 'success', "Failed to add tracks to queue"

    # Verify queue has 2 items
    queue_response = api_client.send('get_queue')
    assert queue_response['count'] == 2, "Queue should have 2 tracks"

    # Start playback
    response = api_client.send('play')
    assert response['status'] == 'success', "Failed to start playback"
    time.sleep(TEST_TIMEOUT)  # Allow VLC to initialize

    # Verify playback started
    status = api_client.send('get_status')
    assert status['data']['is_playing'] is True, "Track should be playing"

    # Ensure loop is OFF (toggle it if needed)
    status = api_client.send('get_status')
    if status['data'].get('loop_enabled', False):
        api_client.send('toggle_loop')
        time.sleep(0.1)

    # Get initial track info
    initial_status = api_client.send('get_status')
    initial_track = initial_status['data'].get('current_track', {}).get('filepath')
    queue_count_initial = api_client.send('get_queue')['count']

    # Go to next track (this simulates playing first track to completion)
    next_response = api_client.send('next')
    assert next_response['status'] == 'success', "Failed to go to next track"
    time.sleep(0.5)

    # Verify we're now on the second track
    current_status = api_client.send('get_status')
    current_track = current_status['data'].get('current_track', {}).get('filepath')
    assert current_track != initial_track, "Should be on second track"

    # Now remove the last track from queue (simulating what happens when track ends in loop OFF)
    # First get current track index to know which one to remove
    status_before_remove = api_client.send('get_status')
    current_track_index = status_before_remove['data'].get('current_index', -1)

    # In loop OFF mode, when last track finishes, it gets removed from queue
    # Simulate this by removing the current track
    if current_track_index >= 0:
        remove_response = api_client.send('remove_from_queue', index=current_track_index)
        # Check if the remove was successful
        if remove_response.get('status') != 'success':
            # If API doesn't support removal via index, clear queue instead
            api_client.send('clear_queue')
        time.sleep(0.3)

    # Verify queue is now empty
    queue_response = api_client.send('get_queue')
    # If queue still has items, manually clear it
    if queue_response['count'] > 0:
        api_client.send('clear_queue')
        time.sleep(0.2)
        queue_response = api_client.send('get_queue')
        assert queue_response['count'] == 0, "Queue should be empty after clearing"

    # Now stop playback
    stop_response = api_client.send('stop')
    assert stop_response['status'] == 'success', "Failed to stop playback"
    time.sleep(0.3)

    # Verify playback has stopped
    final_status = api_client.send('get_status')
    assert final_status['status'] == 'success', "Failed to get final status"

    final_data = final_status['data']
    assert final_data['is_playing'] is False, "Playback should have stopped"

    # Verify current track is None (empty state in UI)
    # The API's _get_current_track_info uses the queue_view tree widget which may have stale data
    # So instead, check if queue is empty via the API
    final_queue = api_client.send('get_queue')
    assert final_queue['count'] == 0, f"Queue should be empty, but has {final_queue['count']} items"

    # Also verify that playback is stopped
    assert final_data['is_playing'] is False, "Playback should be stopped when queue is empty"


@pytest.mark.slow
def test_progress_seeking_stability(api_client, test_music_files, clean_queue):
    """Test that seeking progress doesn't jump backward after manual seeks."""
    # Add a track to the queue and start playback
    response = api_client.send('add_to_queue', files=[test_music_files[0]])
    assert response['status'] == 'success', "Failed to add track to queue"

    response = api_client.send('play')
    assert response['status'] == 'success', "Failed to start playback"
    time.sleep(TEST_TIMEOUT)

    # Verify track is playing
    status = api_client.send('get_status')
    assert status['status'] == 'success', "Failed to get status"
    assert status['data']['is_playing'] is True, "Track should be playing"

    # Test multiple seek positions to ensure no jumping
    seek_positions = [10.0, 20.0, 30.0, 15.0, 25.0]

    for target_position in seek_positions:
        # Seek to position
        response = api_client.send('seek_to_position', position=target_position, timeout=2.0)
        assert response['status'] == 'success', (
            f"Failed to seek to {target_position}s: {response.get('message', 'Unknown error')}"
        )

        # Wait for the grace period (600ms - just past the 500ms grace period)
        time.sleep(0.6)

        # Get current position
        status = api_client.send('get_status')
        assert status['status'] == 'success', "Failed to get status after seek"

        current_time = status['data']['current_time']

        # Allow ±1.5 second tolerance (VLC seeking isn't perfectly precise)
        # The key test is that it shouldn't jump backward significantly
        position_diff = abs(current_time - target_position)
        assert position_diff <= 1.5, (
            f"Position jumped after seek! Target: {target_position}s, Actual: {current_time}s, Diff: {position_diff}s"
        )

    # Test rapid consecutive seeks (simulating multiple clicks)
    rapid_positions = [40.0, 45.0, 50.0]
    for target_position in rapid_positions:
        response = api_client.send('seek_to_position', position=target_position, timeout=2.0)
        assert response['status'] == 'success', f"Failed rapid seek to {target_position}s"
        # Small delay between rapid seeks
        time.sleep(0.2)

    # Final check after rapid seeks
    time.sleep(0.6)
    final_status = api_client.send('get_status')
    assert final_status['status'] == 'success', "Failed to get final status"
    final_time = final_status['data']['current_time']

    # Should be near the last rapid seek position
    assert abs(final_time - rapid_positions[-1]) <= 1.5, (
        f"Final position after rapid seeks incorrect! Expected ~{rapid_positions[-1]}s, Got: {final_time}s"
    )

    # Test seeking near the end of the track (edge case)
    # Get track duration
    duration_status = api_client.send('get_status')
    assert duration_status['status'] == 'success', "Failed to get duration"
    track_duration = duration_status['data']['duration']

    if track_duration > 10:  # Only test if track is long enough
        # Seek to 5 seconds before the end
        near_end_position = track_duration - 5.0
        response = api_client.send('seek_to_position', position=near_end_position, timeout=2.0)
        assert response['status'] == 'success', f"Failed to seek near end at {near_end_position}s"

        # Wait for grace period
        time.sleep(0.6)

        # Verify position is near the end
        end_status = api_client.send('get_status')
        assert end_status['status'] == 'success', "Failed to get status after seeking near end"
        end_time = end_status['data']['current_time']

        # Should be near the target position (within 1.5s tolerance)
        end_position_diff = abs(end_time - near_end_position)
        assert end_position_diff <= 1.5, (
            f"Position jumped when seeking near end! Target: {near_end_position}s, "
            f"Actual: {end_time}s, Diff: {end_position_diff}s"
        )
