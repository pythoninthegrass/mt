import pytest
import time
from config import TEST_TIMEOUT


def test_set_volume_valid(api_client, test_music_files, clean_queue):
    """Test setting volume to valid values."""
    # Add and play a track
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Set volume to 50
    response = api_client.send('set_volume', volume=50)
    assert response['status'] == 'success', "Failed to set volume"
    assert response['volume'] == 50, "Volume should be set to 50"

    # Verify volume via status
    status = api_client.send('get_status')
    assert status['data']['volume'] == 50, "Status should report volume as 50"

    # Set volume to 0
    response = api_client.send('set_volume', volume=0)
    assert response['status'] == 'success', "Failed to set volume to 0"

    # Set volume to 100
    response = api_client.send('set_volume', volume=100)
    assert response['status'] == 'success', "Failed to set volume to 100"


def test_set_volume_invalid(api_client, test_music_files, clean_queue):
    """Test that invalid volume values are rejected."""
    # Try to set volume above 100
    response = api_client.send('set_volume', volume=150)
    assert response['status'] == 'error', "Should reject volume > 100"
    assert 'between 0 and 100' in response.get('message', '').lower(), "Error should mention range"

    # Try to set volume below 0
    response = api_client.send('set_volume', volume=-10)
    assert response['status'] == 'error', "Should reject volume < 0"


def test_set_volume_no_parameter(api_client, clean_queue):
    """Test that missing volume parameter returns error."""
    response = api_client.send('set_volume')
    assert response['status'] == 'error', "Should return error for missing volume"


def test_seek_relative(api_client, test_music_files, clean_queue):
    """Test relative seeking (forward/backward)."""
    # Add and play a track
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(1.0)  # Let track play for a bit

    # Get current time
    initial_status = api_client.send('get_status')
    initial_time = initial_status['data']['current_time']

    # Seek forward 5 seconds
    response = api_client.send('seek', offset=5.0)
    assert response['status'] == 'success', "Failed to seek forward"
    time.sleep(0.2)

    # Verify time increased
    new_status = api_client.send('get_status')
    new_time = new_status['data']['current_time']
    assert new_time > initial_time, "Time should have increased after seeking forward"

    # Seek backward 3 seconds
    response = api_client.send('seek', offset=-3.0)
    assert response['status'] == 'success', "Failed to seek backward"


def test_seek_to_position(api_client, test_music_files, clean_queue):
    """Test absolute position seeking."""
    # Add and play a track
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Seek to 10 seconds
    response = api_client.send('seek_to_position', position=10.0)
    assert response['status'] == 'success', "Failed to seek to position"
    assert response['position'] == 10.0, "Should report position as 10.0"
    time.sleep(0.2)

    # Verify position via status (allow some tolerance)
    status = api_client.send('get_status')
    current_time = status['data']['current_time']
    assert 9.0 <= current_time <= 11.0, f"Time should be around 10s, got {current_time}"


def test_seek_no_position(api_client, clean_queue):
    """Test that missing position parameter returns error."""
    response = api_client.send('seek_to_position')
    assert response['status'] == 'error', "Should return error for missing position"


def test_toggle_loop(api_client, clean_queue):
    """Test toggling loop mode."""
    # Get initial loop state
    initial_status = api_client.send('get_status')
    initial_loop = initial_status['data']['loop_enabled']

    # Toggle loop
    response = api_client.send('toggle_loop')
    assert response['status'] == 'success', "Failed to toggle loop"
    assert response['loop_enabled'] != initial_loop, "Loop state should have changed"

    # Verify via status
    new_status = api_client.send('get_status')
    assert new_status['data']['loop_enabled'] != initial_loop, "Loop state should be toggled"

    # Toggle back
    response = api_client.send('toggle_loop')
    assert response['status'] == 'success', "Failed to toggle loop back"
    assert response['loop_enabled'] == initial_loop, "Loop should be back to initial state"


def test_toggle_shuffle(api_client, clean_queue):
    """Test toggling shuffle mode."""
    # Get initial shuffle state
    initial_status = api_client.send('get_status')
    initial_shuffle = initial_status['data']['shuffle_enabled']

    # Toggle shuffle
    response = api_client.send('toggle_shuffle')
    assert response['status'] == 'success', "Failed to toggle shuffle"
    assert response['shuffle_enabled'] != initial_shuffle, "Shuffle state should have changed"

    # Verify via status
    new_status = api_client.send('get_status')
    assert new_status['data']['shuffle_enabled'] != initial_shuffle, "Shuffle state should be toggled"

    # Toggle back
    response = api_client.send('toggle_shuffle')
    assert response['status'] == 'success', "Failed to toggle shuffle back"
    assert response['shuffle_enabled'] == initial_shuffle, "Shuffle should be back to initial state"


def test_toggle_favorite(api_client, test_music_files, clean_queue):
    """Test toggling favorite status of current track."""
    # Add and play a track
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Toggle favorite
    response = api_client.send('toggle_favorite')
    assert response['status'] == 'success', "Failed to toggle favorite"

    # Toggle again (to unfavorite)
    response = api_client.send('toggle_favorite')
    assert response['status'] == 'success', "Failed to toggle favorite back"


def test_media_key_play_pause(api_client, test_music_files, clean_queue):
    """Test media key simulation for play/pause."""
    # Add a track
    api_client.send('add_to_queue', files=[test_music_files[0]])

    # Simulate play_pause media key
    response = api_client.send('media_key', key='play_pause')
    assert response['status'] == 'success', "Failed to simulate play_pause media key"
    assert response['key'] == 'play_pause', "Should report the key pressed"
    time.sleep(TEST_TIMEOUT)

    # Verify playing
    status = api_client.send('get_status')
    assert status['data']['is_playing'] is True, "Track should be playing after media key"


def test_media_key_next(api_client, test_music_files, clean_queue):
    """Test media key simulation for next track."""
    # Add multiple tracks and play
    api_client.send('add_to_queue', files=test_music_files[:3])
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Get initial track
    initial_status = api_client.send('get_status')
    initial_track = initial_status['data'].get('current_track', {}).get('filepath')

    # Simulate next media key
    response = api_client.send('media_key', key='next')
    assert response['status'] == 'success', "Failed to simulate next media key"
    time.sleep(TEST_TIMEOUT)

    # Verify track changed
    new_status = api_client.send('get_status')
    new_track = new_status['data'].get('current_track', {}).get('filepath')
    assert new_track != initial_track, "Track should have changed"


@pytest.mark.order(index=-4, after="test_stress_test_100_rapid_next_operations")
def test_media_key_previous(api_client, test_music_files, clean_queue):
    """Test media key simulation for previous track."""
    # Add multiple tracks, play, then go to second track
    api_client.send('add_to_queue', files=test_music_files[:3])
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)
    api_client.send('next')
    time.sleep(TEST_TIMEOUT)

    # Simulate previous media key
    response = api_client.send('media_key', key='previous')
    assert response['status'] == 'success', "Failed to simulate previous media key"


@pytest.mark.order(index=-3, after="test_media_key_previous")
def test_media_key_invalid(api_client, clean_queue):
    """Test that invalid media key returns error."""
    response = api_client.send('media_key', key='invalid_key')
    assert response['status'] == 'error', "Should return error for invalid key"
    assert 'invalid key' in response.get('message', '').lower(), "Error should mention invalid key"


@pytest.mark.order(index=-2, after="test_media_key_invalid")
def test_media_key_no_parameter(api_client, clean_queue):
    """Test that missing key parameter returns error."""
    response = api_client.send('media_key')
    assert response['status'] == 'error', "Should return error for missing key"
