#!/usr/bin/env python

import json
import socket


def send_command(action, **kwargs):
    """Send a command to the mt API server.

    Args:
        action: The action to perform
        **kwargs: Additional parameters for the action

    Returns:
        Response dictionary from server or error dict
    """
    try:
        s = socket.socket()
        s.settimeout(5.0)
        s.connect(('localhost', 5555))
        command = {'action': action, **kwargs}
        s.send(json.dumps(command).encode())
        response = s.recv(4096).decode()
        s.close()
        return json.loads(response)
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


# Example usage functions
def play_pause():
    """Toggle play/pause."""
    return send_command('play_pause')


def next_track():
    """Skip to next track."""
    return send_command('next')


def previous_track():
    """Go to previous track."""
    return send_command('previous')


def set_volume(volume):
    """Set volume (0-100)."""
    return send_command('set_volume', volume=volume)


def toggle_favorite():
    """Toggle favorite status."""
    return send_command('toggle_favorite')


def get_status():
    """Get player status."""
    return send_command('get_status')


def search(query):
    """Search for tracks."""
    return send_command('search', query=query)


if __name__ == "__main__":
    # Example: Control playback
    print("Playing/Pausing...")
    print(play_pause())

    # Example: Get current status
    print("\nGetting status...")
    status = get_status()
    if status['status'] == 'success':
        data = status['data']
        print(f"Playing: {data.get('is_playing', False)}")
        if 'current_track' in data:
            track = data['current_track']
            print(f"Current track: {track.get('title', 'Unknown')} by {track.get('artist', 'Unknown')}")

    # Example: Set volume to 75%
    print("\nSetting volume to 75%...")
    print(set_volume(75))
