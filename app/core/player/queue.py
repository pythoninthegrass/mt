"""Queue management for the music player - handles queue operations and playback."""

import os
from core.logging import log_player_action, player_logger
from eliot import log_message, start_action


class PlayerQueueHandler:
    """Manages queue operations and playback initiation."""

    def __init__(self, queue_manager, player_core, queue_view, now_playing_view, progress_bar, favorites_manager, refresh_colors_callback, item_filepath_map):
        """Initialize the queue handler.

        Args:
            queue_manager: QueueManager instance
            player_core: PlayerCore instance
            queue_view: QueueView instance
            now_playing_view: NowPlayingView instance
            progress_bar: ProgressBar instance
            favorites_manager: FavoritesManager instance
            refresh_colors_callback: Callback to refresh colors
            item_filepath_map: Reference to the _item_filepath_map dict
        """
        self.queue_manager = queue_manager
        self.player_core = player_core
        self.queue_view = queue_view
        self.now_playing_view = now_playing_view
        self.progress_bar = progress_bar
        self.favorites_manager = favorites_manager
        self.refresh_colors = refresh_colors_callback
        self._item_filepath_map = item_filepath_map
        self.active_view = 'library'

    def insert_tracks_after_current(self, item_ids: list[str]):
        """Insert selected tracks after currently playing track.

        Args:
            item_ids: List of Treeview item IDs
        """
        filepaths = []
        for item_id in item_ids:
            if item_id in self._item_filepath_map:
                filepaths.append(self._item_filepath_map[item_id])

        if filepaths:
            self.queue_manager.insert_after_current(filepaths)

            # Update Now Playing view if visible
            if self.active_view == 'now_playing':
                self.now_playing_view.refresh_from_queue()

    def add_tracks_to_queue(self, item_ids: list[str]):
        """Append selected tracks to end of queue.

        Args:
            item_ids: List of Treeview item IDs
        """
        filepaths = []
        for item_id in item_ids:
            if item_id in self._item_filepath_map:
                filepaths.append(self._item_filepath_map[item_id])

        if filepaths:
            self.queue_manager.add_to_queue_end(filepaths)

            # Update Now Playing view if visible
            if self.active_view == 'now_playing':
                self.now_playing_view.refresh_from_queue()

    def on_queue_empty(self):
        """Handle queue becoming empty."""
        # Stop playback if playing
        if self.player_core.is_playing:
            self.player_core.stop()

    def play_track_at_index(self, index: int):
        """Play track at specific index in queue (called from Now Playing view).

        Args:
            index: Index in queue
        """
        if 0 <= index < len(self.queue_manager.queue_items):
            self.queue_manager.current_index = index
            filepath = self.queue_manager.queue_items[index]
            self.player_core._play_file(filepath)

            # Update Now Playing view
            if self.active_view == 'now_playing':
                self.now_playing_view.refresh_from_queue()

    def play_selected(self, event=None):
        """Play the selected track and populate queue from current view."""
        with start_action(player_logger, "play_selected_action"):
            selected_items = self.queue_view.queue.selection()
            if not selected_items:
                return "break"

            item_id = selected_items[0]
            item_values = self.queue_view.queue.item(item_id)['values']
            if not item_values:
                return "break"

            track_num, title, artist, album, year = item_values

            # Get all tracks from current view for queue population
            all_filepaths = self._get_all_filepaths_from_view()

            # Find the selected track's index in the filepaths list
            selected_index = 0
            all_item_ids = self.queue_view.queue.get_children()
            for item in all_item_ids:
                if item in self._item_filepath_map:
                    if item == item_id:
                        break
                    selected_index += 1

            # Log the double-click action
            log_player_action("play_selected", title=title, artist=artist, album=album, queue_size=len(all_filepaths))

            if all_filepaths:
                # Populate queue and get track to play
                track_to_play = self.queue_manager.populate_and_play(all_filepaths, selected_index)

                if track_to_play and os.path.exists(track_to_play):
                    was_playing = self.player_core.is_playing
                    self.player_core._play_file(track_to_play)
                    self.progress_bar.controls.update_play_button(True)

                    # Update favorite button icon
                    is_favorite = self.favorites_manager.is_favorite(track_to_play)
                    self.progress_bar.controls.update_favorite_button(is_favorite)

                    # Refresh colors to highlight playing track
                    self.refresh_colors()

                    # Update Now Playing view if visible
                    if self.active_view == 'now_playing':
                        self.now_playing_view.refresh_from_queue()

                    # Log playback state change
                    if not was_playing:
                        log_message(
                            message_type="playback_state", state="started", message="Playback started from library selection"
                        )
                    else:
                        log_message(
                            message_type="playback_state", state="track_changed", message="Track changed from library selection"
                        )

        return "break"

    def _populate_queue_view(self, rows):
        """Populate queue view with rows of data - delegates to library manager."""
        # This method is handled by PlayerLibraryManager
        pass

    def _get_all_filepaths_from_view(self):
        """Get all filepaths from current view in order.

        Returns:
            list[str]: List of filepaths in order
        """
        filepaths = []
        for item in self.queue_view.queue.get_children():
            filepath = self._item_filepath_map.get(item)
            if filepath:
                filepaths.append(filepath)
        return filepaths
