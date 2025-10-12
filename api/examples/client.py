#!/usr/bin/env python

import json
import socket
from typing import Any, Optional


class MtApiClient:
    """Client for controlling the mt music player via API."""

    def __init__(self, host: str = 'localhost', port: int = 5555):
        """Initialize the client.

        Args:
            host: API server hostname (default: localhost)
            port: API server port (default: 5555)
        """
        self.host = host
        self.port = port

    def send_command(self, action: str, **kwargs) -> dict[str, Any]:
        """Send a command to the API server.

        Args:
            action: The action to perform
            **kwargs: Additional parameters for the action

        Returns:
            Response dictionary from the server
        """
        command = {'action': action, **kwargs}

        try:
            # Create socket and connect
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5.0)  # 5 second timeout
            s.connect((self.host, self.port))

            # Send command
            s.send(json.dumps(command).encode('utf-8'))

            # Receive response
            response_data = s.recv(4096).decode('utf-8')
            s.close()

            # Parse response
            return json.loads(response_data)

        except OSError as e:
            return {'status': 'error', 'message': f'Socket error: {str(e)}'}
        except json.JSONDecodeError as e:
            return {'status': 'error', 'message': f'JSON decode error: {str(e)}'}
        except Exception as e:
            return {'status': 'error', 'message': f'Unexpected error: {str(e)}'}

    # === Playback Controls ===

    def play_pause(self) -> dict[str, Any]:
        """Toggle play/pause."""
        return self.send_command('play_pause')

    def play(self) -> dict[str, Any]:
        """Start playback."""
        return self.send_command('play')

    def pause(self) -> dict[str, Any]:
        """Pause playback."""
        return self.send_command('pause')

    def stop(self) -> dict[str, Any]:
        """Stop playback."""
        return self.send_command('stop')

    def next_track(self) -> dict[str, Any]:
        """Skip to next track."""
        return self.send_command('next')

    def previous_track(self) -> dict[str, Any]:
        """Go to previous track."""
        return self.send_command('previous')

    # === Volume Control ===

    def set_volume(self, volume: int) -> dict[str, Any]:
        """Set volume level (0-100)."""
        return self.send_command('set_volume', volume=volume)

    # === Seek Control ===

    def seek(self, offset: float) -> dict[str, Any]:
        """Seek relative to current position (in seconds)."""
        return self.send_command('seek', offset=offset)

    def seek_to(self, position: float) -> dict[str, Any]:
        """Seek to absolute position (in seconds)."""
        return self.send_command('seek_to_position', position=position)

    # === Utility Controls ===

    def toggle_loop(self) -> dict[str, Any]:
        """Toggle loop mode."""
        return self.send_command('toggle_loop')

    def toggle_shuffle(self) -> dict[str, Any]:
        """Toggle shuffle mode."""
        return self.send_command('toggle_shuffle')

    def toggle_favorite(self) -> dict[str, Any]:
        """Toggle favorite status of current track."""
        return self.send_command('toggle_favorite')

    # === UI Navigation ===

    def switch_view(self, view: str) -> dict[str, Any]:
        """Switch to a different view (library, queue, liked, top25)."""
        return self.send_command('switch_view', view=view)

    def select_library_item(self, index: int) -> dict[str, Any]:
        """Select item in library by index."""
        return self.send_command('select_library_item', index=index)

    def select_queue_item(self, index: int) -> dict[str, Any]:
        """Select item in queue by index."""
        return self.send_command('select_queue_item', index=index)

    def play_track_at_index(self, index: int) -> dict[str, Any]:
        """Play track at specific queue index."""
        return self.send_command('play_track_at_index', index=index)

    # === Queue Management ===

    def add_to_queue(self, files: list) -> dict[str, Any]:
        """Add files to queue."""
        return self.send_command('add_to_queue', files=files)

    def clear_queue(self) -> dict[str, Any]:
        """Clear the queue."""
        return self.send_command('clear_queue')

    def remove_from_queue(self, index: int) -> dict[str, Any]:
        """Remove track from queue by index."""
        return self.send_command('remove_from_queue', index=index)

    # === Search ===

    def search(self, query: str) -> dict[str, Any]:
        """Perform a search."""
        return self.send_command('search', query=query)

    def clear_search(self) -> dict[str, Any]:
        """Clear the search."""
        return self.send_command('clear_search')

    # === Info Queries ===

    def get_status(self) -> dict[str, Any]:
        """Get current player status."""
        return self.send_command('get_status')

    def get_current_track(self) -> dict[str, Any]:
        """Get current track information."""
        return self.send_command('get_current_track')

    def get_queue(self) -> dict[str, Any]:
        """Get current queue."""
        return self.send_command('get_queue')

    def get_library(self) -> dict[str, Any]:
        """Get library contents (first 100 items)."""
        return self.send_command('get_library')

    # === Media Key Simulation ===

    def media_key(self, key: str) -> dict[str, Any]:
        """Simulate media key press (play_pause, next, previous)."""
        return self.send_command('media_key', key=key)


if __name__ == "__main__":
    # Example usage
    client = MtApiClient()

    # Get status
    status = client.get_status()
    print("Status:", json.dumps(status, indent=2))

    # Toggle play/pause
    result = client.play_pause()
    print("Play/Pause:", result)

    # Set volume to 50%
    result = client.set_volume(50)
    print("Set Volume:", result)
