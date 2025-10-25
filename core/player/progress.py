"""Progress bar management for the music player - handles progress display, seeking, and volume."""

import time
from config import PROGRESS_BAR
from core.logging import log_player_action, player_logger
from eliot import start_action


class PlayerProgressController:
    """Manages progress bar interactions, seeking, and volume control."""

    def __init__(self, window, db, player_core, progress_bar, queue_view, load_recently_played_callback):
        """Initialize the progress controller.

        Args:
            window: The main Tkinter window
            db: Database instance
            player_core: PlayerCore instance
            progress_bar: ProgressBar instance
            queue_view: QueueView instance
            load_recently_played_callback: Callback to reload recently played view
        """
        self.window = window
        self.db = db
        self.player_core = player_core
        self.progress_bar = progress_bar
        self.queue_view = queue_view
        self.load_recently_played = load_recently_played_callback
        self.play_count_updated = False

    def set_play_count_updated(self, value: bool):
        """Set the play count updated flag.

        Args:
            value: True if play count has been updated for current track
        """
        self.play_count_updated = value

    def update_progress(self):
        """Update progress bar position and time display."""
        current_time = time.time()

        # If we're currently dragging, don't update UI elements
        # This ensures the user's drag action takes precedence over timer-based updates
        if self.progress_bar.dragging:
            # Just schedule the next update and return
            self.window.after(100, self.update_progress)
            return

        # Use the normal player position if we're playing and not recently dragged
        elif (
            self.player_core.is_playing
            and self.player_core.media_player.is_playing()
            and not self.progress_bar.dragging
            and (current_time - self.progress_bar.last_drag_time) > 0.5
        ):
            current = self.player_core.get_current_time()
            duration = self.player_core.get_duration()

            if duration > 0:
                ratio = current / duration

                # Use the progress control's update_progress method
                self.progress_bar.progress_control.update_progress(ratio)

                # Update time display
                current_time_fmt = self._format_time(current / 1000)
                total_time_fmt = self._format_time(duration / 1000)
                self.progress_bar.progress_control.update_time_display(current_time_fmt, total_time_fmt)

                # Update play count once track reaches 90% completion
                if ratio >= 0.9 and not self.play_count_updated and self.player_core.current_file:
                    self.db.update_play_count(self.player_core.current_file)
                    self.play_count_updated = True

                    # Refresh Recently Played view if it's currently active
                    if hasattr(self.queue_view, 'current_view') and self.queue_view.current_view == 'recently_played':
                        self.load_recently_played()

        self.window.after(100, self.update_progress)

    def _format_time(self, seconds):
        """Format time in seconds to MM:SS format."""
        seconds = int(seconds)
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def start_drag(self, event):
        """Start dragging the progress circle."""
        self.progress_bar.dragging = True
        self.progress_bar.last_drag_time = time.time()
        self.player_core.was_playing = self.player_core.is_playing
        if self.player_core.is_playing:
            self.player_core.media_player.pause()
            self.progress_bar.controls.update_play_button(False)
            self.player_core.is_playing = False

    def drag(self, event):
        """Handle progress circle drag."""
        if self.progress_bar.dragging:
            # Update last drag time to prevent progress updates immediately after dragging
            self.progress_bar.last_drag_time = time.time()

            controls_width = self.progress_bar.controls_width
            # Calculate max width for progress bar (consistent with other methods)
            # 380 = space for time display (160) + volume control (110) + utility buttons (~110)
            max_width = self.progress_bar.canvas.winfo_width() - 380

            # Constrain x to valid range
            x = max(controls_width, min(event.x, max_width))

            # Calculate ratio for later use (needed for time display)
            width = max_width - controls_width
            ratio = (x - controls_width) / width
            ratio = max(0, min(ratio, 1))  # Constrain to 0-1

            # Update circle position
            circle_radius = self.progress_bar.circle_radius
            bar_y = self.progress_bar.bar_y
            self.progress_bar.canvas.coords(
                self.progress_bar.progress_circle,
                x - circle_radius,
                bar_y - circle_radius,
                x + circle_radius,
                bar_y + circle_radius,
            )

            # Update progress line coordinates (from start to current position)
            self.progress_bar.canvas.coords(self.progress_bar.progress_line, controls_width, bar_y, x, bar_y)

            # Calculate and update the time display during drag for better feedback
            if self.player_core.media_player.get_length() > 0:
                duration = self.player_core.get_duration()
                current_time_ms = int(duration * ratio)

                # Update time display in real time
                current_time = self._format_time(current_time_ms / 1000)
                total_time = self._format_time(duration / 1000)
                self.progress_bar.progress_control.update_time_display(current_time, total_time)

    def end_drag(self, event):
        """End dragging the progress circle and seek to the position."""
        if self.progress_bar.dragging:
            # Set dragging to false AFTER we've done all calculations
            # to prevent race conditions with progress updates

            # Calculate seek ratio using consistent boundaries
            # 380 = space for time display (160) + volume control (110) + utility buttons (~110)
            max_width = self.progress_bar.canvas.winfo_width() - 380
            width = max_width - self.progress_bar.controls_width

            # Constrain x within valid range
            x = min(max(event.x, self.progress_bar.controls_width), max_width)

            # Calculate final ratio
            ratio = (x - self.progress_bar.controls_width) / width
            ratio = max(0, min(ratio, 1))  # Ensure ratio is between 0 and 1

            # Update UI immediately (like in _seek_to_position)
            if self.player_core.media_player.get_length() > 0:
                # Set a longer timeout after dragging to avoid immediate updates
                self.progress_bar.last_drag_time = time.time()

                # Directly update progress control UI with the new position
                self.progress_bar.progress_control.update_progress(ratio)

                # Calculate the time for the time display
                duration = self.player_core.get_duration()
                new_time_ms = int(duration * ratio)
                self.player_core.current_time = new_time_ms

                # Update time display
                current_time = self._format_time(new_time_ms / 1000)
                total_time = self._format_time(duration / 1000)
                self.progress_bar.progress_control.update_time_display(current_time, total_time)

                # Seek to position in player (actual media update)
                self.player_core.seek(ratio, "progress_bar", "drag")

                # Now that everything is updated, mark dragging as finished
                self.progress_bar.dragging = False

                # Resume playback if it was playing before
                if self.player_core.was_playing:
                    self.player_core.media_player.play()
                    self.progress_bar.controls.update_play_button(True)
                    self.player_core.is_playing = True
            else:
                # If no media is loaded, just mark dragging as finished
                self.progress_bar.dragging = False

    def click_progress(self, event):
        """Handle click on progress bar."""
        # Check if click was near the progress bar and not on a button
        if abs(event.y - self.progress_bar.bar_y) < 10 and not self.progress_bar.dragging:
            self._update_progress_position(event.x)
            # Set position in player
            self._seek_to_position(event.x)

    def _update_progress_position(self, x):
        """Update the position of the progress circle and line."""
        controls_width = self.progress_bar.controls_width

        # Use consistent calculation for max x position
        # 380 = space for time display (160) + volume control (110) + utility buttons (~110)
        max_x = self.progress_bar.canvas.winfo_width() - 380

        # Constrain x to valid range
        x = max(controls_width, min(x, max_x))

        # Update circle position
        circle_radius = self.progress_bar.circle_radius
        bar_y = self.progress_bar.bar_y
        self.progress_bar.canvas.coords(
            self.progress_bar.progress_circle, x - circle_radius, bar_y - circle_radius, x + circle_radius, bar_y + circle_radius
        )

        # Update progress line position
        self.progress_bar.canvas.coords(self.progress_bar.progress_line, controls_width, bar_y, x, bar_y)

    def _seek_to_position(self, x):
        """Seek to a position in the track based on x coordinate."""
        controls_width = self.progress_bar.controls_width

        # Calculate available width for progress bar (same calculation as in progress.py)
        # 380 = space for time display (160) + volume control (110) + utility buttons (~110)
        width = self.progress_bar.canvas.winfo_width() - controls_width - 380

        # Calculate ratio of position (constrained to 0-1)
        ratio = (x - controls_width) / width
        ratio = max(0, min(ratio, 1))  # Constrain to 0-1

        # Update player position
        if self.player_core.media_player.get_length() > 0:
            # Set a longer timeout after dragging to avoid immediate updates
            self.progress_bar.last_drag_time = time.time()

            # Directly update progress control UI with the new position
            # This will ensure the UI reflects exactly where the user clicked/dragged
            self.progress_bar.progress_control.update_progress(ratio)

            # Calculate the time for the time display
            duration = self.player_core.get_duration()
            new_time_ms = int(duration * ratio)
            self.player_core.current_time = new_time_ms

            # Update time display
            current_time = self._format_time(new_time_ms / 1000)
            total_time = self._format_time(duration / 1000)
            self.progress_bar.progress_control.update_time_display(current_time, total_time)

            # Now seek in the player
            self.player_core.seek(ratio, "progress_bar", "click")

    def on_resize(self, event):
        """Handle window resize."""
        # Calculate positions
        controls_width = self.progress_bar.controls_width
        right_margin = PROGRESS_BAR['right_margin']
        volume_width = self.progress_bar.volume_control_width

        # Calculate volume control position
        # Note: on_resize uses a different calculation than progress bar (which uses -380)
        # because it positions elements dynamically based on actual margin/width values
        volume_start_x = event.width - right_margin - volume_width

        # Update line coordinates (end BEFORE volume control)
        self.progress_bar.canvas.coords(
            self.progress_bar.line,
            controls_width,
            self.progress_bar.bar_y,
            volume_start_x - 10,  # Add a small gap before volume control
            self.progress_bar.bar_y,
        )

        # Update time display position
        self.progress_bar.canvas.coords(
            self.progress_bar.time_text,
            event.width - (right_margin / 2),  # Center in right margin
            PROGRESS_BAR['time_label_y'],
        )

        # Reposition volume control
        self.progress_bar.canvas.coords(
            self.progress_bar.volume_window,
            volume_start_x + (volume_width / 2),  # Center the volume control
            self.progress_bar.bar_y,
        )

        # Update progress line if it exists and we're playing
        if hasattr(self.progress_bar, 'progress_line'):
            current_coords = self.progress_bar.canvas.coords(self.progress_bar.progress_line)
            if current_coords and len(current_coords) == 4:
                # Calculate the max x-position where progress line can go
                max_x = volume_start_x - 10

                # Keep progress line within bounds
                if current_coords[2] > max_x:
                    current_coords[2] = max_x

                self.progress_bar.canvas.coords(
                    self.progress_bar.progress_line,
                    current_coords[0],
                    current_coords[1],
                    current_coords[2],
                    current_coords[3],
                )

    def volume_change(self, volume):
        """Handle volume slider changes."""
        with start_action(player_logger, "volume_change"):
            # Get current volume before change
            old_volume = None
            if hasattr(self, 'player_core') and self.player_core:
                try:
                    old_volume = self.player_core.get_volume()
                except Exception:
                    old_volume = 0

            new_volume = int(volume)

            log_player_action(
                "volume_change",
                trigger_source="gui",
                old_volume=old_volume,
                new_volume=new_volume,
                volume_percentage=f"{new_volume}%",
                description=f"Volume changed from {old_volume}% to {new_volume}%",
            )

            if hasattr(self, 'player_core') and self.player_core:
                try:
                    result = self.player_core.set_volume(new_volume)
                    log_player_action("volume_change_success", trigger_source="gui", final_volume=new_volume, result=result)

                    # Persist volume to database
                    self.db.set_volume(new_volume)
                except Exception as e:
                    log_player_action("volume_change_error", trigger_source="gui", attempted_volume=new_volume, error=str(e))
