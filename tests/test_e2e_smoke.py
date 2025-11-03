"""E2E Smoke Tests - Fast critical path validation.

This test suite contains the minimum set of E2E tests needed to validate
core functionality. These tests run in ~15-20 seconds and should be used
for quick feedback during development and CI.

For comprehensive E2E coverage, run the full test suite (including @pytest.mark.slow tests).
"""

import pytest
import time
from config import TEST_TIMEOUT


def test_basic_playback_workflow(api_client, test_music_files, clean_queue):
    """Test the most critical user workflow: add track and play."""
    # Add a track
    response = api_client.send('add_to_queue', files=[test_music_files[0]])
    assert response['status'] == 'success'

    # Start playback
    response = api_client.send('play_pause')
    assert response['status'] == 'success'
    time.sleep(TEST_TIMEOUT)

    # Verify playing
    status = api_client.send('get_status')
    assert status['status'] == 'success'
    assert status['data']['is_playing'] is True


def test_queue_operations(api_client, test_music_files, clean_queue):
    """Test basic queue add/clear operations."""
    # Add tracks
    response = api_client.send('add_to_queue', files=test_music_files[:3])
    assert response['status'] == 'success'

    # Verify queue
    queue_response = api_client.send('get_queue')
    assert queue_response['count'] == 3

    # Clear queue
    response = api_client.send('clear_queue')
    assert response['status'] == 'success'

    queue_response = api_client.send('get_queue')
    assert queue_response['count'] == 0


@pytest.mark.flaky_in_suite
def test_next_previous_navigation(api_client, test_music_files, clean_queue):
    """Test track navigation with next/previous.

    Note: This test is flaky when run in full test suite due to persistent timing
    issues with track navigation after many other tests. Passes reliably when run
    in isolation. The test includes comprehensive retry logic but still experiences
    issues in full suite context.

    To run this test reliably:
        pytest tests/test_e2e_smoke.py::test_next_previous_navigation
    """
    # Add multiple tracks and play
    api_client.send('add_to_queue', files=test_music_files[:3])
    api_client.send('play')

    # Wait for playback to stabilize - give extra time in full test suite context
    time.sleep(TEST_TIMEOUT * 3)  # Increased to 3x for more stability

    # Get first track and verify queue state - with retry to ensure stable state
    initial_track = None
    initial_queue = None
    for _ in range(3):
        initial_status = api_client.send('get_status')
        initial_track = initial_status['data'].get('current_track', {}).get('filepath')
        initial_queue = api_client.send('get_queue')

        # Verify we're in a stable state
        if (initial_track and
            initial_track == test_music_files[0] and
            initial_queue['count'] >= 3 and
            initial_status['data'].get('is_playing', False) and
            not initial_status['data'].get('repeat_one', False)):
            break
        time.sleep(0.5)

    # Ensure we have enough tracks, playback is active, and no repeat-one is active
    assert initial_queue['count'] >= 3, f"Queue should have 3+ tracks, has {initial_queue['count']}"
    assert initial_status['data'].get('is_playing', False) is True, "Player should be playing"
    assert initial_status['data'].get('repeat_one', False) is False, "Repeat-one should be off"
    assert initial_track == test_music_files[0], f"Should be on first track, got {initial_track}"

    # Next track - use longer timeout and retry logic for timing variability
    next_response = api_client.send('next')
    time.sleep(TEST_TIMEOUT)  # Initial wait

    # Retry up to 5 times with increasing delays if track hasn't changed yet
    next_track = None
    for attempt in range(5):
        next_status = api_client.send('get_status')
        next_track = next_status['data'].get('current_track', {}).get('filepath')
        queue_status = api_client.send('get_queue')

        # Debug info on last attempt
        if attempt == 4 and next_track == initial_track:
            # Get full state for debugging
            print(f"\nDEBUG: Next command response: {next_response}")
            print(f"DEBUG: Queue count: {queue_status['count']}")
            print(f"DEBUG: Is playing: {next_status['data'].get('is_playing')}")
            print(f"DEBUG: Repeat-one: {next_status['data'].get('repeat_one')}")
            print(f"DEBUG: Loop enabled: {next_status['data'].get('loop_enabled')}")

        if next_track != initial_track:
            break
        time.sleep(0.3 * (attempt + 1))  # Progressive backoff: 0.3s, 0.6s, 0.9s, 1.2s, 1.5s

    assert next_track != initial_track, f"Track should have changed after next command. Initial: {initial_track}, After next: {next_track}"

    # Previous track - use longer timeout and retry logic
    api_client.send('previous')
    time.sleep(TEST_TIMEOUT)  # Initial wait

    # Retry up to 5 times with increasing delays if track hasn't changed yet
    prev_track = None
    for attempt in range(5):
        prev_status = api_client.send('get_status')
        prev_track = prev_status['data'].get('current_track', {}).get('filepath')
        if prev_track == initial_track:
            break
        time.sleep(0.3 * (attempt + 1))  # Progressive backoff: 0.3s, 0.6s, 0.9s, 1.2s, 1.5s

    assert prev_track == initial_track, f"Should return to first track after previous command. Initial: {initial_track}, After previous: {prev_track}"


def test_volume_control(api_client, test_music_files, clean_queue):
    """Test volume adjustment."""
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Set volume
    response = api_client.send('set_volume', volume=50)
    assert response['status'] == 'success'

    # Verify volume
    status = api_client.send('get_status')
    assert status['data']['volume'] == 50


def test_loop_toggle(api_client, clean_queue):
    """Test loop toggle functionality."""
    # Get initial state
    initial_status = api_client.send('get_status')
    initial_loop = initial_status['data'].get('loop_enabled', False)

    # Toggle loop
    response = api_client.send('toggle_loop')
    assert response['status'] == 'success'

    # Verify toggled
    status = api_client.send('get_status')
    assert status['data']['loop_enabled'] == (not initial_loop)


def test_shuffle_toggle(api_client, clean_queue):
    """Test shuffle toggle functionality."""
    # Get initial state
    initial_status = api_client.send('get_status')
    initial_shuffle = initial_status['data'].get('shuffle_enabled', False)

    # Toggle shuffle
    response = api_client.send('toggle_shuffle')
    assert response['status'] == 'success'

    # Verify toggled
    status = api_client.send('get_status')
    assert status['data']['shuffle_enabled'] == (not initial_shuffle)


def test_stop_clears_playback(api_client, test_music_files, clean_queue):
    """Test that stop clears playback state."""
    # Start playback
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Verify playing
    status = api_client.send('get_status')
    assert status['data']['is_playing'] is True

    # Stop
    response = api_client.send('stop')
    assert response['status'] == 'success'

    # Verify stopped
    status = api_client.send('get_status')
    assert status['data']['is_playing'] is False


def test_seek_position(api_client, test_music_files, clean_queue):
    """Test seeking to a specific position."""
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Seek to 10 seconds
    response = api_client.send('seek_to_position', position=10.0)
    assert response['status'] == 'success'
    time.sleep(0.2)

    # Verify position (allow some tolerance)
    status = api_client.send('get_status')
    current_time = status['data'].get('current_time', 0)
    assert 9.0 <= current_time <= 11.0, f"Expected ~10s, got {current_time}s"


def test_get_library_returns_data(api_client, clean_queue):
    """Test that library retrieval works."""
    response = api_client.send('get_library')
    assert response['status'] == 'success'
    assert 'data' in response
    assert isinstance(response['data'], list)


def test_search_library(api_client, clean_queue):
    """Test basic library search functionality."""
    # Search with empty query returns all
    response = api_client.send('search', query='')
    assert response['status'] == 'success'

    # Clear search
    response = api_client.send('clear_search')
    assert response['status'] == 'success'


def test_switch_view(api_client, clean_queue):
    """Test view switching."""
    # Switch to library view
    response = api_client.send('switch_view', view='library')
    assert response['status'] == 'success'

    # Switch back to queue view
    response = api_client.send('switch_view', view='queue')
    assert response['status'] == 'success'


def test_media_key_controls(api_client, test_music_files, clean_queue):
    """Test media key integration."""
    api_client.send('add_to_queue', files=test_music_files[:2])

    # Media key play/pause
    response = api_client.send('media_key', key='play_pause')
    assert response['status'] == 'success'
    time.sleep(TEST_TIMEOUT)

    # Verify playing
    status = api_client.send('get_status')
    assert status['data']['is_playing'] is True

    # Media key next
    response = api_client.send('media_key', key='next')
    assert response['status'] == 'success'


def test_concurrent_queue_modifications(api_client, test_music_files, clean_queue):
    """Test that rapid queue operations don't crash the app."""
    # Rapid adds
    for i in range(3):
        api_client.send('add_to_queue', files=[test_music_files[i % len(test_music_files)]])

    # Verify queue populated
    queue_response = api_client.send('get_queue')
    assert queue_response['count'] == 3

    # Play and rapidly navigate
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)
    api_client.send('next')
    api_client.send('next')
    time.sleep(0.3)

    # App should still respond
    status = api_client.send('get_status')
    assert status['status'] == 'success'
