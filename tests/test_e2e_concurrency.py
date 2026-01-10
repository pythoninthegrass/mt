"""Concurrent operation and race condition tests requiring real VLC."""

import pytest
import time
from config import TEST_TIMEOUT


@pytest.mark.order("last")
@pytest.mark.slow
def test_rapid_next_operations(api_client, test_music_files, clean_queue):
    """Test rapid consecutive next() calls don't cause race conditions."""
    if not test_music_files or len(test_music_files) < 10:
        pytest.skip("Need at least 10 test music files")

    api_client.send('add_to_queue', files=test_music_files[:10])
    api_client.send('toggle_shuffle')
    api_client.send('toggle_loop')
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    for i in range(20):
        response = api_client.send('next')
        assert response['status'] == 'success', f"Next operation {i + 1} failed"
        time.sleep(0.05)

    time.sleep(0.2)

    status = api_client.send('get_status')
    assert status['status'] == 'success'
    assert status['data']['is_playing'] is True

    queue = api_client.send('get_queue')
    assert queue['status'] == 'success'
    assert queue['count'] == 10


@pytest.mark.order("last")
@pytest.mark.slow
def test_stress_test_100_rapid_next_operations(api_client, test_music_files, clean_queue):
    """Stress test: 100 rapid next() operations with shuffle+loop."""
    if not test_music_files or len(test_music_files) < 10:
        pytest.skip("Need at least 10 test music files")

    api_client.send('add_to_queue', files=test_music_files[:10])
    api_client.send('toggle_shuffle')
    api_client.send('toggle_loop')
    api_client.send('play')
    time.sleep(TEST_TIMEOUT)

    success_count = 0
    for i in range(100):
        response = api_client.send('next')
        if response['status'] == 'success':
            success_count += 1
        time.sleep(0.01)

    assert success_count == 100, f"Only {success_count}/100 next operations succeeded"

    status = api_client.send('get_status')
    assert status['status'] == 'success'
    assert status['data']['is_playing'] is True

    queue = api_client.send('get_queue')
    assert queue['status'] == 'success'
    assert queue['count'] == 10

    time.sleep(0.5)
