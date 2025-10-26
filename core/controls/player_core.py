import os
import threading
import vlc
from config import BUTTON_SYMBOLS
from core.db import MusicDatabase
from core.logging import controls_logger, log_player_action
from core.queue import QueueManager
from eliot import start_action


class PlayerCore:
    def __init__(self, db: MusicDatabase, queue_manager: QueueManager, queue_view=None):
        self.db = db
        self.queue_manager = queue_manager
        self.queue_view = queue_view
        self.player = vlc.Instance()
        self.media_player = self.player.media_player_new()
        self.is_playing = False
        self.current_time = 0
        self.was_playing = False
        self.loop_enabled = self.db.get_loop_enabled()
        self.shuffle_enabled = self.queue_manager.is_shuffle_enabled()
        self.stop_after_current = False  # One-time flag to stop after current track (non-persistent)
        self.progress_bar = None
        self.window = None
        self.favorites_manager = None
        self.current_file = None  # Track currently playing file
        self.queue_handler = None  # Will be set by MusicPlayer
        self.active_view = None  # Will be set by MusicPlayer
        self._playback_lock = threading.RLock()  # Reentrant lock for thread-safe playback operations

        # Rate limiting state for playback operations
        self._rate_limit_state = {
            'next_song': {'last_time': 0, 'pending_timer': None},
            'previous_song': {'last_time': 0, 'pending_timer': None},
            'play_pause': {'last_time': 0, 'pending_timer': None},
        }

        # Set up end of track event handler
        self.media_player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self._on_track_end)

    def _check_rate_limit(self, method_name: str, min_interval: float) -> bool:
        """Check if method call should proceed based on rate limiting.

        Implements debouncing with trailing edge: if called too soon after last execution,
        schedules a pending call instead of executing immediately.

        Args:
            method_name: Name of the method being rate-limited
            min_interval: Minimum seconds between executions

        Returns:
            True if call should proceed immediately, False if throttled
        """
        import time

        state = self._rate_limit_state[method_name]
        current_time = time.time()
        time_since_last = current_time - state['last_time']

        # If enough time has passed, allow immediate execution
        if time_since_last >= min_interval:
            state['last_time'] = current_time

            # Cancel any pending timer since we're executing now
            if state['pending_timer'] is not None:
                state['pending_timer'].cancel()
                state['pending_timer'] = None

            log_player_action(
                "rate_limit_immediate",
                method_name=method_name,
                trigger_source="rate_limit",
                time_since_last=time_since_last,
                description=f"{method_name} executed immediately (sufficient time elapsed)"
            )
            return True

        # Too soon - schedule for later (debounce trailing edge)
        # Cancel any existing pending timer
        if state['pending_timer'] is not None:
            state['pending_timer'].cancel()

        # Schedule execution after minimum interval
        delay = min_interval - time_since_last

        def execute_pending():
            """Execute the pending call after delay."""
            # This will be called from timer thread, but method will acquire lock
            state['last_time'] = time.time()
            state['pending_timer'] = None

            # Call the actual method
            method = getattr(self, method_name)
            method()

        state['pending_timer'] = threading.Timer(delay, execute_pending)
        state['pending_timer'].daemon = True
        state['pending_timer'].start()

        log_player_action(
            "rate_limit_throttled",
            method_name=method_name,
            trigger_source="rate_limit",
            time_since_last=time_since_last,
            delay=delay,
            queued=True,
            description=f"{method_name} throttled, will execute in {delay:.3f}s"
        )
        return False

    def play_pause(self) -> None:
        """Toggle play/pause state."""
        with self._playback_lock:
            # Rate limiting: minimum 50ms between play/pause toggles
            if not self._check_rate_limit('play_pause', 0.05):
                return

            # Get current track info for logging
            current_track = self._get_current_track_info()
            track_display = f"{current_track.get('artist', 'Unknown')} - {current_track.get('title', 'Unknown')}" if current_track else "No track"

            try:
                from core.logging import controls_logger, log_player_action

                with start_action(controls_logger, "play_pause"):
                    log_player_action(
                        "play_pause_pressed",
                        trigger_source="gui",
                        old_state="playing" if self.is_playing else "paused",
                        new_state="paused" if self.is_playing else "playing",
                        track=track_display,
                        description=f"{'Pausing' if self.is_playing else 'Resuming'}: {track_display}"
                    )
            except ImportError:
                pass

            if not self.is_playing:
                if self.media_player.get_media() is not None:
                    self.media_player.play()
                    # Wait for media to be ready (shorter timeout since media already loaded)
                    self._wait_for_media_loaded(timeout=0.5)
                    self.is_playing = True
                    self._update_track_info()
                    # Refresh colors to update play/pause indicator
                    self._refresh_colors_callback()
                    # Update play button icon
                    if hasattr(self.progress_bar, 'controls') and hasattr(self.progress_bar.controls, 'update_play_button'):
                        self.progress_bar.controls.update_play_button(True)
                    try:
                        from core.logging import controls_logger
                        from eliot import log_message

                        log_message(message_type="playback_started", message="Playback resumed from pause")
                    except ImportError:
                        pass
                else:
                    if self.queue_manager.queue_items:
                        if self.queue_manager.current_index < 0:
                            self.queue_manager.current_index = 0
                        filepath = self.queue_manager.queue_items[self.queue_manager.current_index]
                        self._play_file(filepath)
                    else:
                        # Try to populate queue from current view (works in any library section)
                        if self.queue_handler:
                            # Get all tracks from current view
                            all_filepaths = self.queue_handler._get_all_filepaths_from_view()
                            if all_filepaths:
                                # Populate queue and play first track
                                track_to_play = self.queue_manager.populate_and_play(all_filepaths, 0)
                                if track_to_play:
                                    self._play_file(track_to_play)
                                    return
                        # Fallback: try to get current filepath
                        filepath = self._get_current_filepath()
                        if filepath:
                            self._play_file(filepath)
            else:
                self.current_time = self.media_player.get_time()
                self.media_player.pause()
                self.is_playing = False
                # Refresh colors to update play/pause indicator
                self._refresh_colors_callback()
                # Update play button icon
                if hasattr(self.progress_bar, 'controls') and hasattr(self.progress_bar.controls, 'update_play_button'):
                    self.progress_bar.controls.update_play_button(False)
                try:
                    from core.logging import controls_logger
                    from eliot import log_message

                    log_message(message_type="playback_paused", message="Playback paused")
                except ImportError:
                    pass

    def next_song(self) -> None:
        """Play the next song in the queue."""
        with self._playback_lock:
            # Rate limiting: minimum 100ms between next() calls
            if not self._check_rate_limit('next_song', 0.1):
                return

            # Defensive check: ensure queue has items
            if not self.queue_manager.queue_items:
                log_player_action(
                    "next_song_no_queue",
                    trigger_source="gui",
                    reason="queue_empty",
                    description="Next button pressed but queue is empty"
                )
                return

            with start_action(controls_logger, "next_song"):
                # Get current track info for logging
                current_track_info = self._get_current_track_info()
                current_display = f"{current_track_info.get('artist', 'Unknown')} - {current_track_info.get('title', 'Unknown')}" if current_track_info else "No track"

                log_player_action(
                    "next_pressed",
                    trigger_source="gui",
                    current_track=current_display,
                    queue_has_loop=self.loop_enabled,
                    description=f"Next button pressed (currently playing: {current_display})"
                )

                if not self.loop_enabled and self._is_last_song():
                    log_player_action(
                        "next_song_stopped",
                        trigger_source="gui",
                        reason="last_song_and_loop_disabled",
                        current_track=current_track_info,
                    )
                    self.stop("end_of_queue")
                    return

                # In loop mode with shuffle disabled, use carousel mode (move track to end)
                # With shuffle enabled, use shuffle navigation which handles looping internally
                if self.loop_enabled and not self.shuffle_enabled and self.queue_manager.queue_items:
                    # Use atomic operation to prevent race condition
                    filepath = self.queue_manager.move_current_to_end_and_get_next()
                else:
                    filepath = self._get_next_filepath()

                # Defensive check: validate filepath before playing
                if not filepath:
                    log_player_action(
                        "next_song_no_filepath",
                        trigger_source="gui",
                        reason="no_next_track",
                        description="No filepath returned from queue navigation"
                    )
                    return

                # Get target track info after navigation (after queue update)
                target_metadata = self.db.get_metadata_by_filepath(filepath) if self.db else {}
                target_display = f"{target_metadata.get('artist', 'Unknown')} - {target_metadata.get('title', os.path.basename(filepath))}"

                log_player_action(
                    "next_track_selected",
                    trigger_source="gui",
                    next_track=target_display,
                    filepath=filepath,
                    description=f"Playing next: {target_display}"
                )

                self._play_file(filepath)

    def previous_song(self) -> None:
        """Play the previous song in the queue."""
        with self._playback_lock:
            # Rate limiting: minimum 100ms between previous() calls
            if not self._check_rate_limit('previous_song', 0.1):
                return

            # Defensive check: ensure queue has items
            if not self.queue_manager.queue_items:
                log_player_action(
                    "previous_song_no_queue",
                    trigger_source="gui",
                    reason="queue_empty",
                    description="Previous button pressed but queue is empty"
                )
                return

            with start_action(controls_logger, "previous_song"):
                # Get current track info for logging
                current_track_info = self._get_current_track_info()
                current_display = f"{current_track_info.get('artist', 'Unknown')} - {current_track_info.get('title', 'Unknown')}" if current_track_info else "No track"

                log_player_action(
                    "previous_pressed",
                    trigger_source="gui",
                    current_track=current_display,
                    description=f"Previous button pressed (currently playing: {current_display})"
                )

                # In loop mode with shuffle disabled, use reverse carousel mode (move last to beginning)
                # With shuffle enabled, use shuffle navigation which handles looping internally
                if self.loop_enabled and not self.shuffle_enabled and self.queue_manager.queue_items:
                    self.queue_manager.move_last_to_beginning()
                    # After moving last to beginning, it becomes the current track at index 0
                    filepath = self.queue_manager.queue_items[0] if self.queue_manager.queue_items else None
                else:
                    filepath = self._get_previous_filepath()

                # Defensive check: validate filepath before playing
                if not filepath:
                    log_player_action(
                        "previous_song_no_filepath",
                        trigger_source="gui",
                        reason="no_previous_track",
                        description="No filepath returned from queue navigation"
                    )
                    return

                # Get target track info after navigation (after queue update)
                target_metadata = self.db.get_metadata_by_filepath(filepath) if self.db else {}
                target_display = f"{target_metadata.get('artist', 'Unknown')} - {target_metadata.get('title', os.path.basename(filepath))}"

                log_player_action(
                    "previous_track_selected",
                    trigger_source="gui",
                    previous_track=target_display,
                    filepath=filepath,
                    description=f"Playing previous: {target_display}"
                )

                self._play_file(filepath)

    def seek(self, position: float, source: str = "progress_bar", interaction_type: str = "click") -> None:
        """Seek to a position in the current track (0.0 to 1.0)."""
        with start_action(controls_logger, "seek_operation"):
            if self.media_player.get_length() > 0:
                # Get current time before seeking
                old_time = self.media_player.get_time()
                new_time = int(self.media_player.get_length() * position)
                duration = self.media_player.get_length()

                # Get current track info
                current_track_info = self._get_current_track_info()

                log_player_action(
                    "seek_operation",
                    trigger_source=source,
                    interaction_type=interaction_type,
                    old_position=old_time,
                    new_position=new_time,
                    seek_percentage=f"{position:.1%}",
                    duration=duration,
                    current_track=current_track_info,
                    description=f"Seeked to {position:.1%} via {interaction_type} on {source}",
                )

                self.media_player.set_time(new_time)
            else:
                log_player_action(
                    "seek_operation_failed",
                    trigger_source=source,
                    reason="no_duration",
                    current_track=self._get_current_track_info(),
                )

    def seek_to_time(self, time_seconds: float, source: str = "api", timeout: float = 2.0) -> bool:
        """Seek to an absolute time position in seconds with verification.

        Args:
            time_seconds: Target position in seconds
            source: Source of the seek operation (for logging)
            timeout: Maximum time to wait for seek completion (default 2s)

        Returns:
            True if seek completed successfully, False otherwise
        """
        with start_action(controls_logger, "seek_to_time_operation"):
            duration_ms = self.media_player.get_length()
            if duration_ms <= 0:
                log_player_action(
                    "seek_to_time_failed",
                    trigger_source=source,
                    reason="no_duration",
                    current_track=self._get_current_track_info(),
                )
                return False

            # Convert seconds to milliseconds
            target_time_ms = int(time_seconds * 1000)

            # Clamp to valid range
            target_time_ms = max(0, min(target_time_ms, duration_ms))

            # Get current time before seeking
            old_time_ms = self.media_player.get_time()

            log_player_action(
                "seek_to_time_operation",
                trigger_source=source,
                old_position_ms=old_time_ms,
                target_position_ms=target_time_ms,
                target_position_seconds=time_seconds,
                duration_ms=duration_ms,
                current_track=self._get_current_track_info(),
                description=f"Seeking to {time_seconds}s ({target_time_ms}ms) via {source}",
            )

            # Perform seek
            self.media_player.set_time(target_time_ms)

            # Poll to verify seek completed (tolerance: ±500ms)
            import time

            tolerance_ms = 500
            poll_interval = 0.05  # 50ms
            elapsed = 0.0

            while elapsed < timeout:
                time.sleep(poll_interval)
                elapsed += poll_interval

                current_time_ms = self.media_player.get_time()
                diff = abs(current_time_ms - target_time_ms)

                if diff <= tolerance_ms:
                    log_player_action(
                        "seek_to_time_verified",
                        trigger_source=source,
                        target_position_ms=target_time_ms,
                        actual_position_ms=current_time_ms,
                        time_taken=elapsed,
                        description=f"Seek verified after {elapsed:.2f}s",
                    )
                    return True

            # Timeout reached
            final_time_ms = self.media_player.get_time()
            log_player_action(
                "seek_to_time_timeout",
                trigger_source=source,
                target_position_ms=target_time_ms,
                actual_position_ms=final_time_ms,
                timeout=timeout,
                description=f"Seek verification timed out after {timeout}s",
            )
            return False

    def stop(self, reason: str = "user_initiated") -> None:
        """Stop playback."""
        with self._playback_lock, start_action(controls_logger, "stop_playback"):
            # Get current track info before stopping
            current_track_info = self._get_current_track_info()

            log_player_action(
                "stop_playback",
                trigger_source="gui" if reason == "user_initiated" else "automatic",
                stop_reason=reason,
                current_track=current_track_info,
                was_playing=self.is_playing,
                description=f"Playback stopped: {reason.replace('_', ' ')}",
            )

            self.media_player.stop()
            # Clear media from VLC to ensure clean state
            self.media_player.set_media(None)
            self.is_playing = False
            self.current_time = 0
            self.current_file = None  # Clear current file on stop

            # Hide playback elements in progress bar
            if self.progress_bar:
                self.progress_bar.clear_track_info()
                if hasattr(self.progress_bar, 'progress_control'):
                    self.progress_bar.progress_control.hide_playback_elements()
                    # Reset the time display to default state when stopping
                    self.progress_bar.progress_control.update_time_display("00:00", "00:00")
                if hasattr(self.progress_bar, 'controls') and hasattr(self.progress_bar.controls, 'update_play_button'):
                    self.progress_bar.controls.update_play_button(False)
                # Clear favorite button state when stopping
                if hasattr(self.progress_bar, 'controls') and hasattr(self.progress_bar.controls, 'update_favorite_button'):
                    self.progress_bar.controls.update_favorite_button(False)

            # Refresh Now Playing view to show empty state if queue is empty
            if hasattr(self, 'on_track_change') and callable(self.on_track_change):
                self.on_track_change()

    def toggle_loop(self) -> None:
        """Toggle loop mode."""
        with start_action(controls_logger, "toggle_loop"):
            old_state = self.loop_enabled
            new_state = not old_state

            log_player_action(
                "toggle_loop",
                trigger_source="gui",
                old_state=old_state,
                new_state=new_state,
                description=f"Loop mode {'enabled' if new_state else 'disabled'}",
            )

            self.loop_enabled = new_state
            self.db.set_loop_enabled(self.loop_enabled)
            if self.progress_bar and hasattr(self.progress_bar, 'controls'):
                self.progress_bar.controls.update_loop_button_color(self.loop_enabled)

            # Refresh Now Playing view to update track display based on loop state
            if hasattr(self, 'on_track_change') and callable(self.on_track_change):
                self.on_track_change()

    def toggle_shuffle(self) -> None:
        """Toggle shuffle mode."""
        with start_action(controls_logger, "toggle_shuffle"):
            old_state = self.shuffle_enabled
            new_state = self.queue_manager.toggle_shuffle()

            log_player_action(
                "toggle_shuffle",
                trigger_source="gui",
                old_state=old_state,
                new_state=new_state,
                description=f"Shuffle mode {'enabled' if new_state else 'disabled'}",
            )

            self.shuffle_enabled = new_state
            if self.progress_bar and hasattr(self.progress_bar, 'controls'):
                self.progress_bar.controls.update_shuffle_button_color(self.shuffle_enabled)

            # Refresh Now Playing view to show shuffled/unshuffled order
            if hasattr(self, 'on_track_change') and callable(self.on_track_change):
                self.on_track_change()

    def toggle_stop_after_current(self) -> bool:
        """Toggle stop-after-current flag.

        Returns:
            bool: New state of stop_after_current flag
        """
        with start_action(controls_logger, "toggle_stop_after_current"):
            old_state = self.stop_after_current
            self.stop_after_current = not self.stop_after_current

            log_player_action(
                "toggle_stop_after_current",
                trigger_source="gui",
                old_state=old_state,
                new_state=self.stop_after_current,
                description=f"Stop after current {'enabled' if self.stop_after_current else 'disabled'}",
            )

            return self.stop_after_current

    def get_current_time(self) -> int:
        """Get current playback time in milliseconds."""
        return self.media_player.get_time()

    def get_duration(self) -> int:
        """Get total duration of current track in milliseconds."""
        return self.media_player.get_length()

    def get_volume(self) -> int:
        """Get current volume (0-100)."""
        return self.media_player.audio_get_volume()

    def set_volume(self, volume: int) -> None:
        """Set volume (0-100)."""
        try:
            # Ensure volume is within valid range
            volume = max(0, min(100, int(volume)))
            result = self.media_player.audio_set_volume(volume)
            return result
        except Exception as e:
            from eliot import log_message
            log_message(message_type="volume_set_error", error=str(e), attempted_volume=volume)
            return -1

    def cleanup_vlc(self) -> None:
        """Clean up VLC resources to prevent leaks.

        Releases VLC media player and instance resources. Should be called
        between tests or when shutting down the player.
        """
        with self._playback_lock:
            try:
                # Stop playback first
                if self.is_playing:
                    self.media_player.stop()
                    self.is_playing = False

                # Clear media
                self.media_player.set_media(None)

                # Release media player resources
                if self.media_player:
                    self.media_player.release()

                # Release VLC instance resources
                if self.player:
                    self.player.release()

                # Clear references
                self.current_file = None
                self.current_time = 0

                log_player_action(
                    "vlc_cleanup",
                    trigger_source="cleanup",
                    description="VLC resources released"
                )
            except Exception as e:
                from eliot import log_message
                log_message(message_type="vlc_cleanup_error", error=str(e))

    def _wait_for_media_loaded(self, timeout: float = 2.0) -> bool:
        """Wait for VLC media to be loaded after play() call.

        Args:
            timeout: Maximum time to wait in seconds (default: 2.0)

        Returns:
            bool: True if media loaded successfully, False if timeout
        """
        import time

        start_time = time.time()
        poll_interval = 0.05  # Poll every 50ms

        while time.time() - start_time < timeout:
            media = self.media_player.get_media()
            if media is not None:
                mrl = media.get_mrl()
                if mrl:
                    return True
            time.sleep(poll_interval)

        # Timeout - media didn't load
        return False

    def _play_file(self, filepath: str) -> None:
        """Play a specific file."""
        with self._playback_lock:
            # Defensive check: file must exist
            if not os.path.exists(filepath):
                from eliot import log_message
                log_message(message_type="file_not_found", filepath=filepath)
                return

            # Get track metadata for logging
            track_metadata = self.db.get_metadata_by_filepath(filepath) if self.db else {}
            track_title = track_metadata.get('title', os.path.basename(filepath))
            track_artist = track_metadata.get('artist', 'Unknown')
            track_album = track_metadata.get('album', 'Unknown')

            with start_action(controls_logger, "play_file"):
                log_player_action(
                    "playback_started",
                    trigger_source="gui",
                    filepath=filepath,
                    title=track_title,
                    artist=track_artist,
                    album=track_album,
                    description=f"Started playing: {track_artist} - {track_title}"
                )

            # Store the filepath immediately for reliable access
            self.current_file = filepath

            # Reset play count tracking for new track
            if hasattr(self, 'play_count_updated_callback') and self.play_count_updated_callback:
                self.play_count_updated_callback(False)

            # Store the current volume before changing media
            current_volume = self.get_volume()

            media = self.player.media_new(filepath)
            self.media_player.set_media(media)
            self.media_player.play()

            # Wait for VLC to load the media asynchronously
            if not self._wait_for_media_loaded(timeout=2.0):
                print(f"Warning: Media loading timeout for {filepath}")

            self.media_player.set_time(0)  # Ensure track starts from beginning
            self.current_time = 0
            self.is_playing = True

            # Restore volume after media change (including 0% for muted state)
            self.set_volume(current_volume)

            # Find and select the corresponding item in the queue view
            self._select_item_by_filepath(filepath)

            # Update track info in UI
            self._update_track_info()

            # Show playback elements in progress bar
            if self.progress_bar and hasattr(self.progress_bar, 'progress_control'):
                self.progress_bar.progress_control.show_playback_elements()

            # Update play button to pause symbol since we're now playing
            if (
                self.progress_bar
                and hasattr(self.progress_bar, 'controls')
                and hasattr(self.progress_bar.controls, 'update_play_button')
            ):
                self.progress_bar.controls.update_play_button(True)

            # Update favorite button icon based on track's favorite status
            if self.favorites_manager and self.progress_bar and hasattr(self.progress_bar, 'controls'):
                is_favorite = self.favorites_manager.is_favorite(filepath)
                self.progress_bar.controls.update_favorite_button(is_favorite)

            # Notify track change for view updates
            if hasattr(self, 'on_track_change') and callable(self.on_track_change):
                self.on_track_change()

    def _select_item_by_filepath(self, filepath: str) -> None:
        """Find and select the item in the queue view that corresponds to the given filepath."""
        if not self.queue_view or not filepath:
            return

        # Get the metadata for the file
        metadata = self.db.get_metadata_by_filepath(filepath)
        if not metadata:
            return

        # Find the corresponding item in the queue view
        for item in self.queue_view.get_children():
            values = self.queue_view.item(item)['values']
            if not values or len(values) < 3:
                continue

            # Values are: track, title, artist, album, year
            track, title, artist, album, year = values[:5]

            # Check if this item matches the metadata
            if title == metadata.get('title') and artist == metadata.get('artist'):
                # Found the matching item - select it and make it visible
                self.queue_view.selection_set(item)
                self.queue_view.see(item)

                # Also tell the player to refresh colors to highlight this item
                if hasattr(self, 'window') and self.window:
                    # Schedule the refresh_colors call using the event loop
                    # Use a faster refresh (50ms) to ensure highlighting happens quickly
                    self.window.after(50, self._refresh_colors_callback)
                break

    def _refresh_colors_callback(self):
        """Callback to refresh colors in the player."""
        # Find the MusicPlayer instance
        for child in self.window.winfo_children():
            if hasattr(child, 'refresh_colors'):
                child.refresh_colors()
                break

    def _update_track_info(self) -> None:
        """Update track info in progress bar based on current file."""
        if not self.progress_bar:
            return

        # Use current_file to get track info from database
        if self.current_file and self.db:
            track_data = self.db.get_track_by_filepath(self.current_file)
            if track_data:
                artist, title, album, track_number, date = track_data
                # Provide fallback values if artist or title are empty
                artist = artist or "Unknown Artist"
                title = title or "Unknown Title"
                self.progress_bar.update_track_info(title=title, artist=artist)
            else:
                # Track not found in database - try to use filename
                import os

                filename = os.path.basename(self.current_file)
                self.progress_bar.update_track_info(title=filename, artist="Unknown Artist")
        else:
            self.progress_bar.clear_track_info()

    def _get_current_filepath(self) -> str | None:
        """Get filepath of current song."""
        children = self.queue_view.get_children()
        if not children:
            return None

        current_selection = self.queue_view.selection()
        # If nothing is selected, start with the first item
        item = children[0] if not current_selection else current_selection[0]

        values = self.queue_view.item(item)['values']
        if not values:
            return None

        track_num, title, artist, album, year = values
        return self.db.find_file_by_metadata(title, artist, album, track_num)

    def _get_next_filepath(self) -> str | None:
        """Get filepath of next song using in-memory queue."""
        return self.queue_manager.next_track()

    def _get_previous_filepath(self) -> str | None:
        """Get filepath of previous song using in-memory queue."""
        return self.queue_manager.previous_track()

    def _is_last_song(self) -> bool:
        """Check if current song is last in queue using in-memory queue."""
        if not self.queue_manager.queue_items:
            return True
        return self.queue_manager.current_index == len(self.queue_manager.queue_items) - 1

    def _get_current_track_info(self) -> dict[str, any]:
        """Get current track information for logging."""
        current_selection = self.queue_view.selection()
        if not current_selection:
            return {"track": "none", "index": -1}

        current_item = current_selection[0]
        children = self.queue_view.get_children()
        current_index = children.index(current_item) if current_item in children else -1

        values = self.queue_view.item(current_item).get('values', [])
        if len(values) >= 4:
            track_num, title, artist, album = values[0:4]

            track_info = {
                "track_num": track_num,
                "title": title,
                "artist": artist,
                "album": album,
                "queue_index": current_index,
                "queue_position": f"{current_index + 1}/{len(children)}",
            }

            # Use current_file as the reliable source for filepath
            # This is set immediately when playback starts, before VLC finishes loading
            if self.current_file:
                track_info["filepath"] = self.current_file
            else:
                # Fallback: try to get filepath from VLC media player
                media = self.media_player.get_media()
                if media:
                    mrl = media.get_mrl()
                    # Convert file:// URL to normal path
                    if mrl and mrl.startswith('file://'):
                        from urllib.parse import unquote

                        filepath = unquote(mrl[7:])  # Remove 'file://' prefix
                        track_info["filepath"] = filepath

            return track_info
        else:
            return {"track": "unknown", "index": current_index}

    def _on_track_end(self, event):
        """Handle end of track event by scheduling the next action in the main thread."""
        if self.window:
            # Schedule the handler in the main thread since VLC calls this from its own thread
            self.window.after(0, self._handle_track_end)

    def _handle_track_end(self):
        """Handle track end in the main thread."""
        with self._playback_lock:
            # Defensive check: only proceed if we were actually playing
            # This prevents double-triggering of track end events
            if not self.is_playing:
                log_player_action(
                    "track_end_ignored",
                    trigger_source="automatic",
                    reason="not_playing",
                    description="Track end event ignored because player is not in playing state"
                )
                return

            # Check stop_after_current flag first (highest priority)
            if self.stop_after_current:
                # Stop playback and reset the flag
                self.stop_after_current = False
                self.stop("stop_after_current")
                log_player_action(
                    "stop_after_current_triggered",
                    trigger_source="automatic",
                    description="Stopped playback after current track as requested",
                )
                return

            if self.loop_enabled:
                # If loop is enabled, play the next track (or first if at end)
                self.next_song()
            else:
                # If loop is disabled, remove current track from queue and advance
                # This creates a linear playback where tracks disappear after playing
                if self._is_last_song():
                    # Last track - remove it and stop
                    self.queue_manager.remove_from_queue_at_index(self.queue_manager.current_index)
                    self.stop("end_of_queue")
                    # Explicitly refresh Now Playing view when queue becomes empty
                    if hasattr(self, 'on_track_change') and callable(self.on_track_change):
                        self.on_track_change()
                else:
                    # Not last track - remove current track and play next
                    # After removing current track, the next track is now at current_index
                    self.queue_manager.remove_from_queue_at_index(self.queue_manager.current_index)
                    filepath = self._get_next_filepath()
                    if filepath:
                        self._play_file(filepath)
                    else:
                        self.stop("queue_exhausted")

            # Update UI elements
            if self.progress_bar and hasattr(self.progress_bar, 'controls'):
                self.progress_bar.controls.play_button.configure(
                    text=BUTTON_SYMBOLS['pause'] if self.is_playing else BUTTON_SYMBOLS['play']
                )
