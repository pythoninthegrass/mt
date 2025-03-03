#!/usr/bin/env python

import flet as ft
import os
import random
import threading
import time
import traceback
from config import (
    ALPHABET_ROW,
    COLUMNS,
    THEME_CONFIG,
)
from core.models import MusicLibrary, Track
from core.player import Player
from core.ui.components import MusicAppComponents
from flet import (
    Column,
    Container,
    CrossAxisAlignment,
    Divider,
    IconButton,
    MainAxisAlignment,
    Row,
    Slider,
    Text,
)
from typing import Any, Optional
from utils.common import format_time


class MusicApp:
    """
    Main music player application UI class.

    This class is responsible for building and managing the UI components
    of the music player application.
    """

    def __init__(self, page: ft.Page):
        """
        Initialize the music player application.

        Args:
            page: The Flet page to render the UI on
        """
        self.page = page
        self.player = Player()
        self.library = MusicLibrary()
        self.current_view = "library"
        self.selected_tracks: list[Track] = []
        self.library_last_click = None
        self.library_last_track = None

        # Apply theme colors to the page
        colors = THEME_CONFIG.get('colors', {})
        self.page.bgcolor = colors.get('bg')
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=colors.get('primary'),
                secondary=colors.get('secondary'),
                background=colors.get('bg'),
                surface=colors.get('bg'),
                on_primary=colors.get('fg'),
                on_secondary=colors.get('fg'),
                on_background=colors.get('fg'),
                on_surface=colors.get('fg'),
            )
        )

        # Create some sample data
        sample_dir = os.path.expanduser("~/Music")
        self.library.scan_directory(sample_dir)

        # If no tracks were found, create some dummy tracks
        if not self.library.tracks:
            for i in range(1, 21):
                track = Track(
                    id=str(i),
                    title=f"Track {i}",
                    artist="Artist" if i % 3 != 0 else "Various Artists",
                    album=f"Album {i // 4 + 1}",
                    path=f"/path/to/track_{i}.mp3",
                    duration=random.randint(120, 360),
                    year=str(random.randint(2000, 2023)),
                    genre=random.choice(["Rock", "Pop", "Electronic", "Indie", "Folk"]),
                    track_number=i % 12 + 1,
                )
                self.library.add_track(track)

                # Add to recently added
                if i <= 15:
                    self.library.playlists["Recently Added"].append(track)

                # Add to recently played
                if i % 2 == 0 and i <= 10:
                    self.library.playlists["Recently Played"].append(track)

                # Add to top 25
                if i % 3 == 0 or i < 5:
                    self.library.playlists["Top 25 Most Played"].append(track)

        # Populate the queue with all library tracks to enable prev/next navigation
        threading.Thread(target=self._initialize_queue, daemon=True).start()

        # Register player events
        self.player.on_track_changed = self._on_track_changed
        self.player.on_playback_state_changed = self._on_playback_state_changed

        # Setup playback update timer
        self._setup_playback_timer()

        # Build the UI
        self.build_layout()
        self.page.update()

    def _initialize_queue(self):
        """
        Initialize the queue with all library tracks.

        This method populates the playback queue with all tracks from the library
        to enable seamless navigation between tracks with next/previous buttons.
        """
        try:
            # Wait a moment to ensure the library has been fully loaded
            time.sleep(1)

            # Add all library tracks to the queue
            if self.library and self.library.tracks:
                print(f"Initializing queue with {len(self.library.tracks)} tracks from UI library")
                self.player.add_library_to_queue(self.library.tracks)
            else:
                print("No tracks in UI library to add to queue")
                # Fall back to database tracks if UI library is empty
                self.player.add_library_to_queue()
        except Exception as e:
            print(f"Error initializing queue: {e}")
            traceback.print_exc()

    def _on_track_changed(self, track):
        """
        Handle track change events from the player.

        Args:
            track: The new current track
        """
        try:
            # Update UI to reflect the current track
            if hasattr(self, 'controls') and hasattr(self.controls, 'update_current_track'):
                self.page.run_sync(lambda: self.controls.update_current_track(track))
        except Exception as e:
            print(f"Error in track changed handler: {e}")
            traceback.print_exc()

    def _on_playback_state_changed(self, is_playing):
        """
        Handle playback state change events from the player.

        Args:
            is_playing: Whether playback is currently active
        """
        try:
            # Update UI to reflect the playback state
            if hasattr(self, 'controls') and hasattr(self.controls, 'update_play_state'):
                self.page.run_sync(lambda: self.controls.update_play_state(is_playing))
        except Exception as e:
            print(f"Error in playback state changed handler: {e}")
            traceback.print_exc()

    def _setup_playback_timer(self):
        """
        Setup a single persistent timer thread for playback progress updates.

        This method creates a background thread that continuously updates
        the playback progress UI elements.
        """
        # Create a flag to indicate when the thread should stop
        self._timer_active = True
        self._is_shutting_down = False  # New flag to indicate app shutdown

        def update_loop():
            """
            Update loop for playback progress and UI elements.
            Runs on a separate thread.
            """
            try:
                # Get current position/duration for progress updates
                position = self.player.player_core.media_player.get_time() / 1000.0  # Convert to seconds
                duration = self.player.player_core.media_player.get_length() / 1000.0  # Convert to seconds

                # Safely format time values - fix for the format error
                def safe_format(seconds):
                    try:
                        if seconds is None or seconds < 0:
                            return "00:00"
                        # Ensure we're working with a float then convert for display
                        seconds = float(seconds)
                        minutes = int(seconds // 60)
                        secs = int(seconds % 60)
                        return f"{minutes}:{secs:02d}"
                    except Exception:
                        return "00:00"

                # Update time labels
                current_time = safe_format(position)
                total_time = safe_format(duration)

                # Update progress bar value
                if duration > 0:  # Avoid division by zero
                    progress = position / duration
                    self._progress_slider.value = progress
                else:
                    self._progress_slider.value = 0

                # Update time labels
                if self._time_display:
                    self._time_display.value = f"{current_time} / {total_time}"

                # Update UI
                if hasattr(self, 'page') and self.page and not self._is_shutting_down:
                    self.page.update()
            except Exception as e:
                print(f"Error updating playback: {e}")

            # Sleep instead of creating a new timer
            # This prevents accumulation of timer threads
            time.sleep(0.5)

        # Start a single persistent thread for the update loop
        self._update_thread = threading.Thread(target=update_loop)
        self._update_thread.daemon = True
        self._update_thread.start()

    def build(self):
        """Build the UI (backward compatibility method)."""
        # This method is now just a wrapper for backward compatibility
        self.build_layout()
        self.page.update()

    def build_layout(self):
        """Build the main application layout."""
        # Sidebar for library and playlists
        sidebar = self.build_sidebar()

        # Main content area
        main_content = self.build_main_content()

        # Player controls at bottom
        player_controls = self.build_player_controls()

        colors = THEME_CONFIG.get('colors', {})

        # Create full layout
        layout = Column(
            [
                Row(
                    [
                        sidebar,
                        ft.VerticalDivider(width=1, color=colors.get('border')),
                        main_content,
                    ],
                    expand=True,
                    spacing=0,
                ),
                Divider(height=1, color=colors.get('border')),
                player_controls,
            ],
            spacing=0,
            expand=True,
        )

        self.page.add(layout)

        # Add a window event handler to detect resize events
        def handle_window_event(e):
            # Process resize events only if we have a resize handler
            if (
                hasattr(e, 'data')
                and e.data == 'resize'
                and hasattr(self, 'page')
                and hasattr(self.page, 'on_resize')
            ):
                try:
                    self.page.on_resize(e)
                except Exception as ex:
                    print(f"Error handling window resize: {ex}")

        # Register the window event handler
        self.page.on_window_event = handle_window_event

    def build_sidebar(self):
        """
        Build the sidebar containing library and playlist navigation.

        Returns:
            Container: The sidebar container
        """
        return MusicAppComponents.build_sidebar(self)

    def build_player_controls(self):
        """
        Build the player controls UI component.

        Returns:
            Container: The player controls container
        """
        return MusicAppComponents.build_player_controls(self)

    def build_main_content(self):
        """
        Build the main content area showing the library or playlist.

        Returns:
            Container: The main content container
        """
        colors = THEME_CONFIG.get('colors', {})

        # Build alphabet row
        alphabet_container = MusicAppComponents.build_alphabet_row(self)

        # Store reference for resize handling
        self.alphabet_container = alphabet_container

        # Add a page resize handler for responsive behavior
        def on_page_resize(e):
            try:
                # Get window width from page
                window_width = self.page.window.width

                # Get breakpoint settings from configuration
                minimum_width_breakpoint = ALPHABET_ROW['min_breakpoint']
                fixed_alphabet_width = ALPHABET_ROW['fixed_width']
                scale_factor = ALPHABET_ROW['scale_factor']

                # Only adjust width below the breakpoint, keep centered above
                if window_width < minimum_width_breakpoint:
                    # When below the breakpoint, adjust width proportionally
                    new_width = window_width * scale_factor
                    self.alphabet_container.width = new_width

                    # Update position if initial_x is set
                    if ALPHABET_ROW['initial_x'] is not None:
                        # Recalculate position based on new width if needed
                        # Otherwise, it stays at initial_x
                        pass
                else:
                    # Above breakpoint - fixed width
                    self.alphabet_container.width = fixed_alphabet_width

                    # Reset position if initial_x is set
                    if ALPHABET_ROW['initial_x'] is not None:
                        self.alphabet_container.left = ALPHABET_ROW['initial_x']

                # Update the UI
                self.page.update()
            except Exception as ex:
                print(f"Error in resize handler: {ex}")

        # Register the resize handler
        self.page.on_resize = on_page_resize

        # Create table headers
        headers = Container(
            content=Row(
                [
                    Container(
                        content=Text(
                            col["name"],
                            color=colors.get('fg'),
                            weight=ft.FontWeight.BOLD,
                        ),
                        width=col["width"],
                        padding=ft.padding.only(left=10),
                    )
                    for col in COLUMNS
                ],
                spacing=0,
            ),
            bgcolor=colors.get('bg'),
            height=40,
            border=ft.border.only(bottom=ft.border.BorderSide(1, colors.get('border'))),
        )

        # Create tracks list
        track_rows = []
        for i, track in enumerate(self.library.tracks):
            bg_color = colors.get('row_alt') if i % 2 == 1 else colors.get('bg')

            # Build row cells based on COLUMNS configuration
            row_cells = []
            for col in COLUMNS:
                cell_content = ""
                if col["id"] == "number":
                    cell_content = str(i + 1)
                elif col["id"] == "title":
                    cell_content = track.title
                elif col["id"] == "artist":
                    cell_content = track.artist
                elif col["id"] == "album":
                    cell_content = track.album
                elif col["id"] == "year":
                    cell_content = track.year
                elif col["id"] == "duration":
                    cell_content = track.duration_str

                row_cells.append(
                    Container(
                        content=Text(cell_content, color=colors.get('fg')),
                        width=col["width"],
                        padding=ft.padding.only(left=10),
                    )
                )

            track_row = Container(
                content=Row(
                    row_cells,
                    spacing=0,
                ),
                height=40,
                bgcolor=bg_color,
                on_click=lambda e, t=track: self.track_clicked(e, t),
                data=track,  # Store track reference in data attribute
            )
            track_rows.append(track_row)

        track_list = Column(
            track_rows,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

        # Create a simple column layout with the alphabet row at the top
        main_content = Column(
            [
                # Alphabet row at the top
                alphabet_container,
                # Divider to separate alphabet row from content
                Divider(height=1, color=colors.get('border')),
                # Main content
                Container(
                    content=Column(
                        [
                            headers,
                            track_list,
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    expand=True,
                    bgcolor=colors.get('bg'),
                    padding=0,
                ),
            ],
            spacing=0,
            expand=True,
        )

        # Trigger initial sizing
        # Use a default fixed width for alphabet container if above breakpoint
        if self.page.window.width >= ALPHABET_ROW['min_breakpoint']:
            alphabet_container.width = ALPHABET_ROW['fixed_width']
        else:
            alphabet_container.width = (
                self.page.window.width * ALPHABET_ROW['scale_factor']
            )

        # Apply initial x position if specified
        if ALPHABET_ROW['initial_x'] is not None:
            alphabet_container.left = ALPHABET_ROW['initial_x']

        # Debug output
        print(
            f"Initial alphabet row setup: width={alphabet_container.width}, "
            + f"x={ALPHABET_ROW['initial_x'] if ALPHABET_ROW['initial_x'] is not None else 'centered'}"
        )

        return Container(
            content=main_content,
            expand=True,
            bgcolor=colors.get('bg'),
            padding=0,
        )

    def track_clicked(self, e, track: Track):
        """
        Handle track click with double-click detection.

        Args:
            e: Click event
            track: The track that was clicked
        """
        now = time.time()

        # Check if this is a double-click on the same track
        is_double_click = (
            self.library_last_click
            and now - self.library_last_click < 0.5
            and self.library_last_track
            and self.library_last_track.id == track.id
        )

        # Update last click timestamp and track
        self.library_last_click = now
        self.library_last_track = track

        # On double-click, play the track
        if is_double_click:
            self.play_track(track)

        # Highlight the selected track
        colors = THEME_CONFIG.get('colors', {})

        # Reset all track rows to their normal color first
        for row in e.control.parent.controls:
            if hasattr(row, 'data') and isinstance(row.data, Track):
                # Get row index for alternating colors
                i = (
                    self.library.tracks.index(row.data)
                    if row.data in self.library.tracks
                    else 0
                )
                row.bgcolor = colors.get('row_alt') if i % 2 == 1 else colors.get('bg')

        # Highlight the clicked row
        e.control.bgcolor = colors.get('selectbg')
        self.page.update()

    def play_track(self, track: Track):
        """
        Play a track with proper isolation to prevent event loop closure.

        Args:
            track: The track to play
        """
        print(f"Playing track: {track.title} - {track.artist}")

        # Check if we're shutting down
        if hasattr(self, '_is_shutting_down') and self._is_shutting_down:
            print("Application is shutting down, ignoring play request")
            return

        try:
            # 1. Update UI elements immediately in the main thread
            if self._track_info:
                self._track_info.value = f"{track.artist} - {track.title}"
            if self._play_button:
                self._play_button.icon = ft.Icons.PAUSE
            if self._time_display:
                self._time_display.value = f"0:00 / {track.duration_str}"
            if self._progress_slider:
                self._progress_slider.value = 0

            # 2. Store as current track
            self.player.current_track = track

            # 3. Update UI first to ensure visual feedback is immediate
            if hasattr(self, 'page') and self.page:
                self.page.update()
        except Exception as ui_err:
            print(f"Error updating UI: {ui_err}")
            traceback.print_exc()

        # 4. Use a separate thread to handle actual playback with proper isolation
        def play_media_safely():
            # Check again if we're shutting down before starting playback
            if hasattr(self, '_is_shutting_down') and self._is_shutting_down:
                return

            try:
                # Add a small delay to ensure UI updates have completed
                time.sleep(0.2)

                # Use a try-except block specifically for player operations
                try:
                    self.player.play(track)
                except Exception as play_err:
                    print(f"Error in player.play: {play_err}")
                    traceback.print_exc()

                    # Try to recover player state if there was an error
                    try:
                        if self.player.player_core and not self._is_shutting_down:
                            self.player.player_core.is_playing = False
                            if self._play_button:
                                self._play_button.icon = ft.Icons.PLAY_ARROW
                                # Check if we can safely update the UI
                                if hasattr(self, 'page') and self.page and not self._is_shutting_down:
                                    self.page.update()
                    except:
                        pass
            except Exception as e:
                print(f"Critical error in play_media_safely: {e}")
                traceback.print_exc()

        # Start the playback in a well-isolated thread
        play_thread = threading.Thread(target=play_media_safely)
        play_thread.daemon = True
        play_thread.start()

    def toggle_play(self):
        """Toggle play/pause state using safe scheduling to avoid window reloads."""
        # Check if we're shutting down
        if hasattr(self, '_is_shutting_down') and self._is_shutting_down:
            return

        # Update UI immediately
        if self.player.player_core.is_playing:
            self._play_button.icon = ft.Icons.PLAY_ARROW
        else:
            self._play_button.icon = ft.Icons.PAUSE

        # Update UI
        if hasattr(self, 'page') and self.page and not self._is_shutting_down:
            self.page.update()

        # Schedule the toggle operation after UI update
        def do_toggle():
            # Check again if we're shutting down
            if hasattr(self, '_is_shutting_down') and self._is_shutting_down:
                return

            try:
                self.player.player_core.play_pause()
            except Exception as e:
                print(f"Error toggling playback: {e}")
                traceback.print_exc()

        # Use threading instead of Flet's scheduling
        timer = threading.Timer(0.1, do_toggle)
        timer.daemon = True
        timer.start()

    def previous_track(self):
        """Go to previous track using safe scheduling to avoid window reloads."""

        def do_previous():
            try:
                self.player.previous()

                # Update UI after navigation
                if self.player.current_track:
                    self._track_info.value = f"{self.player.current_track.artist} - {self.player.current_track.title}"
                    # Start playback if we were paused
                    if not self.player.player_core.is_playing:
                        self.player.player_core.play_pause()
                        self._play_button.icon = ft.Icons.PAUSE
                    else:
                        self._play_button.icon = ft.Icons.PAUSE

                    # Update immediately to avoid lag
                    self.page.update()
            except Exception as e:
                print(f"Error going to previous track: {e}")
                traceback.print_exc()

        # Use threading instead of Flet's scheduling
        timer = threading.Timer(0.1, do_previous)
        timer.daemon = True
        timer.start()

    def next_track(self):
        """Go to next track using safe scheduling to avoid window reloads."""

        def do_next():
            try:
                self.player.next()

                # Update UI after navigation
                if self.player.current_track:
                    self._track_info.value = f"{self.player.current_track.artist} - {self.player.current_track.title}"
                    # Start playback if we were paused
                    if not self.player.player_core.is_playing:
                        self.player.player_core.play_pause()
                        self._play_button.icon = ft.Icons.PAUSE
                    else:
                        self._play_button.icon = ft.Icons.PAUSE

                    # Update immediately to avoid lag
                    self.page.update()
            except Exception as e:
                print(f"Error going to next track: {e}")
                traceback.print_exc()

        # Use threading instead of Flet's scheduling
        timer = threading.Timer(0.1, do_next)
        timer.daemon = True
        timer.start()

    def set_position_threaded(self, position):
        """
        Set position using safe scheduling to avoid window reloads.

        Args:
            position: Position value from 0-100
        """

        def do_set_position():
            try:
                self.player.set_position(position)
            except Exception as e:
                print(f"Error setting position: {e}")
                traceback.print_exc()

        # Use threading instead of Flet's scheduling
        timer = threading.Timer(0.1, do_set_position)
        timer.daemon = True
        timer.start()

    def set_volume_threaded(self, volume):
        """
        Set volume using safe scheduling to avoid window reloads.

        Args:
            volume: Volume value from 0-1
        """

        def do_set_volume():
            try:
                self.player.set_volume(volume)
            except Exception as e:
                print(f"Error setting volume: {e}")
                traceback.print_exc()

        # Use threading instead of Flet's scheduling
        timer = threading.Timer(0.1, do_set_volume)
        timer.daemon = True
        timer.start()

    def switch_view(self, view_name: str, data: Any = None):
        """
        Switch to a different view in the application.

        Args:
            view_name: Name of the view to switch to
            data: Optional data needed for the view
        """
        self.current_view = view_name
        # Update UI to show the selected view
        # In a real implementation, we would rebuild the main content
        # For now, we'll just print the change
        print(f"Switching to view: {view_name}, data: {data}")

    def filter_by_letter(self, letter: str):
        """
        Filter the tracks by first letter.

        Args:
            letter: The letter to filter by
        """
        # In a real implementation, we would filter the tracks by letter
        print(f"Filtering by letter: {letter}")

    def cleanup(self):
        """Clean up resources when app is closing."""
        print("Cleaning up MusicApp resources...")
        try:
            # Set shutdown flag to prevent new operations
            self._is_shutting_down = True

            # Stop the update timer thread
            if hasattr(self, '_timer_active'):
                self._timer_active = False

            # Wait a moment for threads to notice shutdown flag
            time.sleep(0.2)

            # Stop playback
            if self.player and self.player.player_core:
                # Stop playback first
                self.player.player_core.stop()

                # Release VLC resources
                try:
                    if self.player.player_core.media_player:
                        self.player.player_core.media_player.release()
                    if self.player.player_core.player:
                        self.player.player_core.player.release()
                except Exception as vlc_err:
                    print(f"Error releasing VLC resources: {vlc_err}")

            # Close database connections
            if self.player and hasattr(self.player, 'db'):
                try:
                    self.player.db.close()
                except Exception as db_err:
                    print(f"Error closing database: {db_err}")

            print("MusicApp resources cleaned up successfully")
        except Exception as e:
            print(f"Error during MusicApp cleanup: {e}")
            traceback.print_exc()
