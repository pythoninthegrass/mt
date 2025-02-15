import os
import vlc
from core.db import MusicDatabase
from core.gui import BUTTON_SYMBOLS
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
        if not self.loop_enabled and self._is_last_song():
            self.stop()
            return

        filepath = self._get_next_filepath()
        if filepath:
            self._play_file(filepath)

    def previous_song(self) -> None:
        """Play the previous song in the queue."""
        filepath = self._get_previous_filepath()
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
            return None

        current_selection = self.queue_view.selection()
        if not current_selection:
            # If nothing is selected, start with the first item
            next_index = 0
        else:
            current_index = children.index(current_selection[0])
            # If loop is disabled and on the last song, then stop playback
            if not self.loop_enabled and current_index == len(children) - 1:
                return None
            # Otherwise, move to next song (or first if at end)
            next_index = (current_index + 1) % len(children)

        next_item = children[next_index]
        self.queue_view.selection_set(next_item)
        self.queue_view.see(next_item)

        values = self.queue_view.item(next_item)['values']
        if not values:
            return None

        track_num, title, artist, album, year = values
        return self.db.find_file_by_metadata(title, artist, album, track_num)

    def _get_previous_filepath(self) -> str | None:
        """Get filepath of previous song."""
        children = self.queue_view.get_children()
        if not children:
            return None

        current_selection = self.queue_view.selection()
        if not current_selection:
            # If nothing is selected, start with the last item
            prev_index = len(children) - 1
        else:
            current_index = children.index(current_selection[0])
            # Move to previous song (or last if at beginning)
            prev_index = (current_index - 1) % len(children)

        prev_item = children[prev_index]
        self.queue_view.selection_set(prev_item)
        self.queue_view.see(prev_item)

        values = self.queue_view.item(prev_item)['values']
        if not values:
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
