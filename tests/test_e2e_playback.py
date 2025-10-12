"""End-to-end tests for playback controls via API."""

import pytest
import time


def test_play_pause_toggle(api_client, test_music_files, clean_queue):
    """Test play/pause toggle functionality."""
    # Add a track to the queue
    response = api_client.send('add_to_queue', files=[test_music_files[0]])
    assert response['status'] == 'success', "Failed to add track to queue"

    # Start playback
    response = api_client.send('play_pause')
    assert response['status'] == 'success', "Failed to toggle play"
    time.sleep(0.5)  # Allow VLC to initialize

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


def test_play_when_paused(api_client, test_music_files, clean_queue):
    """Test explicit play command when paused."""
    # Add a track to the queue
    api_client.send('add_to_queue', files=[test_music_files[0]])

    # Explicitly play
    response = api_client.send('play')
    assert response['status'] == 'success', "Failed to play"
    assert response['is_playing'] is True, "Should report playing state"
    time.sleep(0.5)

    # Verify playing state
    status = api_client.send('get_status')
    assert status['data']['is_playing'] is True, "Track should be playing"


def test_pause_when_playing(api_client, test_music_files, clean_queue):
    """Test explicit pause command when playing."""
    # Add and play a track
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(0.5)

    # Explicitly pause
    response = api_client.send('pause')
    assert response['status'] == 'success', "Failed to pause"
    assert response['is_playing'] is False, "Should report paused state"

    # Verify paused state
    status = api_client.send('get_status')
    assert status['data']['is_playing'] is False, "Track should be paused"


def test_next_track(api_client, test_music_files, clean_queue):
    """Test navigation to next track."""
    # Add multiple tracks
    api_client.send('add_to_queue', files=test_music_files[:3])

    # Play first track
    api_client.send('play')
    time.sleep(0.5)

    # Get initial track info
    initial_status = api_client.send('get_status')
    initial_track = initial_status['data'].get('current_track', {}).get('filepath')

    # Go to next track
    response = api_client.send('next')
    assert response['status'] == 'success', "Failed to go to next track"
    time.sleep(0.5)

    # Verify track changed
    new_status = api_client.send('get_status')
    new_track = new_status['data'].get('current_track', {}).get('filepath')
    assert new_track != initial_track, "Track should have changed"


def test_previous_track(api_client, test_music_files, clean_queue):
    """Test navigation to previous track."""
    # Add multiple tracks
    api_client.send('add_to_queue', files=test_music_files[:3])

    # Play first track, then go to second
    api_client.send('play')
    time.sleep(0.5)
    api_client.send('next')
    time.sleep(0.5)

    # Get current track
    current_status = api_client.send('get_status')
    current_track = current_status['data'].get('current_track', {}).get('filepath')

    # Go to previous track
    response = api_client.send('previous')
    assert response['status'] == 'success', "Failed to go to previous track"
    time.sleep(0.5)

    # Verify track changed
    new_status = api_client.send('get_status')
    new_track = new_status['data'].get('current_track', {}).get('filepath')
    assert new_track != current_track, "Track should have changed to previous"


def test_stop_playback(api_client, test_music_files, clean_queue):
    """Test stop command."""
    # Add and play a track
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(0.5)

    # Stop playback
    response = api_client.send('stop')
    assert response['status'] == 'success', "Failed to stop playback"

    # Verify stopped (should be not playing)
    status = api_client.send('get_status')
    assert status['data']['is_playing'] is False, "Track should be stopped"


def test_get_status(api_client, test_music_files, clean_queue):
    """Test status query returns valid information."""
    # Add and play a track
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(0.5)

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


def test_get_current_track(api_client, test_music_files, clean_queue):
    """Test getting current track information."""
    # Add and play a track
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(0.5)

    # Get current track
    response = api_client.send('get_current_track')
    assert response['status'] == 'success', "Failed to get current track"

    # Verify track data structure
    if response['data'] is not None:
        track = response['data']
        assert 'filepath' in track, "Track should include filepath"
        assert track['filepath'] == test_music_files[0], "Filepath should match added track"
