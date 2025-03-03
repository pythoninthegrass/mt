import os
import traceback
import vlc
from core.db import MusicDatabase
from core.queue import QueueManager
from utils.logs import get_player_logger

# Setup logger
logger = get_player_logger()


class PlayerCore:
    """
    Core player functionality for media playback.

    This class provides low-level media player control using VLC,
    handling playback state, track navigation, and event management.
    """

    def __init__(self, db: MusicDatabase, queue_manager: QueueManager):
        """
        Initialize the player core with database and queue manager.

        Args:
            db: Database instance for track information
            queue_manager: Queue manager for playlist handling
        """
        self.db = db
        self.queue_manager = queue_manager
        self.player = vlc.Instance()
        self.media_player = self.player.media_player_new()
        self.is_playing = False
        self.current_time = 0
        self.was_playing = False
        self.loop_enabled = self.db.get_loop_enabled()
        self.on_track_end_callback = None
        self.on_track_info_updated_callback = None

        # Set up end of track event handler
        self.media_player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self._on_track_end)

        logger.info("PlayerCore initialized")

    def play_pause(self) -> None:
        """Toggle play/pause state."""
        if not self.is_playing:
            if self.media_player.get_media() is not None:
                self.media_player.play()
                self.is_playing = True
                logger.info("Playback resumed: is_playing=%s", self.is_playing)
                self._update_track_info()
            else:
                filepath = self._get_current_filepath()
                if filepath:
                    logger.info("Starting playback of new file: %s", os.path.basename(filepath))
                    self._play_file(filepath)
                else:
                    logger.warning("No file to play: queue empty or files not found")
        else:
            self.current_time = self.media_player.get_time()
            self.media_player.pause()
            self.is_playing = False
            logger.info("Playback paused: is_playing=%s", self.is_playing)

    def next_song(self) -> None:
        """Play the next song in the queue."""
        logger.info("Next song requested")

        # Save current playing state to restore it after switching tracks
        was_playing = self.is_playing

        # Get current file path for debugging
        current_path = None
        if self.media_player.get_media():
            current_mrl = self.media_player.get_media().get_mrl()
            if current_mrl:
                current_path = current_mrl[7:] if current_mrl.startswith('file://') else current_mrl
                logger.info(f"Current file before next: {os.path.basename(current_path)}")

        # Stop current playback
        if self.is_playing:
            self.media_player.stop()

        # Get next filepath
        filepath = self._get_next_filepath()

        if filepath:
            logger.info(f"Playing next track: {os.path.basename(filepath)}")
            if os.path.exists(filepath):
                # Create a completely new media object
                media = self.player.media_new(filepath)
                self.media_player.set_media(media)
                logger.info(f"New media set to: {os.path.basename(filepath)}")

                # Start playback if it was playing before
                if was_playing:
                    self.media_player.play()
                    self.is_playing = True
                    logger.info(f"Playback started for: {os.path.basename(filepath)}")
                else:
                    logger.info(f"Media loaded but not playing for: {os.path.basename(filepath)}")

                # Fire track info updated callback if registered
                if self.on_track_info_updated_callback:
                    self.on_track_info_updated_callback()
            else:
                logger.error(f"Next track file doesn't exist: {filepath}")
        else:
            logger.info("No next track available")

    def previous_song(self) -> None:
        """Play the previous song in the queue."""
        logger.info("Previous song requested")

        # Save current playing state to restore it after switching tracks
        was_playing = self.is_playing

        # Get current file path for debugging
        current_path = None
        if self.media_player.get_media():
            current_mrl = self.media_player.get_media().get_mrl()
            if current_mrl:
                current_path = current_mrl[7:] if current_mrl.startswith('file://') else current_mrl
                logger.info(f"Current file before previous: {os.path.basename(current_path)}")

        # Stop current playback
        if self.is_playing:
            self.media_player.stop()

        # Get previous filepath
        filepath = self._get_previous_filepath()

        if filepath:
            logger.info(f"Playing previous track: {os.path.basename(filepath)}")
            if os.path.exists(filepath):
                # Create a completely new media object
                media = self.player.media_new(filepath)
                self.media_player.set_media(media)
                logger.info(f"New media set to: {os.path.basename(filepath)}")

                # Start playback if it was playing before
                if was_playing:
                    self.media_player.play()
                    self.is_playing = True
                    logger.info(f"Playback started for: {os.path.basename(filepath)}")
                else:
                    logger.info(f"Media loaded but not playing for: {os.path.basename(filepath)}")

                # Fire track info updated callback if registered
                if self.on_track_info_updated_callback:
                    self.on_track_info_updated_callback()
            else:
                logger.error(f"Previous track file doesn't exist: {filepath}")
        else:
            logger.info("No previous track available")

    def seek(self, position: float) -> None:
        """
        Seek to a position in the current track.

        Args:
            position: Position in milliseconds
        """
        if self.media_player.get_media() is not None:
            self.media_player.set_time(int(position))

    def stop(self) -> None:
        """Stop playback and reset player state."""
        if self.media_player.get_media() is not None:
            self.media_player.stop()
            self.is_playing = False
            logger.info("Playback stopped: is_playing=%s", self.is_playing)

    def toggle_loop(self) -> None:
        """Toggle loop playback mode."""
        self.loop_enabled = not self.loop_enabled
        self.db.set_loop_enabled(self.loop_enabled)
        logger.info("Loop mode toggled: %s", "enabled" if self.loop_enabled else "disabled")

    def get_current_time(self) -> int:
        """Get current playback position in milliseconds."""
        return self.media_player.get_time()

    def get_duration(self) -> int:
        """Get track duration in milliseconds."""
        return self.media_player.get_length()

    def get_volume(self) -> int:
        """Get current volume level (0-100)."""
        return self.media_player.audio_get_volume()

    def set_volume(self, volume: int) -> None:
        """
        Set the player volume.

        Args:
            volume: Volume level (0-100)
        """
        try:
            # Ensure volume is within valid range
            volume = max(0, min(100, int(volume)))
            self.media_player.audio_set_volume(volume)
        except Exception as e:
            logger.error("Error setting volume: %s", e)
            traceback.print_exc()

    def _play_file(self, filepath: str) -> None:
        """
        Play a media file.

        Args:
            filepath: Path to the media file
        """
        if not os.path.exists(filepath):
            logger.error("File not found: %s", filepath)
            return

        try:
            # Create media and set to player
            media = self.player.media_new(filepath)
            self.media_player.set_media(media)
            self.media_player.play()
            self.is_playing = True
            logger.info("Playing file: %s, is_playing=%s", os.path.basename(filepath), self.is_playing)
            self._update_track_info()
        except Exception as e:
            logger.error("Error playing file: %s", e)
            traceback.print_exc()

    def _update_track_info(self) -> None:
        """Update current track information and notify listeners."""
        if self.on_track_info_updated_callback:
            try:
                self.on_track_info_updated_callback()
            except Exception as e:
                logger.error("Error in track info update callback: %s", e)
                traceback.print_exc()

    def _get_current_filepath(self) -> str | None:
        """
        Get the filepath of the current track.

        Returns:
            str | None: Path to the current track or None if not found
        """
        current_items = self.queue_manager.get_queue_items()
        if not current_items:
            return None

        # Find the current track
        for item in current_items:
            # item structure is (id, path, title, artist, album, track_num)
            filepath = item[1]
            if os.path.exists(filepath):
                return filepath

        return None

    def _get_next_filepath(self) -> str | None:
        """
        Get the filepath of the next track.

        Returns:
            str | None: Path to the next track or None if not found
        """
        current_items = self.queue_manager.get_queue_items()
        if not current_items:
            logger.warning("No items in queue for _get_next_filepath")
            return None

        # Log queue size for debugging
        logger.info(f"Queue has {len(current_items)} items for next track lookup")

        # Debug the structure of the first few queue items
        if current_items:
            logger.info(f"First queue item structure: {current_items[0]}")
            if len(current_items) > 1:
                logger.info(f"Second queue item structure: {current_items[1]}")

        # If there's no current media, return the first track
        if self.media_player.get_media() is None:
            # Filepath is the first element (index 0) in each queue item tuple
            first_item_path = current_items[0][0]
            if os.path.exists(first_item_path):
                logger.info(f"No current media, returning first track: {os.path.basename(first_item_path)}")
                return first_item_path
            else:
                logger.warning(f"First track in queue doesn't exist: {first_item_path}")
                return None

        # Find the current track and get the next one
        current_media = self.media_player.get_media()
        if not current_media:
            logger.warning("No current media in player")
            return None

        current_mrl = current_media.get_mrl()
        if not current_mrl:
            logger.warning("Current media has no MRL")
            return None

        # Convert mrl to filepath and handle URL encoding
        if current_mrl.startswith('file://'):
            current_filepath = current_mrl[7:]
            # Handle URL encoding in the path (e.g., spaces encoded as %20)
            import urllib.parse
            current_filepath = urllib.parse.unquote(current_filepath)
        else:
            current_filepath = current_mrl

        current_abs_path = os.path.abspath(current_filepath)
        logger.info(f"Current absolute track path: {current_abs_path}")

        # Print all queue items for debugging
        for i, item in enumerate(current_items):
            filepath = item[0]
            abs_filepath = os.path.abspath(filepath)
            logger.info(f"Queue item {i}: {abs_filepath}")

        # Find the next track after the current one
        found_current = False
        for index, item in enumerate(current_items):
            # Filepath is the first element (index 0) in each queue item tuple
            filepath = item[0]
            abs_filepath = os.path.abspath(filepath)

            # Log comparison for debugging
            logger.info(f"Comparing current: {current_abs_path}")
            logger.info(f"With queue item: {abs_filepath}")
            logger.info(f"Equal? {abs_filepath == current_abs_path}")

            # If we already found the current track, return the next valid one
            if found_current and os.path.exists(filepath):
                logger.info(f"Found next track: {os.path.basename(filepath)} at position {index}")
                return filepath

            # Check if this is the current track - using absolute paths for reliable comparison
            if abs_filepath == current_abs_path:
                logger.info(f"Found current track at position {index}")
                found_current = True

        # If we reached the end and loop is enabled, return the first track
        if found_current and self.loop_enabled and current_items:
            logger.info("Reached end of queue, looping to first track")
            first_item_path = current_items[0][0]
            if os.path.exists(first_item_path):
                return first_item_path
            else:
                logger.warning(f"First track for loop doesn't exist: {first_item_path}")

        # If we didn't find the current track or the next track, try to return any non-current track
        if not found_current and current_items:
            logger.warning("Current track not found in queue by exact path, trying basename comparison")
            current_basename = os.path.basename(current_filepath)

            for index, item in enumerate(current_items):
                filepath = item[0]
                basename = os.path.basename(filepath)

                if basename == current_basename:
                    logger.info(f"Found current track by basename at position {index}")
                    found_current = True
                    if index + 1 < len(current_items):
                        next_filepath = current_items[index + 1][0]
                        if os.path.exists(next_filepath):
                            logger.info(f"Found next track by basename: {os.path.basename(next_filepath)}")
                            return next_filepath
                    elif self.loop_enabled:
                        first_item_path = current_items[0][0]
                        if os.path.exists(first_item_path):
                            logger.info("Looping to first track after basename match")
                            return first_item_path

            # If still not found, just return the first valid track that's not the current one
            logger.warning("Track not found by basename either, selecting different track")
            for item in current_items:
                filepath = item[0]
                if os.path.exists(filepath) and os.path.basename(filepath) != current_basename:
                    logger.info(f"Selected different track: {os.path.basename(filepath)}")
                    return filepath

        logger.info("No next track found in queue")
        return None

    def _get_previous_filepath(self) -> str | None:
        """
        Get the filepath of the previous track.

        Returns:
            str | None: Path to the previous track or None if not found
        """
        current_items = self.queue_manager.get_queue_items()
        if not current_items:
            logger.warning("No items in queue for _get_previous_filepath")
            return None

        # Log queue size for debugging
        logger.info(f"Queue has {len(current_items)} items for previous track lookup")

        # Debug the structure of the first few queue items
        if current_items:
            logger.info(f"Last queue item structure: {current_items[-1]}")
            if len(current_items) > 1:
                logger.info(f"Second-to-last queue item structure: {current_items[-2]}")

        # If there's no current media, return the last track
        if self.media_player.get_media() is None:
            # Filepath is the first element (index 0) in each queue item tuple
            last_item_path = current_items[-1][0]
            if os.path.exists(last_item_path):
                logger.info(f"No current media, returning last track: {os.path.basename(last_item_path)}")
                return last_item_path
            else:
                logger.warning(f"Last track in queue doesn't exist: {last_item_path}")
                return None

        # Find the current track and get the previous one
        current_media = self.media_player.get_media()
        if not current_media:
            logger.warning("No current media in player")
            return None

        current_mrl = current_media.get_mrl()
        if not current_mrl:
            logger.warning("Current media has no MRL")
            return None

        # Convert mrl to filepath and handle URL encoding
        if current_mrl.startswith('file://'):
            current_filepath = current_mrl[7:]
            # Handle URL encoding in the path (e.g., spaces encoded as %20)
            import urllib.parse
            current_filepath = urllib.parse.unquote(current_filepath)
        else:
            current_filepath = current_mrl

        current_abs_path = os.path.abspath(current_filepath)
        logger.info(f"Current absolute track path: {current_abs_path}")

        # Print all queue items for debugging
        for i, item in enumerate(current_items):
            filepath = item[0]
            abs_filepath = os.path.abspath(filepath)
            logger.info(f"Queue item {i}: {abs_filepath}")

        # Find the previous track before the current one using absolute paths
        previous_item = None
        found_current = False

        for index, item in enumerate(current_items):
            # Filepath is the first element (index 0) in each queue item tuple
            filepath = item[0]
            abs_filepath = os.path.abspath(filepath)

            # Log comparison for debugging
            logger.info(f"Comparing current: {current_abs_path}")
            logger.info(f"With queue item: {abs_filepath}")
            logger.info(f"Equal? {abs_filepath == current_abs_path}")

            # Check if this is the current track using absolute paths for reliable comparison
            if abs_filepath == current_abs_path:
                logger.info(f"Found current track at position {index}")
                found_current = True
                if previous_item is not None and os.path.exists(previous_item[0]):
                    logger.info(f"Found previous track: {os.path.basename(previous_item[0])} at position {index-1}")
                    return previous_item[0]
                elif self.loop_enabled and current_items:
                    # If loop is enabled and we're at the first track, go to the last
                    last_item_path = current_items[-1][0]
                    if os.path.exists(last_item_path):
                        logger.info("At first track, looping to last track")
                        return last_item_path
                    else:
                        logger.warning(f"Last track for loop doesn't exist: {last_item_path}")
                else:
                    logger.info("No previous track available (at start of queue)")
                    return None

            if os.path.exists(filepath):
                previous_item = item

        # If we somehow didn't find the current track, try to match by basename
        if not found_current:
            logger.warning("Current track not found in queue by exact path, trying basename comparison")
            current_basename = os.path.basename(current_filepath)

            for index, item in enumerate(current_items):
                filepath = item[0]
                basename = os.path.basename(filepath)

                if basename == current_basename:
                    logger.info(f"Found current track by basename at position {index}")
                    found_current = True
                    if index > 0:
                        prev_filepath = current_items[index - 1][0]
                        if os.path.exists(prev_filepath):
                            logger.info(f"Found previous track by basename: {os.path.basename(prev_filepath)}")
                            return prev_filepath
                    elif self.loop_enabled and len(current_items) > 1:
                        last_item_path = current_items[-1][0]
                        if os.path.exists(last_item_path):
                            logger.info("Looping to last track after basename match")
                            return last_item_path

            # If still not found, just return the first valid track that's not the current one
            logger.warning("Track not found by basename either, selecting different track")
            for item in current_items:
                filepath = item[0]
                if os.path.exists(filepath) and os.path.basename(filepath) != current_basename:
                    logger.info(f"Selected different track: {os.path.basename(filepath)}")
                    return filepath

        logger.info("No previous track found in queue")
        return None

    def _is_last_song(self) -> bool:
        """
        Check if current track is the last in the queue.

        Returns:
            bool: True if current track is the last, False otherwise
        """
        current_items = self.queue_manager.get_queue_items()
        if not current_items:
            return True

        current_media = self.media_player.get_media()
        if not current_media:
            return False

        current_mrl = current_media.get_mrl()
        if not current_mrl:
            return False

        # Convert mrl to filepath
        if current_mrl.startswith('file://'):
            current_filepath = current_mrl[7:]
        else:
            current_filepath = current_mrl

        # Get the last item's filepath
        last_filepath = current_items[-1][1]

        return current_filepath == last_filepath or os.path.abspath(current_filepath) == os.path.abspath(last_filepath)

    def _on_track_end(self, event):
        """
        Handle the end of track event from VLC.

        Args:
            event: VLC event object
        """
        # This is called from VLC event thread, schedule handling on main thread
        # In a Flet app, we'll handle this differently
        try:
            self._handle_track_end()
        except Exception as e:
            logger.error("Error handling track end: %s", e)
            traceback.print_exc()

    def _handle_track_end(self):
        """Handle actions when a track ends."""
        # If loop is not enabled and this is the last song, just stop
        if not self.loop_enabled and self._is_last_song():
            logger.info("End of queue reached and loop disabled, stopping playback")
            self.stop()
            return

        # Otherwise, play the next song
        filepath = self._get_next_filepath()
        if filepath:
            logger.info("Track ended, playing next track: %s", os.path.basename(filepath))
            self._play_file(filepath)
        else:
            logger.info("Track ended, no next track available, stopping playback")
            self.stop()

        # Call callback if registered
        if self.on_track_end_callback:
            try:
                self.on_track_end_callback()
            except Exception as e:
                logger.error("Error in track end callback: %s", e)
                traceback.print_exc()
