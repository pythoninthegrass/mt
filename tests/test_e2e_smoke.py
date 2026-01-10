"""E2E Smoke Tests - Fast critical path validation requiring real VLC/app."""

import pytest
import time
from config import TEST_TIMEOUT


def test_basic_playback_workflow(api_client, test_music_files, clean_queue):
    """Test the most critical user workflow: add track and play."""
    if not test_music_files:
        pytest.skip("No test music files available")

    response = api_client.send('add_to_queue', files=[test_music_files[0]])
    assert response['status'] == 'success'

    response = api_client.send('play_pause')
    assert response['status'] == 'success'
    time.sleep(TEST_TIMEOUT)

    status = api_client.send('get_status')
    assert status['status'] == 'success'
    assert status['data']['is_playing'] is True


def test_queue_operations(api_client, test_music_files, clean_queue):
    """Test basic queue add/clear operations."""
    if not test_music_files or len(test_music_files) < 3:
        pytest.skip("Need at least 3 test music files")

    response = api_client.send('add_to_queue', files=test_music_files[:3])
    assert response['status'] == 'success'

    queue_response = api_client.send('get_queue')
    assert queue_response['count'] == 3

    response = api_client.send('clear_queue')
    assert response['status'] == 'success'

    queue_response = api_client.send('get_queue')
    assert queue_response['count'] == 0


def test_stop_clears_playback(api_client, test_music_files, clean_queue):
    """Test that stop clears playback state."""
    if not test_music_files:
        pytest.skip("No test music files available")

    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    status = api_client.send('get_status')
    assert status['data']['is_playing'] is True

    response = api_client.send('stop')
    assert response['status'] == 'success'

    status = api_client.send('get_status')
    assert status['data']['is_playing'] is False


def test_seek_position(api_client, test_music_files, clean_queue):
    """Test seeking to a specific position."""
    if not test_music_files:
        pytest.skip("No test music files available")

    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    response = api_client.send('seek_to_position', position=10.0)
    assert response['status'] == 'success'
    time.sleep(0.2)

    status = api_client.send('get_status')
    current_time = status['data'].get('current_time', 0)
    assert 9.0 <= current_time <= 11.0, f"Expected ~10s, got {current_time}s"
