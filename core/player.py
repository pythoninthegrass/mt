#!/usr/bin/env python

import os
import random
import threading
import time
import traceback
from collections.abc import Callable
from core.controls import PlayerCore
from core.db import DB_TABLES, MusicDatabase
from core.library import LibraryManager
from core.models import Track
from core.queue import QueueManager
from typing import Optional
from urllib.parse import unquote
from utils.common import format_time, set_db_instance
from utils.logs import get_player_logger

# Setup logger
logger = get_player_logger()


class Player:
    """
    Player class that provides high-level playback control.

    This class wraps the PlayerCore and QueueManager to provide a simplified
    interface for playing and controlling music playback.
    """

    def __init__(self):
        """Initialize player components and database."""
        # Initialize database, queue manager, and player core
        self.db = MusicDatabase('mt.db', DB_TABLES)
        self.queue_manager = QueueManager(self.db)
        self.player_core = PlayerCore(self.db, self.queue_manager)
        self.library_manager = LibraryManager(self.db)
        self.current_track = None
        self.is_playing = False
        self.error_handler = None

        # Register callback handlers
        self.player_core.on_track_end_callback = self._on_track_end
        self.player_core.on_track_info_updated_callback = self._on_track_info_updated

        # Event handlers for UI updates
        self.on_track_changed = None
        self.on_playback_state_changed = None

        # Set global database instance for app access
        set_db_instance(self.db)

        logger.info("Player initialized")

    def play(self, track: Track | None = None) -> None:
        """
        Play a track or resume playback.

        Args:
            track (Optional[Track], optional): Track to play. Defaults to None.
        """
        if track is None:
            # If we're paused, just resume
            if self.current_track and not self.player_core.is_playing and self.player_core.media_player.get_media() is not None:
                logger.info(f"Resuming playback of current track: {self.current_track.title}")
                self.player_core.play()
                self.is_playing = True
                if self.on_playback_state_changed:
                    self.on_playback_state_changed(self.is_playing)
                return

            # If no current track, start from the beginning of the library
            if not self.current_track:
                logger.info("No current track, starting from first track in library")
                library_items = self.library_manager.get_library_items()
                if library_items:
                    first_track_path = library_items[0][0]  # First item's filepath
                    if first_track_path and os.path.exists(first_track_path):
                        # Set up the queue from the beginning
                        self.set_up_queue()
                        # Get track metadata
                        metadata = self.db.get_metadata_by_filepath(first_track_path)
                        if metadata:
                            # Create a Track object
                            track = Track(
                                id=metadata.get('id', ''),
                                title=metadata.get('title', os.path.basename(first_track_path)),
                                artist=metadata.get('artist', ''),
                                album=metadata.get('album', ''),
                                path=first_track_path,
                                duration=metadata.get('duration', 0),
                                year=metadata.get('year', ''),
                                genre=metadata.get('genre', ''),
                                track_number=metadata.get('track_number', '')
                            )
                            logger.info(f"Starting playback from first track: {track.title}")
                        else:
                            logger.warning(f"No metadata found for first track: {first_track_path}")
                            return
                    else:
                        logger.warning("First track path is invalid or doesn't exist")
                        return
                else:
                    logger.warning("No tracks in library to play")
                    return
            else:
                # We have a current track but it's not playing, so play it
                track = self.current_track
                logger.info(f"Playing current track: {track.title}")
        else:
            # If we have a specific track to play
            logger.info(f"Playing specific track: {track.title}")
            # Set up the queue starting from this track
            self.set_up_queue(track.path)

        # At this point, we have a valid track to play
        try:
            # Use _play_file method instead of set_media_by_filepath
            self.player_core._play_file(track.path)

            # Update current track and state
            self.current_track = track
            self.is_playing = True

            # Notify listeners about track and state changes
            if self.on_track_changed:
                self.on_track_changed(self.current_track)
            if self.on_playback_state_changed:
                self.on_playback_state_changed(self.is_playing)

            logger.info(f"Started playback of: {track.title}")
        except Exception as e:
            # Log the error
            logger.error(f"Error playing track {track.title}: {e}")
            # Include stack trace for debugging
            logger.error(traceback.format_exc())

            # Reset player state
            self.is_playing = False

            # Use error handler if available, otherwise just log
            if self.error_handler:
                self.error_handler(str(e))
            # Notify of playback state change even if error
            if self.on_playback_state_changed:
                self.on_playback_state_changed(False)

    def _rebuild_queue_from_track(self, selected_track: Track):
        """
        Rebuild the queue to start from the selected track and continue sequentially.

        Args:
            selected_track: Track to start the queue from
        """
        try:
            logger.info("Rebuilding queue from track: %s - %s", selected_track.title, selected_track.artist)

            # Get all library items
            library_items = self.library_manager.get_library_items()
            if not library_items:
                logger.warning("Cannot rebuild queue: no library items")
                return

            # Find the index of the selected track in the library
            selected_index = -1
            selected_filepath = os.path.abspath(selected_track.path)

            for i, item in enumerate(library_items):
                filepath = item[0]
                if os.path.abspath(filepath) == selected_filepath:
                    selected_index = i
                    break

            if selected_index == -1:
                logger.warning("Selected track not found in library, cannot rebuild queue")
                # Still ensure the track is in queue
                self._ensure_track_in_queue(selected_track.path)
                return

            # Clear current queue (optional - based on whether you want to keep history)
            # For now, we'll keep the queue as is and just ensure the selected track is in it

            # Add the selected track and all subsequent tracks to the queue
            # Only add tracks that aren't already in the queue
            queue_items = self.queue_manager.get_queue_items()
            queue_paths = [os.path.abspath(item[0]) for item in queue_items] if queue_items else []

            # Add selected track first if not already in queue
            if selected_filepath not in queue_paths:
                self.queue_manager.add_to_queue(selected_track.path)
                logger.info("Added selected track to queue: %s", os.path.basename(selected_track.path))

            # Add subsequent tracks
            for i in range(selected_index + 1, len(library_items)):
                filepath = library_items[i][0]
                abs_path = os.path.abspath(filepath)
                if abs_path not in queue_paths and os.path.exists(filepath):
                    self.queue_manager.add_to_queue(filepath)
                    logger.info("Added subsequent track to queue: %s", os.path.basename(filepath))

            logger.info("Queue rebuilt from selected track")
        except Exception as e:
            logger.error("Error rebuilding queue: %s", e)
            traceback.print_exc()

    def _ensure_track_in_queue(self, filepath: str):
        """
        Ensure that a track is in the queue.

        Args:
            filepath: Path to the media file to add to queue
        """
        try:
            # Check if the track is already in the queue
            items = self.queue_manager.get_queue_items()
            for item in items:
                if os.path.abspath(item[0]) == os.path.abspath(filepath):
                    logger.debug("Track already in queue: %s", os.path.basename(filepath))
                    return

            # If not in queue, add it
            logger.info("Adding track to queue: %s", os.path.basename(filepath))
            self.queue_manager.add_to_queue(filepath)
        except Exception as e:
            logger.error("Error ensuring track in queue: %s", e)
            traceback.print_exc()

    def add_library_to_queue(self, tracks=None):
        """
        Add all library items to the queue to enable next/previous navigation.

        This method populates the queue with all tracks from the library,
        enabling seamless navigation through the entire collection.

        Args:
            tracks: Optional list of Track objects to add to the queue directly.
                   If provided, these will be added instead of querying the database.
        """
        try:
            items_to_add = 0

            # Get current queue items to avoid duplicates
            queue_items = self.queue_manager.get_queue_items()

            # Debug queue items
            logger.info(f"Current queue has {len(queue_items) if queue_items else 0} items")

            # Extract absolute paths from queue items for comparison
            queue_paths = []
            if queue_items:
                for item in queue_items:
                    if item and len(item) > 0:
                        filepath = item[0]
                        if filepath:
                            queue_paths.append(os.path.abspath(filepath))

            if tracks:
                # Add tracks provided directly from the UI's MusicLibrary
                logger.info(f"Adding {len(tracks)} tracks from provided library to queue")
                for track in tracks:
                    if hasattr(track, 'path') and track.path:
                        # Debug track information
                        logger.info(f"Processing track: {track.title} - path: {track.path}")

                        if os.path.exists(track.path):
                            abs_path = os.path.abspath(track.path)

                            # Debug path comparison
                            logger.info(f"Checking if path is already in queue: {abs_path}")
                            logger.info(f"Queue contains {len(queue_paths)} paths")

                            if abs_path not in queue_paths:
                                logger.info(f"Adding track to queue: {track.title}")
                                self.queue_manager.add_to_queue(abs_path)
                                items_to_add += 1
                            else:
                                logger.info(f"Track already in queue: {track.title}")
                        else:
                            logger.warning(f"Track path doesn't exist: {track.path}")
                    else:
                        logger.warning(f"Track has no valid path: {track}")
            else:
                # Get all library items from the database if no tracks provided
                library_items = self.library_manager.get_library_items()
                if not library_items:
                    logger.info("No library items to add to queue")
                    return

                # Add each library item to queue if not already there
                for item in library_items:
                    # Library item format depends on the specific query, but filepath should be at a consistent index
                    # Assuming filepath is the first element in the tuple
                    filepath = item[0]
                    if filepath and os.path.exists(filepath):
                        abs_path = os.path.abspath(filepath)
                        if abs_path not in queue_paths:
                            self.queue_manager.add_to_queue(filepath)
                            items_to_add += 1

            logger.info(f"Added {items_to_add} tracks from library to queue")
        except Exception as e:
            logger.error(f"Error adding library to queue: {e}")
            traceback.print_exc()

    def _play_file(self, filepath: str):
        """
        Play a file and update playback state.

        Args:
            filepath: Path to the media file to play
        """
        try:
            # Play the file using player core
            old_state = self.player_core.is_playing
            self.player_core._play_file(filepath)
            new_state = self.player_core.is_playing

            # Log state change if it occurred
            if old_state != new_state:
                logger.info("Player state changed in _play_file: %s to %s", old_state, new_state)
                if self.on_playback_state_changed:
                    self.on_playback_state_changed(new_state)

            # Update current track info
            track_info = self.db.get_metadata_by_filepath(filepath)
            if track_info:
                # Create a Track object from the metadata
                track_id = os.path.basename(filepath)
                self.current_track = Track(
                    id=track_id,
                    title=track_info.get('title', 'Unknown Title'),
                    artist=track_info.get('artist', 'Unknown Artist'),
                    album=track_info.get('album', 'Unknown Album'),
                    path=filepath,
                    duration=track_info.get('length', 0),
                    year=track_info.get('year', ''),
                    genre=track_info.get('genre', ''),
                    track_number=track_info.get('track_num', 0)
                )

                logger.info("Now playing: %s - %s", self.current_track.title, self.current_track.artist)

                # Notify listeners
                if self.on_track_changed:
                    self.on_track_changed(self.current_track)

                # Update play count in database
                self._update_play_count(filepath)
            else:
                logger.warning("No track metadata found for %s", os.path.basename(filepath))
        except Exception as e:
            logger.error("Error playing file: %s", e)
            traceback.print_exc()

    def _update_play_count(self, filepath: str):
        """
        Update play count for a track in the database.

        Args:
            filepath: Path to the track file
        """
        def update_play_count():
            try:
                # Delay a bit to make sure playback has really started
                time.sleep(5)
                # Only update if we're still playing the same track
                current_media = self.player_core.media_player.get_media()
                if current_media:
                    current_mrl = current_media.get_mrl()
                    if current_mrl:
                        current_path = current_mrl[7:] if current_mrl.startswith('file://') else current_mrl
                        if os.path.abspath(current_path) == os.path.abspath(filepath):
                            self.db.increment_play_count(filepath)
                            logger.debug("Incremented play count for %s", os.path.basename(filepath))
            except Exception as e:
                logger.error("Error updating play count: %s", e)
                traceback.print_exc()

        # Run in a separate thread to not block UI
        threading.Thread(target=update_play_count, daemon=True).start()

    def pause(self):
        """Pause playback if playing."""
        if self.player_core.is_playing:
            old_state = self.player_core.is_playing
            self.player_core.play_pause()
            new_state = self.player_core.is_playing
            logger.info("Pause called: is_playing changed from %s to %s", old_state, new_state)
            if self.on_playback_state_changed:
                self.on_playback_state_changed(self.player_core.is_playing)

    def stop(self):
        """Stop playback."""
        old_state = self.player_core.is_playing
        self.player_core.stop()
        logger.info("Stop called: was_playing=%s, is_playing=False", old_state)
        if self.on_playback_state_changed:
            self.on_playback_state_changed(False)

    def next(self) -> None:
        """
        Skip to the next track in the queue.
        """
        try:
            if not self.queue_manager.get_queue_items():
                logger.warning("Cannot skip to next track: queue is empty")
                return

            queue_items = self.queue_manager.get_queue_items()
            logger.info(f"Current queue has {len(queue_items)} items")

            current_filepath = None
            if self.current_track:
                current_filepath = self.current_track.path
                logger.info(f"Current track before next: {os.path.basename(current_filepath)}")
            else:
                logger.info("No current track before next")

            # Use the player core to go to the next track
            self.player_core.next_song()

            # Get the current media after navigation
            next_filepath = None
            if self.player_core.media_player.get_media():
                next_mrl = self.player_core.media_player.get_media().get_mrl()
                if next_mrl:
                    next_filepath = next_mrl[7:] if next_mrl.startswith('file://') else next_mrl
                    # Decode URL-encoded characters
                    next_filepath = unquote(next_filepath)
                    logger.info(f"Next filepath after navigation: {next_filepath}")

            if next_filepath and os.path.exists(next_filepath):
                # Get track metadata
                metadata = self.db.get_metadata_by_filepath(next_filepath)
                if metadata:
                    # Create a Track object
                    next_track = Track(
                        id=metadata.get('id', ''),
                        title=metadata.get('title', os.path.basename(next_filepath)),
                        artist=metadata.get('artist', ''),
                        album=metadata.get('album', ''),
                        path=next_filepath,
                        duration=metadata.get('duration', 0),
                        year=metadata.get('year', ''),
                        genre=metadata.get('genre', ''),
                        track_number=metadata.get('track_number', '')
                    )

                    # Update current track
                    self.current_track = next_track
                    self.is_playing = self.player_core.is_playing

                    # Notify listeners
                    if self.on_track_changed:
                        self.on_track_changed(next_track)
                    if self.on_playback_state_changed:
                        self.on_playback_state_changed(self.is_playing)

                    logger.info(f"Updated to next track: {next_track.title}")
                else:
                    logger.warning(f"No metadata found for next track: {next_filepath}")
            else:
                logger.warning("Failed to get next track filepath or file doesn't exist")
        except Exception as e:
            logger.error(f"Error in next track navigation: {e}")
            logger.error(traceback.format_exc())
            # Reset state
            self.is_playing = False
            if self.on_playback_state_changed:
                self.on_playback_state_changed(False)

    def previous(self) -> None:
        """
        Skip to the previous track in the queue.
        """
        try:
            if not self.queue_manager.get_queue_items():
                logger.warning("Cannot skip to previous track: queue is empty")
                return

            queue_items = self.queue_manager.get_queue_items()
            logger.info(f"Current queue has {len(queue_items)} items")

            current_filepath = None
            if self.current_track:
                current_filepath = self.current_track.path
                logger.info(f"Current track before previous: {os.path.basename(current_filepath)}")
            else:
                logger.info("No current track before previous")

            # Use the player core to go to the previous track
            self.player_core.previous_song()

            # Get the current media after navigation
            prev_filepath = None
            if self.player_core.media_player.get_media():
                prev_mrl = self.player_core.media_player.get_media().get_mrl()
                if prev_mrl:
                    prev_filepath = prev_mrl[7:] if prev_mrl.startswith('file://') else prev_mrl
                    # Decode URL-encoded characters
                    prev_filepath = unquote(prev_filepath)
                    logger.info(f"Previous filepath after navigation: {prev_filepath}")

            if prev_filepath and os.path.exists(prev_filepath):
                # Get track metadata
                metadata = self.db.get_metadata_by_filepath(prev_filepath)
                if metadata:
                    # Create a Track object
                    prev_track = Track(
                        id=metadata.get('id', ''),
                        title=metadata.get('title', os.path.basename(prev_filepath)),
                        artist=metadata.get('artist', ''),
                        album=metadata.get('album', ''),
                        path=prev_filepath,
                        duration=metadata.get('duration', 0),
                        year=metadata.get('year', ''),
                        genre=metadata.get('genre', ''),
                        track_number=metadata.get('track_number', '')
                    )

                    # Update current track
                    self.current_track = prev_track
                    self.is_playing = self.player_core.is_playing

                    # Notify listeners
                    if self.on_track_changed:
                        self.on_track_changed(prev_track)
                    if self.on_playback_state_changed:
                        self.on_playback_state_changed(self.is_playing)

                    logger.info(f"Updated to previous track: {prev_track.title}")
                else:
                    logger.warning(f"No metadata found for previous track: {prev_filepath}")
            else:
                logger.warning("Failed to get previous track filepath or file doesn't exist")
        except Exception as e:
            logger.error(f"Error in previous track navigation: {e}")
            logger.error(traceback.format_exc())
            # Reset state
            self.is_playing = False
            if self.on_playback_state_changed:
                self.on_playback_state_changed(False)

    def _on_track_end(self):
        """Handle track end event from player core."""
        logger.info("Track end event received")

        # Get updated track info if playback continued to next track
        if self.player_core.is_playing:
            logger.info("Playback continued to next track")
            current_media = self.player_core.media_player.get_media()
            if current_media:
                current_mrl = current_media.get_mrl()
                if current_mrl:
                    current_path = current_mrl[7:] if current_mrl.startswith('file://') else current_mrl
                    track_info = self.db.get_metadata_by_filepath(current_path)
                    if track_info:
                        # Update current track with new information
                        track_id = os.path.basename(current_path)
                        self.current_track = Track(
                            id=track_id,
                            title=track_info.get('title', 'Unknown Title'),
                            artist=track_info.get('artist', 'Unknown Artist'),
                            album=track_info.get('album', 'Unknown Album'),
                            path=current_path,
                            duration=track_info.get('length', 0),
                            year=track_info.get('year', ''),
                            genre=track_info.get('genre', ''),
                            track_number=track_info.get('track_num', 0)
                        )

                        logger.info("Track changed to: %s - %s", self.current_track.title, self.current_track.artist)

                        # Notify listeners
                        if self.on_track_changed:
                            self.on_track_changed(self.current_track)
                    else:
                        logger.warning("No metadata found for next track: %s", os.path.basename(current_path))
        else:
            # Playback stopped at end of queue
            logger.info("Playback stopped at end of queue")
            self.current_track = None
            if self.on_track_changed:
                self.on_track_changed(None)

        # Notify about playback state
        if self.on_playback_state_changed:
            logger.info("Notifying UI of playback state: is_playing=%s", self.player_core.is_playing)
            self.on_playback_state_changed(self.player_core.is_playing)

    def _on_track_info_updated(self):
        """Handle track info updated event from player core."""
        logger.debug("Track info updated event received")
        # This method is called by the player core when track information is updated

    def toggle_play(self):
        """Toggle play/pause state."""
        old_state = self.player_core.is_playing
        self.player_core.play_pause()
        new_state = self.player_core.is_playing
        logger.info("Toggle play called: is_playing changed from %s to %s", old_state, new_state)
        if self.on_playback_state_changed:
            self.on_playback_state_changed(self.player_core.is_playing)

    def set_position(self, position: int):
        """
        Set the playback position.

        Args:
            position: Position in milliseconds
        """
        self.player_core.seek(position)

    def set_volume(self, volume: float):
        """
        Set the player volume.

        Args:
            volume: Volume level from 0.0 to 1.0
        """
        # Convert from 0.0-1.0 to 0-100 for VLC
        volume_int = int(volume * 100)
        self.player_core.set_volume(volume_int)

    def toggle_loop(self):
        """Toggle loop playback mode."""
        self.player_core.toggle_loop()
        return self.player_core.loop_enabled

    def _update_current_track_from_filepath(self, filepath: str) -> bool:
        """
        Update the current_track property based on a filepath.

        Args:
            filepath: Path to the audio file

        Returns:
            bool: True if the track was updated successfully, False otherwise
        """
        if not filepath or not os.path.exists(filepath):
            logger.warning(f"Cannot update track info - file doesn't exist: {filepath}")
            return False

        try:
            # Get metadata from the database
            track_info = self.db.get_metadata_by_filepath(filepath)
            if track_info:
                # Create a Track object from the metadata
                track_id = os.path.basename(filepath)
                self.current_track = Track(
                    id=track_id,
                    title=track_info.get('title', 'Unknown Title'),
                    artist=track_info.get('artist', 'Unknown Artist'),
                    album=track_info.get('album', 'Unknown Album'),
                    path=filepath,
                    duration=track_info.get('duration', 0),
                    year=track_info.get('date', ''),
                    genre=track_info.get('genre', ''),
                    track_number=track_info.get('track_number', 0)
                )

                logger.info(f"Updated current track to: {self.current_track.title} - {self.current_track.artist}")

                # Notify listeners about the track change
                if self.on_track_changed:
                    self.on_track_changed(self.current_track)

                return True
            else:
                logger.warning(f"No metadata found for track: {os.path.basename(filepath)}")
        except Exception as e:
            logger.error(f"Error updating current track: {e}")
            traceback.print_exc()

        return False

    def set_up_queue(self, start_track_path=None):
        """
        Set up the queue with all tracks from the library, optionally starting from a specific track.

        This ensures that next/previous navigation works correctly by having all tracks in the queue.

        Args:
            start_track_path (str, optional): The path of the track to start the queue from.
                If None, starts from the beginning of the library.
        """
        try:
            # Get all tracks from the library using the correct method
            library_items = self.library_manager.get_library_items()
            if not library_items:
                logger.warning("No tracks in library to set up queue")
                return

            logger.info(f"Setting up queue with {len(library_items)} tracks from library")

            # Clear the current queue - use get_queue_items and remove_from_queue instead of clear_queue
            try:
                queue_items = self.queue_manager.get_queue_items()
                # Remove each item from queue
                for item in queue_items:
                    if item and len(item) > 0:
                        filepath = item[0]
                        if filepath:
                            self.queue_manager.remove_from_queue(filepath)
                logger.info("Queue cleared")
            except Exception as e:
                logger.warning(f"Could not clear queue: {e}")

            # If a specific start track is provided, reorganize the queue to start from that track
            if start_track_path:
                # Find the index of the start track
                start_index = -1
                for i, item in enumerate(library_items):
                    if item[0] == start_track_path:  # First element in tuple is filepath
                        start_index = i
                        break

                if start_index >= 0:
                    logger.info(f"Starting queue from track at index {start_index}: {os.path.basename(start_track_path)}")
                    # Rearrange tracks to start from the specified track
                    library_items = library_items[start_index:] + library_items[:start_index]
                else:
                    logger.warning(f"Start track not found in library: {start_track_path}")

            # Add all tracks to the queue
            for item in library_items:
                track_path = item[0]  # First element in tuple is filepath
                if track_path and os.path.exists(track_path):
                    # Add track to queue
                    self.queue_manager.add_to_queue(track_path)
                    logger.info(f"Added to queue: {os.path.basename(track_path)}")
                else:
                    logger.warning(f"Skipping invalid track path: {track_path}")

            logger.info(f"Queue set up with {len(self.queue_manager.get_queue_items())} tracks")

            # Update listeners that the queue has changed
            if self.on_track_changed:
                self.on_track_changed(self.current_track)
        except Exception as e:
            logger.error(f"Error setting up queue: {e}")
            logger.error(traceback.format_exc())
