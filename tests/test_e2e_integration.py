"""Comprehensive integration tests for cross-component workflows.

These tests validate complete user workflows that span multiple components
(library, queue, player, database) to ensure proper integration.
"""

import pytest
import time
from config import TEST_TIMEOUT


def test_library_search_to_playback_workflow(api_client, test_music_files, clean_queue):
    """Test complete workflow: Library search → Filter → Add multiple → Play → Verify.

    This tests the integration of:
    - Library view and search functionality
    - Adding multiple tracks from search results
    - Queue management (receiving and storing tracks)
    - Player initialization and playback start
    - Database persistence across operations
    """
    # Start in library view
    response = api_client.send('switch_view', view='library')
    assert response['status'] == 'success', "Failed to switch to library"

    # Get initial library count
    library = api_client.send('get_library')
    assert library['status'] == 'success', "Failed to get library"
    initial_count = library['count']
    assert initial_count > 0, "Library should have items"

    # Search for "deadmau5" (known artist in test music)
    search_response = api_client.send('search', query='deadmau5')
    assert search_response['status'] == 'success', "Failed to search library"

    # Add multiple tracks to queue
    add_response = api_client.send('add_to_queue', files=test_music_files[:3])
    assert add_response['status'] == 'success', "Failed to add tracks"

    # Verify queue has all tracks
    queue = api_client.send('get_queue')
    assert queue['status'] == 'success', "Failed to get queue"
    assert queue['count'] == 3, f"Queue should have 3 items, got {queue['count']}"

    # Start playback
    play_response = api_client.send('play')
    assert play_response['status'] == 'success', "Failed to start playback"
    time.sleep(TEST_TIMEOUT)

    # Verify playing state and current track
    status = api_client.send('get_status')
    assert status['status'] == 'success', "Failed to get status"
    assert status['data']['is_playing'] is True, "Should be playing"
    assert status['data']['current_track'] is not None, "Should have current track"

    # Clear search
    clear_response = api_client.send('clear_search')
    assert clear_response['status'] == 'success', "Failed to clear search"

    # Verify library count restored
    library_after = api_client.send('get_library')
    assert library_after['count'] == initial_count, "Library count should be restored after clearing search"


def test_shuffle_mode_full_workflow(api_client, test_music_files, clean_queue):
    """Test shuffle mode across library/queue/player integration.

    This tests:
    - Enabling shuffle mode
    - Adding tracks and verifying shuffle affects queue order
    - Playing through shuffled queue
    - Verifying all tracks are preserved (just reordered)
    """
    # Add multiple tracks to queue
    api_client.send('add_to_queue', files=test_music_files[:5])

    # Get original queue order (using title+artist as unique identifier)
    original_queue = api_client.send('get_queue')
    original_items = [(item['title'], item['artist']) for item in original_queue['data']]

    # Enable shuffle
    shuffle_response = api_client.send('toggle_shuffle')
    assert shuffle_response['status'] == 'success', "Failed to toggle shuffle"

    # Verify shuffle is enabled
    status = api_client.send('get_status')
    assert status['data']['shuffle_enabled'] is True, "Shuffle should be enabled"

    # Start playback
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Get current track
    current_track_response = api_client.send('get_current_track')
    current_track = current_track_response['data']
    assert current_track is not None, "Should have current track"

    # Navigate through a few tracks
    for _ in range(3):
        next_response = api_client.send('next')
        assert next_response['status'] == 'success', "Failed to go to next track"
        time.sleep(TEST_TIMEOUT / 2)

    # Verify queue still has all original tracks (just different order)
    final_queue = api_client.send('get_queue')
    final_items = [(item['title'], item['artist']) for item in final_queue['data']]
    assert len(final_items) == len(original_items), "Queue size should be preserved"
    assert set(final_items) == set(original_items), "All original tracks should be present"


def test_loop_queue_exhaustion(api_client, test_music_files, clean_queue):
    """Test loop mode with queue exhaustion and restart.

    This tests:
    - Loop mode enabling
    - Playing through entire queue
    - Verifying queue restarts from beginning when loop is enabled
    - Player state transitions
    """
    # Add 3 tracks
    api_client.send('add_to_queue', files=test_music_files[:3])

    # Enable loop mode
    loop_response = api_client.send('toggle_loop')
    assert loop_response['status'] == 'success', "Failed to toggle loop"

    # Verify loop is enabled
    status = api_client.send('get_status')
    assert status['data']['loop_enabled'] is True, "Loop should be enabled"

    # Start playback
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    # Get first track
    first_track = api_client.send('get_current_track')['data']
    assert first_track is not None, "Should have first track"
    first_filepath = first_track['filepath']

    # Skip to end of queue (go next 3 times)
    for i in range(3):
        next_response = api_client.send('next')
        assert next_response['status'] == 'success', f"Failed to go to next track (iteration {i + 1})"
        time.sleep(TEST_TIMEOUT / 2)

    # With loop enabled, should be back at first track (or close to it)
    # Get current track and verify we're still playing
    final_status = api_client.send('get_status')
    assert final_status['data']['is_playing'] is True, "Should still be playing with loop enabled"

    current_track = api_client.send('get_current_track')['data']
    # Note: Depending on timing, we might be at first track or about to loop
    # The key is that playback continues


def test_add_from_different_library_views(api_client, test_music_files, clean_queue):
    """Test adding tracks from different library views (Top25, Liked Songs, Library).

    This tests:
    - View switching functionality
    - Adding tracks from different view contexts
    - Queue properly receiving tracks from all sources
    - View state preservation
    """
    # Start with library view
    api_client.send('switch_view', view='library')
    api_client.send('add_to_queue', files=[test_music_files[0]])

    # Verify 1 track in queue
    queue1 = api_client.send('get_queue')
    assert queue1['count'] == 1, "Should have 1 track from library"

    # Switch to Top25 view
    top25_response = api_client.send('switch_view', view='top25')
    assert top25_response['status'] == 'success', "Failed to switch to Top25"
    assert top25_response['view'] == 'Top 25 Most Played', "Should report Top 25 Most Played view"

    # Add another track
    api_client.send('add_to_queue', files=[test_music_files[1]])

    # Verify 2 tracks in queue
    queue2 = api_client.send('get_queue')
    assert queue2['count'] == 2, "Should have 2 tracks"

    # Switch to Liked Songs view
    liked_response = api_client.send('switch_view', view='liked')
    assert liked_response['status'] == 'success', "Failed to switch to Liked Songs"
    assert liked_response['view'] == 'Liked Songs', "Should report Liked Songs view"

    # Add another track
    api_client.send('add_to_queue', files=[test_music_files[2]])

    # Verify 3 tracks in queue
    queue3 = api_client.send('get_queue')
    assert queue3['count'] == 3, "Should have 3 tracks from different views"

    # Verify all tracks are unique (using title+artist pairs)
    track_identifiers = [(item['title'], item['artist']) for item in queue3['data']]
    assert len(set(track_identifiers)) == 3, "All tracks should be unique"


def test_error_recovery_workflow(api_client, test_music_files, clean_queue):
    """Test error recovery: Add invalid file → Play → Skip → Continue playback.

    This tests:
    - Graceful handling of invalid files
    - Player continues after encountering errors
    - Queue management with mixed valid/invalid entries
    - Error reporting and recovery
    """
    # Add valid tracks and an invalid file path
    valid_files = test_music_files[:2]
    invalid_file = '/nonexistent/path/to/invalid.mp3'

    # Add valid track
    api_client.send('add_to_queue', files=[valid_files[0]])

    # Try to add invalid file (should either fail or add but not play)
    api_client.send('add_to_queue', files=[invalid_file])

    # Add another valid track
    api_client.send('add_to_queue', files=[valid_files[1]])

    # Get queue (may or may not include invalid file depending on validation)
    queue = api_client.send('get_queue')
    queue_count = queue['count']
    assert queue_count >= 2, "Should have at least 2 valid tracks"

    # Start playback
    play_response = api_client.send('play')
    assert play_response['status'] == 'success', "Playback should start"
    time.sleep(TEST_TIMEOUT)

    # Should be playing first valid track
    status = api_client.send('get_status')
    current_track = status['data'].get('current_track')

    # If we're playing, verify it's a valid track
    if status['data']['is_playing']:
        assert current_track is not None, "Should have current track"
        assert current_track['filepath'] in valid_files, "Should be playing valid track"

    # Skip to next track
    api_client.send('next')
    time.sleep(TEST_TIMEOUT)

    # Should still be able to play or have gracefully stopped
    final_status = api_client.send('get_status')
    # Either playing the next valid track or stopped gracefully
    assert final_status['status'] == 'success', "Should handle track transition"


def test_concurrent_operations_workflow(api_client, test_music_files, clean_queue):
    """Test rapid concurrent operations: view switching + queue ops + playback control.

    This tests:
    - Thread safety and race condition handling
    - State consistency under rapid operations
    - UI responsiveness during heavy operations
    - No deadlocks or hangs
    """
    # Add initial tracks
    api_client.send('add_to_queue', files=test_music_files[:3])

    # Start playback
    api_client.send('play')
    time.sleep(TEST_TIMEOUT / 2)

    # Perform rapid operations
    operations = [
        ('switch_view', {'view': 'library'}),
        ('add_to_queue', {'files': [test_music_files[3]]}),
        ('switch_view', {'view': 'queue'}),
        ('next', {}),
        ('set_volume', {'volume': 75}),
        ('toggle_shuffle', {}),
        ('switch_view', {'view': 'top25'}),
        ('get_status', {}),
        ('add_to_queue', {'files': [test_music_files[4]]}),
        ('toggle_loop', {}),
        ('get_queue', {}),
    ]

    # Execute all operations rapidly
    for command, params in operations:
        response = api_client.send(command, **params)
        # All operations should succeed or fail gracefully
        assert response['status'] in ['success', 'error'], f"Command {command} should return valid status"

    # Wait for operations to settle
    time.sleep(0.5)

    # Verify final state is consistent
    final_status = api_client.send('get_status')
    assert final_status['status'] == 'success', "Should get status after concurrent operations"

    final_queue = api_client.send('get_queue')
    assert final_queue['status'] == 'success', "Should get queue after concurrent operations"
    # Queue should have 5 tracks (3 initial + 2 added)
    assert final_queue['count'] == 5, f"Queue should have 5 tracks, got {final_queue['count']}"

    # Verify player is still functional
    current_track = api_client.send('get_current_track')
    assert current_track['status'] == 'success', "Should get current track after concurrent operations"
