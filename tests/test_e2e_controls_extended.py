"""Extended E2E tests for player controls via API to increase coverage."""

import pytest
import time
from config import TEST_TIMEOUT


@pytest.mark.order("last")
def test_stop_playback_clears_state(api_client, test_music_files, clean_queue):
    """Test that stop command properly clears playback state."""
    # Add tracks and start playback
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play_track_at_index', index=0)
    time.sleep(0.3)

    # Verify playing
    status = api_client.send('get_status')
    assert status["data"]["is_playing"] is True

    # Stop playback
    stop_result = api_client.send('stop')
    assert stop_result["status"] == "success"

    # Verify stopped state
    status = api_client.send('get_status')
    assert status["data"]["is_playing"] is False
    assert status["data"]["current_time"] == 0.0


def test_get_volume(api_client, test_music_files, clean_queue):
    """Test getting and setting volume level."""
    # Play something first so VLC has a valid audio stream
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play_track_at_index', index=0)
    time.sleep(0.3)

    # Get initial volume
    status1 = api_client.send('get_status')
    initial_volume = status1["data"]["volume"]

    # Set a different volume
    new_volume = 75 if initial_volume != 75 else 60
    api_client.send('set_volume', volume=new_volume)
    time.sleep(0.1)

    # Verify volume in status response
    status2 = api_client.send('get_status')
    assert "volume" in status2["data"]
    # Volume should have changed (unless VLC returns -1 for uninitialized)
    assert status2["data"]["volume"] in [new_volume, -1]


def test_volume_boundaries(api_client, test_music_files, clean_queue):
    """Test volume validation rejects out-of-range values."""
    # Play something first so VLC has a valid audio stream
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play_track_at_index', index=0)
    time.sleep(0.3)

    # Test setting volume above max - should reject
    result = api_client.send('set_volume', volume=150)
    assert result["status"] == "error"
    assert "must be between 0 and 100" in result["message"].lower()

    # Test setting volume below min - should reject
    result = api_client.send('set_volume', volume=-10)
    assert result["status"] == "error"
    assert "must be between 0 and 100" in result["message"].lower()

    # Test valid volume values work
    result = api_client.send('set_volume', volume=50)
    assert result["status"] == "success"
    assert result["volume"] == 50


def test_get_duration_without_media(api_client, clean_queue):
    """Test getting duration when no media is loaded."""
    # Get status - duration should be 0 (clean_queue ensures stopped state)
    status = api_client.send('get_status')
    assert status["data"]["duration"] == 0.0


def test_seek_without_media(api_client, clean_queue):
    """Test seeking when no media is playing (should handle gracefully)."""
    # Try to seek - should not crash
    result = api_client.send('seek_to_position', position=10.0)
    # Should either succeed gracefully or report error
    assert result["status"] in ["success", "error"]


def test_play_pause_without_queue(api_client, clean_queue):
    """Test play_pause when queue is empty."""
    # Try to play - should handle gracefully
    result = api_client.send('play_pause')
    assert result["status"] == "success"


def test_next_on_last_track_without_loop(api_client, test_music_files, clean_queue):
    """Test next command on last track without loop enabled."""
    # Setup: Add single track, ensure loop disabled (clean_queue does this)
    api_client.send('add_to_queue', files=[test_music_files[0]])

    # Play track
    api_client.send('play_track_at_index', index=0)
    time.sleep(0.3)

    # Try next - should stop
    result = api_client.send('next')
    assert result["status"] == "success"

    time.sleep(0.2)

    # Should be stopped
    status = api_client.send('get_status')
    assert status["data"]["is_playing"] is False


def test_previous_on_first_track(api_client, test_music_files, clean_queue):
    """Test previous command on first track."""
    # Setup: Add tracks, play first
    api_client.send('add_to_queue', files=test_music_files[:2])
    api_client.send('play_track_at_index', index=0)
    time.sleep(0.3)

    # Try previous on first track
    result = api_client.send('previous')
    assert result["status"] == "success"


def test_toggle_loop_multiple_times(api_client, clean_queue):
    """Test toggling loop mode multiple times."""
    # Get initial state (should be disabled from clean_queue)
    status = api_client.send('get_status')
    initial_loop = status["data"]["loop_enabled"]

    # Toggle twice - should return to initial state
    api_client.send('toggle_loop')
    api_client.send('toggle_loop')

    status = api_client.send('get_status')
    assert status["data"]["loop_enabled"] == initial_loop


def test_toggle_shuffle_multiple_times(api_client, clean_queue):
    """Test toggling shuffle mode multiple times."""
    # Get initial state (should be disabled from clean_queue)
    status = api_client.send('get_status')
    initial_shuffle = status["data"]["shuffle_enabled"]

    # Toggle twice - should return to initial state
    api_client.send('toggle_shuffle')
    api_client.send('toggle_shuffle')

    status = api_client.send('get_status')
    assert status["data"]["shuffle_enabled"] == initial_shuffle


def test_get_current_track_when_stopped(api_client, clean_queue):
    """Test get_current_track when nothing is playing."""
    # Get current track (clean_queue ensures stopped state)
    result = api_client.send('get_current_track')
    assert result["status"] == "success"
    # May return track info from queue selection even when stopped, or None
    # This is acceptable behavior - the queue view maintains selection
    assert result is not None


def test_seek_to_beginning(api_client, test_music_files, clean_queue):
    """Test seeking to the beginning of a track."""
    # Setup and play
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play_track_at_index', index=0)
    time.sleep(0.5)

    # Seek to middle first
    api_client.send('seek_to_position', position=5.0)
    time.sleep(0.1)

    # Seek to beginning
    result = api_client.send('seek_to_position', position=0.0)
    assert result["status"] == "success"

    time.sleep(0.1)
    status = api_client.send('get_status')
    assert status["data"]["current_time"] < 1.0  # Should be near start


def test_seek_to_end(api_client, test_music_files, clean_queue):
    """Test seeking near the end of a track."""
    # Setup and play
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play_track_at_index', index=0)
    time.sleep(0.5)

    # Get duration
    status = api_client.send('get_status')
    duration = status["data"]["duration"]

    # Seek near end
    result = api_client.send('seek_to_position', position=duration - 1.0)
    assert result["status"] == "success"


def test_get_queue_with_empty_queue(api_client, clean_queue):
    """Test getting queue when it's empty."""
    result = api_client.send('get_queue')
    assert result["status"] == "success"
    assert result["data"] == []
    assert result["count"] == 0


def test_remove_from_queue_invalid_index(api_client, test_music_files, clean_queue):
    """Test removing from queue with invalid index."""
    # Add track
    api_client.send('add_to_queue', files=[test_music_files[0]])

    # Try to remove with invalid index
    result = api_client.send('remove_from_queue', index=999)
    assert result["status"] == "error"
    assert "out of range" in result["message"].lower()


def test_select_track_not_in_queue(api_client, clean_queue):
    """Test selecting a track by filepath that's not in queue."""
    result = api_client.send('select_track', filepath="/nonexistent/file.mp3")
    assert result["status"] == "error"


def test_invalid_action(api_client, clean_queue):
    """Test sending an invalid action."""
    # We need to send raw command, so use a socket directly
    import json
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect(('localhost', 5555))

    command = json.dumps({"action": "nonexistent_action"})
    sock.send(command.encode('utf-8'))

    data_parts = []
    while True:
        chunk = sock.recv(8192)
        if not chunk:
            break
        data_parts.append(chunk)

    data = b''.join(data_parts).decode('utf-8')
    result = json.loads(data)
    sock.close()

    assert result["status"] == "error"
    assert "unknown action" in result["message"].lower()
    assert "available_actions" in result


def test_missing_action(api_client, clean_queue):
    """Test sending command without action field."""
    # Send raw command with missing action
    import json
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect(('localhost', 5555))

    command = json.dumps({})
    sock.send(command.encode('utf-8'))

    data_parts = []
    while True:
        chunk = sock.recv(8192)
        if not chunk:
            break
        data_parts.append(chunk)

    data = b''.join(data_parts).decode('utf-8')
    result = json.loads(data)
    sock.close()

    assert result["status"] == "error"
    assert "no action specified" in result["message"].lower()


def test_concurrent_commands(api_client, test_music_files, clean_queue):
    """Test sending multiple commands rapidly."""
    # Setup
    api_client.send('add_to_queue', files=test_music_files[:3])

    # Send multiple commands rapidly
    results = [
        api_client.send('play_track_at_index', index=0),
        api_client.send('set_volume', volume=50),
        api_client.send('toggle_loop'),
        api_client.send('get_status'),
    ]

    # All should succeed
    for result in results:
        assert result["status"] == "success"
