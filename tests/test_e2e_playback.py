"""E2E Playback Tests - Tests requiring real VLC seeking behavior."""

import pytest
import time
from config import TEST_TIMEOUT


@pytest.mark.slow
def test_progress_seeking_stability(api_client, test_music_files, clean_queue):
    """Test that seeking progress doesn't jump backward after manual seeks."""
    if not test_music_files:
        pytest.skip("No test music files available")

    response = api_client.send('add_to_queue', files=[test_music_files[0]])
    assert response['status'] == 'success'

    response = api_client.send('play')
    assert response['status'] == 'success'
    time.sleep(TEST_TIMEOUT)

    status = api_client.send('get_status')
    assert status['status'] == 'success'
    assert status['data']['is_playing'] is True

    seek_positions = [10.0, 20.0, 30.0, 15.0, 25.0]

    for target_position in seek_positions:
        response = api_client.send('seek_to_position', position=target_position, timeout=2.0)
        assert response['status'] == 'success', f"Failed to seek to {target_position}s"

        time.sleep(0.6)

        status = api_client.send('get_status')
        assert status['status'] == 'success'

        current_time = status['data']['current_time']
        position_diff = abs(current_time - target_position)
        assert position_diff <= 1.5, f"Position jumped after seek! Target: {target_position}s, Actual: {current_time}s"

    rapid_positions = [40.0, 45.0, 50.0]
    for target_position in rapid_positions:
        response = api_client.send('seek_to_position', position=target_position, timeout=2.0)
        assert response['status'] == 'success'
        time.sleep(0.2)

    time.sleep(0.6)
    final_status = api_client.send('get_status')
    assert final_status['status'] == 'success'
    final_time = final_status['data']['current_time']

    assert abs(final_time - rapid_positions[-1]) <= 1.5, (
        f"Final position after rapid seeks incorrect! Expected ~{rapid_positions[-1]}s, Got: {final_time}s"
    )

    duration_status = api_client.send('get_status')
    assert duration_status['status'] == 'success'
    track_duration = duration_status['data']['duration']

    if track_duration > 10:
        near_end_position = track_duration - 5.0
        response = api_client.send('seek_to_position', position=near_end_position, timeout=2.0)
        assert response['status'] == 'success'

        time.sleep(0.6)

        end_status = api_client.send('get_status')
        assert end_status['status'] == 'success'
        end_time = end_status['data']['current_time']

        end_position_diff = abs(end_time - near_end_position)
        assert end_position_diff <= 1.5, (
            f"Position jumped when seeking near end! Target: {near_end_position}s, Actual: {end_time}s"
        )
