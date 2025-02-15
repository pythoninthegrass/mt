import os
import tkinter as tk
import vlc
from config import BUTTON_SYMBOLS
from core.db import MusicDatabase
from core.queue import QueueManager


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
        self.progress_bar = None  # Will be set by MusicPlayer
        self.window = None  # Will be set by MusicPlayer

        # Set up end of track event handler
        self.media_player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self._on_track_end)

    def play_pause(self) -> None:
        """Toggle play/pause state."""
        if not self.is_playing:
            if self.media_player.get_media() is not None:
                self.media_player.play()
                self.is_playing = True
                self._update_track_info()
            else:
                filepath = self._get_current_filepath()
                if filepath:
                    self._play_file(filepath)
        else:
            self.current_time = self.media_player.get_time()
            self.media_player.pause()
            self.is_playing = False

    def next_song(self) -> None:
        """Play the next song in the queue."""
        print("next_song called")  # Debug log
        if not self.loop_enabled and self._is_last_song():
            print("Last song and loop disabled, stopping")  # Debug log
            self.stop()
            return

        filepath = self._get_next_filepath()
        print(f"Next filepath: {filepath}")  # Debug log
        if filepath:
            self._play_file(filepath)

    def previous_song(self) -> None:
        """Play the previous song in the queue."""
        print("previous_song called")  # Debug log
        filepath = self._get_previous_filepath()
        print(f"Previous filepath: {filepath}")  # Debug log
        if filepath:
            self._play_file(filepath)

    def seek(self, position: float) -> None:
        """Seek to a position in the current track (0.0 to 1.0)."""
        if self.media_player.get_length() > 0:
            new_time = int(self.media_player.get_length() * position)
            self.media_player.set_time(new_time)

    def stop(self) -> None:
        """Stop playback."""
        self.media_player.stop()
        self.is_playing = False
        self.current_time = 0
        if self.progress_bar:
            self.progress_bar.clear_track_info()
            if hasattr(self.progress_bar, 'controls') and hasattr(self.progress_bar.controls, 'play_button'):
                self.progress_bar.controls.play_button.configure(text=BUTTON_SYMBOLS['play'])

    def toggle_loop(self) -> None:
        """Toggle loop mode."""
        self.loop_enabled = not self.loop_enabled
        self.db.set_loop_enabled(self.loop_enabled)
        if self.progress_bar and hasattr(self.progress_bar, 'controls'):
            self.progress_bar.controls.update_loop_button_color(self.loop_enabled)

    def get_current_time(self) -> int:
        """Get current playback time in milliseconds."""
        return self.media_player.get_time()

    def get_duration(self) -> int:
        """Get total duration of current track in milliseconds."""
        return self.media_player.get_length()

    def _play_file(self, filepath: str) -> None:
        """Play a specific file."""
        if not os.path.exists(filepath):
            print(f"File not found on disk: {filepath}")
            return

        media = self.player.media_new(filepath)
        self.media_player.set_media(media)
        self.media_player.play()
        self.current_time = 0
        self.is_playing = True
        self._update_track_info()

        # Update play button to pause symbol since we're now playing
        if self.progress_bar and hasattr(self.progress_bar, 'controls') and hasattr(self.progress_bar.controls, 'play_button'):
            self.progress_bar.controls.play_button.configure(text=BUTTON_SYMBOLS['pause'])

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
        if not current_selection:
            # If nothing is selected, start with the first item
            item = children[0]
        else:
            item = current_selection[0]

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
            if not self.loop_enabled and current_index == len(children) - 1:
                print("Last song and loop disabled")  # Debug log
                return None
            # Otherwise, move to next song (or first if at end)
            next_index = (current_index + 1) % len(children)
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
            # Move to previous song (or last if at beginning)
            prev_index = (current_index - 1) % len(children)
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
                self.stop()
            else:
                self.next_song()

        # Update UI elements
        if self.progress_bar and hasattr(self.progress_bar, 'controls'):
            self.progress_bar.controls.play_button.configure(
                text=BUTTON_SYMBOLS['pause'] if self.is_playing else BUTTON_SYMBOLS['play']
            )
