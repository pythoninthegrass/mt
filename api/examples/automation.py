#!/usr/bin/env python

import json
import time
from client import MtApiClient


def test_playback_controls(client: MtApiClient):
    """Test all playback controls."""
    print("Testing Playback Controls")
    print("-" * 40)

    # Play/Pause
    print("Toggle play/pause...")
    result = client.play_pause()
    print(f"  Result: {result}")
    time.sleep(1)

    # Next track
    print("Next track...")
    result = client.next_track()
    print(f"  Result: {result}")
    time.sleep(1)

    # Previous track
    print("Previous track...")
    result = client.previous_track()
    print(f"  Result: {result}")
    time.sleep(1)

    # Stop
    print("Stop playback...")
    result = client.stop()
    print(f"  Result: {result}")

    print()


def test_volume_control(client: MtApiClient):
    """Test volume controls."""
    print("Testing Volume Control")
    print("-" * 40)

    volumes = [50, 75, 25, 80]
    for vol in volumes:
        print(f"Setting volume to {vol}%...")
        result = client.set_volume(vol)
        print(f"  Result: {result}")
        time.sleep(0.5)

    print()


def test_ui_navigation(client: MtApiClient):
    """Test UI navigation commands."""
    print("Testing UI Navigation")
    print("-" * 40)

    views = ['library', 'queue', 'liked', 'top25']
    for view in views:
        print(f"Switching to {view} view...")
        result = client.switch_view(view)
        print(f"  Result: {result}")
        time.sleep(1)

    print()


def test_search_functionality(client: MtApiClient):
    """Test search functionality."""
    print("Testing Search")
    print("-" * 40)

    # Search for something
    query = "rock"
    print(f"Searching for '{query}'...")
    result = client.search(query)
    print(f"  Result: {result}")
    time.sleep(2)

    # Clear search
    print("Clearing search...")
    result = client.clear_search()
    print(f"  Result: {result}")

    print()


def test_utility_controls(client: MtApiClient):
    """Test utility controls like loop and shuffle."""
    print("Testing Utility Controls")
    print("-" * 40)

    # Toggle loop
    print("Toggle loop mode...")
    result = client.toggle_loop()
    print(f"  Result: {result}")
    time.sleep(0.5)

    # Toggle shuffle
    print("Toggle shuffle mode...")
    result = client.toggle_shuffle()
    print(f"  Result: {result}")
    time.sleep(0.5)

    # Toggle favorite
    print("Toggle favorite...")
    result = client.toggle_favorite()
    print(f"  Result: {result}")

    print()


def get_full_status(client: MtApiClient):
    """Get and display full player status."""
    print("Full Player Status")
    print("-" * 40)

    status = client.get_status()
    if status['status'] == 'success':
        data = status['data']
        print(f"Is Playing: {data.get('is_playing', False)}")
        print(f"Loop Enabled: {data.get('loop_enabled', False)}")
        print(f"Shuffle Enabled: {data.get('shuffle_enabled', False)}")
        print(f"Volume: {data.get('volume', 0)}%")
        print(f"Current View: {data.get('current_view', 'Unknown')}")

        if 'current_track' in data:
            track = data['current_track']
            print("\nCurrent Track:")
            print(f"  Title: {track.get('title', 'Unknown')}")
            print(f"  Artist: {track.get('artist', 'Unknown')}")
            print(f"  Album: {track.get('album', 'Unknown')}")

        # Time info
        current_time = data.get('current_time', 0)
        duration = data.get('duration', 0)
        if duration > 0:
            progress = (current_time / duration) * 100
            print(f"\nProgress: {current_time:.1f}s / {duration:.1f}s ({progress:.1f}%)")
    else:
        print(f"Error: {status.get('message', 'Unknown error')}")

    print()


def simulate_user_session(client: MtApiClient):
    """Simulate a typical user session."""
    print("Simulating User Session")
    print("=" * 40)

    # Get initial status
    print("\n1. Getting initial status...")
    get_full_status(client)

    # Switch to library view
    print("2. Switching to library view...")
    client.switch_view('library')
    time.sleep(1)

    # Select and play first track
    print("3. Selecting first library item...")
    client.select_library_item(0)
    time.sleep(0.5)

    print("4. Playing selected track...")
    client.play()
    time.sleep(2)

    # Adjust volume
    print("5. Setting volume to 60%...")
    client.set_volume(60)
    time.sleep(1)

    # Toggle favorite
    print("6. Marking as favorite...")
    client.toggle_favorite()
    time.sleep(1)

    # Skip to next track
    print("7. Skipping to next track...")
    client.next_track()
    time.sleep(2)

    # Enable shuffle
    print("8. Enabling shuffle mode...")
    client.toggle_shuffle()
    time.sleep(1)

    # Final status
    print("\n9. Final status:")
    get_full_status(client)


def test_queue_operations(client: MtApiClient):
    """Test queue management operations."""
    print("Testing Queue Operations")
    print("-" * 40)

    # Get current queue
    print("Getting current queue...")
    queue = client.get_queue()
    if queue['status'] == 'success':
        print(f"  Queue has {queue['count']} items")
        if queue['count'] > 0 and 'data' in queue:
            # Show first 3 items
            for item in queue['data'][:3]:
                print(f"    [{item['index']}] {item['title']} - {item['artist']}")

    # Play track at index 2 (if exists)
    if queue.get('count', 0) > 2:
        print("\nPlaying track at index 2...")
        result = client.play_track_at_index(2)
        print(f"  Result: {result}")

    print()


def interactive_mode(client: MtApiClient):
    """Interactive command mode."""
    print("Interactive API Control")
    print("=" * 40)
    print("Commands: play, pause, next, prev, stop, status, volume <n>, quit")
    print()

    while True:
        try:
            cmd = input("> ").strip().lower()

            if cmd == "quit":
                break
            elif cmd == "play":
                print(client.play())
            elif cmd == "pause":
                print(client.pause())
            elif cmd == "next":
                print(client.next_track())
            elif cmd == "prev":
                print(client.previous_track())
            elif cmd == "stop":
                print(client.stop())
            elif cmd == "status":
                get_full_status(client)
            elif cmd.startswith("volume "):
                try:
                    vol = int(cmd.split()[1])
                    print(client.set_volume(vol))
                except (IndexError, ValueError):
                    print("Usage: volume <0-100>")
            else:
                print("Unknown command. Try: play, pause, next, prev, stop, status, volume <n>, quit")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    # Create client
    client = MtApiClient()

    # Check if server is running
    print("Checking API server connection...")
    status = client.get_status()
    if status.get('status') == 'error':
        print(f"Error: Cannot connect to API server. {status.get('message', '')}")
        print("\nMake sure the mt player is running with API server enabled:")
        print("  MT_API_SERVER_ENABLED=true uv run main.py")
        exit(1)

    print("Connected to mt API server!\n")

    # Run different test scenarios
    try:
        # Uncomment the tests you want to run:

        # test_playback_controls(client)
        # test_volume_control(client)
        # test_ui_navigation(client)
        # test_search_functionality(client)
        # test_utility_controls(client)
        # test_queue_operations(client)
        # simulate_user_session(client)

        # Or run interactive mode:
        interactive_mode(client)

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        print(f"\nError during tests: {e}")
