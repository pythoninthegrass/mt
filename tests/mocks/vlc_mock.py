class MockEventType:
    """Mock VLC EventType enum."""

    MediaPlayerEndReached = 265


class MockEventManager:
    """Mock VLC EventManager for handling events."""

    def __init__(self):
        self.callbacks = {}

    def event_attach(self, event_type, callback):
        """Attach a callback to an event type."""
        self.callbacks[event_type] = callback

    def trigger_event(self, event_type, *args, **kwargs):
        """Manually trigger an event (for testing)."""
        if event_type in self.callbacks:
            self.callbacks[event_type](*args, **kwargs)


class MockMedia:
    """Mock VLC Media object with ctypes compatibility.

    When real VLC is loaded (e.g., after E2E tests), the real MediaPlayer
    may be used with MockMedia objects. VLC uses ctypes which requires
    the _as_parameter_ attribute for proper conversion.
    """

    def __init__(self, filepath):
        self.filepath = filepath
        # ctypes compatibility: return None to indicate no native object
        # This allows set_media() to work without crashing
        self._as_parameter_ = None


class MockMediaPlayer:
    """Mock VLC MediaPlayer for unit testing.

    Simulates VLC media player behavior without actual playback.
    Provides deterministic responses for time, duration, volume, etc.
    """

    def __init__(self):
        self._media = None
        self._is_playing = False
        self._time = 0  # Current position in milliseconds
        self._length = 180000  # Default 3 minutes in milliseconds
        self._volume = 100
        self._event_manager = MockEventManager()

    def event_manager(self):
        """Return the event manager."""
        return self._event_manager

    def get_media(self):
        """Get the current media object."""
        return self._media

    def set_media(self, media):
        """Set the media to play."""
        self._media = media
        self._time = 0
        if media is not None:
            # Reset to reasonable defaults when setting new media
            self._length = 180000  # 3 minutes default

    def play(self):
        """Start playback."""
        self._is_playing = True
        return 0  # VLC returns 0 on success

    def pause(self):
        """Pause playback."""
        self._is_playing = False

    def stop(self):
        """Stop playback."""
        self._is_playing = False
        self._time = 0

    def get_time(self):
        """Get current playback time in milliseconds."""
        return self._time

    def set_time(self, time_ms):
        """Set playback position in milliseconds."""
        self._time = max(0, min(time_ms, self._length))

    def get_length(self):
        """Get media duration in milliseconds."""
        if self._media is None:
            return 0
        return self._length

    def audio_get_volume(self):
        """Get volume (0-100)."""
        return self._volume

    def audio_set_volume(self, volume):
        """Set volume (0-100)."""
        self._volume = max(0, min(100, volume))
        return 0  # VLC returns 0 on success

    def is_playing(self):
        """Check if currently playing."""
        return self._is_playing

    # Test helper methods (not part of real VLC API)
    def _set_length(self, length_ms):
        """Set the media length for testing purposes."""
        self._length = length_ms

    def _simulate_playback(self, duration_ms):
        """Simulate playback for a given duration."""
        if self._is_playing and self._media is not None:
            self._time = min(self._time + duration_ms, self._length)
            if self._time >= self._length:
                # Trigger end reached event
                self._event_manager.trigger_event(MockEventType.MediaPlayerEndReached)
                self._is_playing = False


class MockInstance:
    """Mock VLC Instance for creating media players and media objects."""

    def __init__(self, *args, **kwargs):
        """Initialize mock VLC instance."""
        self._media_player = None

    def media_player_new(self):
        """Create a new media player."""
        self._media_player = MockMediaPlayer()
        return self._media_player

    def media_new(self, filepath):
        """Create a new media object from filepath."""
        return MockMedia(filepath)
