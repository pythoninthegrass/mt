import os
import tkinter as tk
import vlc
from config import BUTTON_SYMBOLS
from core.db import MusicDatabase
from core.logging import controls_logger, log_error, log_player_action
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
        self.progress_bar = None
        self.window = None
        self.favorites_manager = None
        self.current_file = None  # Track currently playing file

        # Set up end of track event handler
        self.media_player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self._on_track_end)

    def play_pause(self) -> None:
        """Toggle play/pause state."""
        try:
            from core.logging import controls_logger, log_player_action

            with start_action(controls_logger, "play_pause"):
                log_player_action("play_pause", current_state=self.is_playing)
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
                try:
                    from core.logging import controls_logger
                    from eliot import log_message

                    log_message(message_type="playback_started", message="Playback resumed from pause")
                except ImportError:
                    pass
            else:
                filepath = self._get_current_filepath()
                if filepath:
                    self._play_file(filepath)
        else:
            self.current_time = self.media_player.get_time()
            self.media_player.pause()
            self.is_playing = False
            # Refresh colors to update play/pause indicator
            self._refresh_colors_callback()
            try:
                from core.logging import controls_logger
                from eliot import log_message

                log_message(message_type="playback_paused", message="Playback paused")
            except ImportError:
                pass

    def next_song(self) -> None:
        """Play the next song in the queue."""
        with start_action(controls_logger, "next_song"):
            # Get current track info for logging
            current_track_info = self._get_current_track_info()

            log_player_action(
                "next_song", trigger_source="gui", current_track=current_track_info, queue_has_loop=self.loop_enabled
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

            filepath = self._get_next_filepath()

            # Get target track info after navigation
            target_track_info = self._get_current_track_info()

            log_player_action("next_song_selected", trigger_source="gui", target_track=target_track_info, filepath=filepath)

            if filepath:
                self._play_file(filepath)

    def previous_song(self) -> None:
        """Play the previous song in the queue."""
        with start_action(controls_logger, "previous_song"):
            # Get current track info for logging
            current_track_info = self._get_current_track_info()

            log_player_action("previous_song", trigger_source="gui", current_track=current_track_info)

            filepath = self._get_previous_filepath()

            # Get target track info after navigation
            target_track_info = self._get_current_track_info()

            log_player_action("previous_song_selected", trigger_source="gui", target_track=target_track_info, filepath=filepath)

            if filepath:
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

    def seek_to_time(
        self, 
        time_seconds: float, 
        source: str = "api", 
        timeout: float = 2.0
    ) -> bool:
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
        with start_action(controls_logger, "stop_playback"):
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
                if hasattr(self.progress_bar, 'controls') and hasattr(self.progress_bar.controls, 'update_play_button'):
                    self.progress_bar.controls.update_play_button(False)

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
        print(f"PlayerCore: Setting volume to {volume}")  # Debug log
        try:
            # Ensure volume is within valid range
            volume = max(0, min(100, int(volume)))
            result = self.media_player.audio_set_volume(volume)
            print(f"VLC set_volume result: {result}")  # Debug result
            return result
        except Exception as e:
            print(f"Exception in set_volume: {e}")
            return -1

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
        if not os.path.exists(filepath):
            print(f"File not found on disk: {filepath}")
            return

        # Store the filepath immediately for reliable access
        self.current_file = filepath

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

        # Restore volume after media change
        self.set_volume(current_volume if current_volume > 0 else 80)

        # Find and select the corresponding item in the queue view
        self._select_item_by_filepath(filepath)

        # Update track info in UI
        self._update_track_info()

        # Show playback elements in progress bar
        if self.progress_bar and hasattr(self.progress_bar, 'progress_control'):
            self.progress_bar.progress_control.show_playback_elements()

        # Update play button to pause symbol since we're now playing
        if self.progress_bar and hasattr(self.progress_bar, 'controls') and hasattr(self.progress_bar.controls, 'update_play_button'):
            self.progress_bar.controls.update_play_button(True)
        
        # Update favorite button icon based on track's favorite status
        if self.favorites_manager and self.progress_bar and hasattr(self.progress_bar, 'controls'):
            is_favorite = self.favorites_manager.is_favorite(filepath)
            self.progress_bar.controls.update_favorite_button(is_favorite)

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
                print("Calling refresh_colors from PlayerCore")  # Debug log
                child.refresh_colors()
                break

    def _update_track_info(self) -> None:
        """Update track info in progress bar based on current selection."""
        if not self.progress_bar or not self.queue_view:
            return

        current_selection = self.queue_view.selection()
        if current_selection:
            values = self.queue_view.item(current_selection[0])['values']
            if values and len(values) >= 3:
                # Queue view columns are: track, title, artist, album, year
                track_num, title, artist, album, year = values
                # We should always have values since we set defaults in _populate_queue_view
                self.progress_bar.update_track_info(title=title, artist=artist)
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
        """Get filepath of next song."""
        children = self.queue_view.get_children()
        if not children:
            print("No children in queue")  # Debug log
            return None

        current_selection = self.queue_view.selection()
        if not current_selection:
            # If nothing is selected, start with the first item
            print("No selection, starting with first item")  # Debug log
            next_index = 0
        else:
            current_index = children.index(current_selection[0])
            print(f"Current index: {current_index}")  # Debug log
            # If loop is disabled and on the last song, then stop playback
            if not self.loop_enabled and current_index == len(children) - 1 and not self.shuffle_enabled:
                print("Last song and loop disabled")  # Debug log
                return None

            # Use QueueManager to get next track index (handles shuffle)
            next_index = self.queue_manager.get_next_track_index(current_index, len(children))
            if next_index is None:
                return None
            print(f"Next index: {next_index}")  # Debug log

        next_item = children[next_index]
        self.queue_view.selection_set(next_item)
        self.queue_view.see(next_item)

        values = self.queue_view.item(next_item)['values']
        if not values:
            print("No values for next item")  # Debug log
            return None

        track_num, title, artist, album, year = values
        return self.db.find_file_by_metadata(title, artist, album, track_num)

    def _get_previous_filepath(self) -> str | None:
        """Get filepath of previous song."""
        children = self.queue_view.get_children()
        if not children:
            print("No children in queue")  # Debug log
            return None

        current_selection = self.queue_view.selection()
        if not current_selection:
            # If nothing is selected, start with the last item
            print("No selection, starting with last item")  # Debug log
            prev_index = len(children) - 1
        else:
            current_index = children.index(current_selection[0])
            print(f"Current index: {current_index}")  # Debug log
            # Use QueueManager to get previous track index (handles shuffle)
            prev_index = self.queue_manager.get_previous_track_index(current_index, len(children))
            if prev_index is None:
                return None
            print(f"Previous index: {prev_index}")  # Debug log

        prev_item = children[prev_index]
        self.queue_view.selection_set(prev_item)
        self.queue_view.see(prev_item)

        values = self.queue_view.item(prev_item)['values']
        if not values:
            print("No values for previous item")  # Debug log
            return None

        track_num, title, artist, album, year = values
        return self.db.find_file_by_metadata(title, artist, album, track_num)

    def _is_last_song(self) -> bool:
        """Check if current song is last in queue."""
        children = self.queue_view.get_children()
        if not children:
            return True

        current_selection = self.queue_view.selection()
        if not current_selection:
            return False

        current_index = children.index(current_selection[0])
        return current_index == len(children) - 1

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
        if self.loop_enabled:
            # If loop is enabled, play the next track (or first if at end)
            self.next_song()
        else:
            # If loop is disabled and we're at the last track, stop playback
            if self._is_last_song():
                self.stop("end_of_track")
            else:
                self.next_song()

        # Update UI elements
        if self.progress_bar and hasattr(self.progress_bar, 'controls'):
            self.progress_bar.controls.play_button.configure(
                text=BUTTON_SYMBOLS['pause'] if self.is_playing else BUTTON_SYMBOLS['play']
            )
