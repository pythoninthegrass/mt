import pytest
import time
from config import TEST_TIMEOUT


def test_switch_to_library_view(api_client):
    """Test switching to library view."""
    response = api_client.send('switch_view', view='library')
    assert response['status'] == 'success', "Failed to switch to library view"
    assert response['view'] == 'Library', "Should report Library view"


def test_switch_to_queue_view(api_client):
    """Test switching to queue view."""
    response = api_client.send('switch_view', view='queue')
    assert response['status'] == 'success', "Failed to switch to queue view"
    assert response['view'] == 'Queue', "Should report Queue view"


def test_switch_to_liked_songs(api_client):
    """Test switching to liked songs view."""
    response = api_client.send('switch_view', view='liked')
    assert response['status'] == 'success', "Failed to switch to liked songs"
    assert response['view'] == 'Liked Songs', "Should report Liked Songs view"


def test_switch_to_top25_view(api_client):
    """Test switching to top 25 most played view."""
    response = api_client.send('switch_view', view='top25')
    assert response['status'] == 'success', "Failed to switch to top 25 view"
    assert response['view'] == 'Top 25 Most Played', "Should report Top 25 Most Played view"


def test_switch_to_invalid_view(api_client):
    """Test switching to invalid view returns error."""
    response = api_client.send('switch_view', view='invalid_view')
    assert response['status'] == 'error', "Should return error for invalid view"
    assert 'unknown view' in response.get('message', '').lower(), "Error should mention unknown view"
    assert 'available_views' in response, "Should include list of available views"


def test_switch_view_no_parameter(api_client):
    """Test switch_view with no view parameter returns error."""
    response = api_client.send('switch_view')
    assert response['status'] == 'error', "Should return error for missing view parameter"


def test_view_switching_sequence(api_client):
    """Test switching between multiple views in sequence."""
    # Switch to each view in sequence
    views = ['library', 'queue', 'liked', 'top25']

    for view in views:
        response = api_client.send('switch_view', view=view)
        assert response['status'] == 'success', f"Failed to switch to {view} view"

    # Switch back to library
    response = api_client.send('switch_view', view='library')
    assert response['status'] == 'success', "Failed to switch back to library"


def test_select_queue_item_in_queue_view(api_client, test_music_files, clean_queue):
    """Test selecting an item in queue view."""
    # Switch to queue view
    api_client.send('switch_view', view='queue')

    # Add tracks to queue
    api_client.send('add_to_queue', files=test_music_files[:3])

    # Select item at index 1
    response = api_client.send('select_queue_item', index=1)
    assert response['status'] == 'success', "Failed to select queue item"


def test_select_queue_item_invalid_index(api_client, test_music_files, clean_queue):
    """Test selecting queue item with invalid index."""
    # Add only 2 tracks
    api_client.send('add_to_queue', files=test_music_files[:2])

    # Try to select invalid index
    response = api_client.send('select_queue_item', index=10)
    assert response['status'] == 'error', "Should return error for invalid index"


def test_library_and_queue_interaction(api_client, test_music_files, clean_queue):
    """Test interaction between library view and queue."""
    # Start in library view
    api_client.send('switch_view', view='library')

    # Get library items
    library = api_client.send('get_library')
    assert library['status'] == 'success', "Failed to get library"

    # Add tracks to queue
    api_client.send('add_to_queue', files=test_music_files[:2])

    # Switch to queue view
    response = api_client.send('switch_view', view='queue')
    assert response['status'] == 'success', "Failed to switch to queue"

    # Verify queue has items
    queue = api_client.send('get_queue')
    assert queue['count'] == 2, "Queue should have 2 items"

    # Switch back to library
    response = api_client.send('switch_view', view='library')
    assert response['status'] == 'success', "Failed to switch back to library"


def test_play_from_library_selection(api_client, test_music_files, clean_queue):
    """Test selecting and playing from library view."""
    # Switch to library and select item
    api_client.send('switch_view', view='library')

    # Add a track to queue first
    api_client.send('add_to_queue', files=[test_music_files[0]])

    # Play the track
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Verify playback
    status = api_client.send('get_status')
    assert status['data']['is_playing'] is True, "Track should be playing"


def test_view_state_preserved(api_client, test_music_files, clean_queue):
    """Test that view states are preserved when switching."""
    # Add tracks to queue
    api_client.send('add_to_queue', files=test_music_files[:3])

    # Switch to queue view
    api_client.send('switch_view', view='queue')

    # Get queue count
    queue1 = api_client.send('get_queue')
    count1 = queue1['count']

    # Switch to library
    api_client.send('switch_view', view='library')

    # Switch back to queue
    api_client.send('switch_view', view='queue')

    # Queue should still have same items
    queue2 = api_client.send('get_queue')
    count2 = queue2['count']

    assert count2 == count1, "Queue count should be preserved across view switches"
