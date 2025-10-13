import pytest
import time
from config import TEST_TIMEOUT


def test_add_single_track(api_client, test_music_files, clean_queue):
    """Test adding a single track to the queue."""
    # Add one track
    response = api_client.send('add_to_queue', files=[test_music_files[0]])
    assert response['status'] == 'success', "Failed to add track"
    assert response['added'] == 1, "Should report 1 track added"

    # Verify queue has the track
    queue = api_client.send('get_queue')
    assert queue['status'] == 'success', "Failed to get queue"
    assert queue['count'] == 1, "Queue should have 1 track"


def test_add_multiple_tracks(api_client, test_music_files, clean_queue):
    """Test adding multiple tracks at once."""
    # Add three tracks
    tracks_to_add = test_music_files[:3]
    response = api_client.send('add_to_queue', files=tracks_to_add)
    assert response['status'] == 'success', "Failed to add tracks"
    assert response['added'] == 3, "Should report 3 tracks added"

    # Verify queue has all tracks
    queue = api_client.send('get_queue')
    assert queue['status'] == 'success', "Failed to get queue"
    assert queue['count'] == 3, "Queue should have 3 tracks"


def test_get_queue(api_client, test_music_files, clean_queue):
    """Test getting queue contents."""
    # Add tracks
    api_client.send('add_to_queue', files=test_music_files[:2])

    # Get queue
    response = api_client.send('get_queue')
    assert response['status'] == 'success', "Failed to get queue"
    assert 'data' in response, "Response should include data"
    assert 'count' in response, "Response should include count"

    # Verify queue structure
    queue_items = response['data']
    assert len(queue_items) == 2, "Should have 2 items"

    # Check first item structure
    first_item = queue_items[0]
    assert 'index' in first_item, "Item should have index"
    assert 'title' in first_item, "Item should have title"
    assert 'artist' in first_item, "Item should have artist"
    assert 'album' in first_item, "Item should have album"


def test_remove_from_queue(api_client, test_music_files, clean_queue):
    """Test removing a track from the queue by index."""
    # Add three tracks
    api_client.send('add_to_queue', files=test_music_files[:3])

    # Get initial queue
    initial_queue = api_client.send('get_queue')
    assert initial_queue['count'] == 3, "Should start with 3 tracks"

    # Remove the middle track (index 1)
    response = api_client.send('remove_from_queue', index=1)
    assert response['status'] == 'success', "Failed to remove track"

    # Verify queue now has 2 tracks
    updated_queue = api_client.send('get_queue')
    assert updated_queue['count'] == 2, "Queue should have 2 tracks after removal"


def test_clear_queue(api_client, test_music_files, clean_queue):
    """Test clearing the entire queue."""
    # Add tracks
    api_client.send('add_to_queue', files=test_music_files[:5])

    # Verify tracks were added
    queue = api_client.send('get_queue')
    assert queue['count'] == 5, "Should have 5 tracks before clearing"

    # Clear queue
    response = api_client.send('clear_queue')
    assert response['status'] == 'success', "Failed to clear queue"

    # Verify queue is empty
    empty_queue = api_client.send('get_queue')
    assert empty_queue['count'] == 0, "Queue should be empty after clearing"


def test_play_track_at_index(api_client, test_music_files, clean_queue):
    """Test playing a track at a specific queue index."""
    # Add multiple tracks
    api_client.send('add_to_queue', files=test_music_files[:3])

    # Play track at index 1 (second track)
    response = api_client.send('play_track_at_index', index=1)
    assert response['status'] == 'success', "Failed to play track at index"
    time.sleep(TEST_TIMEOUT)

    # Verify playback started
    status = api_client.send('get_status')
    assert status['data']['is_playing'] is True, "Track should be playing"

    # Verify the correct track is playing (second track)
    current_track = status['data'].get('current_track', {}).get('filepath')
    assert current_track == test_music_files[1], "Should be playing the second track"


def test_remove_invalid_index(api_client, test_music_files, clean_queue):
    """Test removing with invalid index returns error."""
    # Add only 2 tracks
    api_client.send('add_to_queue', files=test_music_files[:2])

    # Try to remove at invalid index
    response = api_client.send('remove_from_queue', index=10)
    assert response['status'] == 'error', "Should return error for invalid index"
    assert 'out of range' in response.get('message', '').lower(), "Error message should mention range"


def test_play_invalid_index(api_client, test_music_files, clean_queue):
    """Test playing at invalid index returns error."""
    # Add only 2 tracks
    api_client.send('add_to_queue', files=test_music_files[:2])

    # Try to play at invalid index
    response = api_client.send('play_track_at_index', index=10)
    assert response['status'] == 'error', "Should return error for invalid index"
    assert 'out of range' in response.get('message', '').lower(), "Error message should mention range"


def test_select_queue_item(api_client, test_music_files, clean_queue):
    """Test selecting an item in the queue view."""
    # Add tracks
    api_client.send('add_to_queue', files=test_music_files[:3])

    # Select item at index 1
    response = api_client.send('select_queue_item', index=1)
    assert response['status'] == 'success', "Failed to select queue item"


def test_add_no_files(api_client, clean_queue):
    """Test adding with no files returns appropriate response."""
    # Try to add empty list
    response = api_client.send('add_to_queue', files=[])
    assert response['status'] == 'error', "Should return error for empty file list"
    assert 'no files' in response.get('message', '').lower(), "Error should mention no files"
