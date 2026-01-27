"""Event handlers for the music player - handles user interactions and callbacks."""

import os
import urllib.parse
from core.logging import log_player_action, player_logger
from eliot import log_message, start_action


class PlayerEventHandlers:
    """Manages event handling, callbacks, and user interactions."""

    def __init__(
        self,
        window,
        db,
        player_core,
        library_view,
        queue_view,
        now_playing_view,
        library_manager,
        queue_manager,
        favorites_manager,
        progress_bar,
        status_bar,
        load_library_callback,
        load_liked_songs_callback,
        load_recently_played_callback,
        refresh_colors_callback,
        _item_filepath_map,
        library_handler=None,
    ):
        """Initialize the event handlers.

        Args:
            window: The main Tkinter window
            db: Database instance
            player_core: PlayerCore instance
            library_view: LibraryView instance
            queue_view: QueueView instance
            now_playing_view: NowPlayingView instance
            library_manager: LibraryManager instance
            queue_manager: QueueManager instance
            favorites_manager: FavoritesManager instance
            progress_bar: ProgressBar instance
            status_bar: StatusBar instance
            load_library_callback: Callback to reload library
            load_liked_songs_callback: Callback to reload liked songs
            load_recently_played_callback: Callback to reload recently played
            refresh_colors_callback: Callback to refresh colors
            _item_filepath_map: Reference to the _item_filepath_map dict
        """
        self.window = window
        self.db = db
        self.player_core = player_core
        self.library_view = library_view
        self.queue_view = queue_view
        self.now_playing_view = now_playing_view
        self.library_manager = library_manager
        self.queue_manager = queue_manager
        self.favorites_manager = favorites_manager
        self.progress_bar = progress_bar
        self.status_bar = status_bar
        self.load_library = load_library_callback
        self.load_liked_songs = load_liked_songs_callback
        self.load_recently_played = load_recently_played_callback
        self.refresh_colors = refresh_colors_callback
        self._item_filepath_map = _item_filepath_map
        self.library_handler = library_handler
        self.active_view = 'library'

    def handle_drop(self, event):
        """Handle drag and drop of files."""
        with start_action(player_logger, "file_drop"):
            # On macOS, paths are separated by spaces and wrapped in curly braces
            # Example: "{/path/to/first file.mp3} {/path/to/second file.mp3}"
            raw_data = event.data.strip()
            paths = []

            # Extract paths between curly braces
            current = 0
            while current < len(raw_data):
                if raw_data[current] == '{':
                    end = raw_data.find('}', current)
                    if end != -1:
                        # Extract path without braces and handle quotes
                        path = raw_data[current + 1 : end].strip().strip('"')
                        if path:  # Only add non-empty paths
                            paths.append(path)
                        current = end + 1
                    else:
                        break
                else:
                    current += 1

            if not paths:  # Fallback for non-macOS or different format
                paths = [p.strip('{}').strip('"') for p in event.data.split() if p.strip()]

            # Analyze dropped files
            file_types = {}
            valid_paths = []
            for path in paths:
                if os.path.exists(path):
                    valid_paths.append(path)
                    ext = os.path.splitext(path)[1].lower()
                    file_types[ext] = file_types.get(ext, 0) + 1

            # Get current view to determine destination
            selected_item = self.library_view.library_tree.selection()
            destination = "unknown"

            if selected_item:
                tags = self.library_view.library_tree.item(selected_item[0])['tags']
                if tags:
                    destination = tags[0]

                    log_player_action(
                        "file_drop",
                        trigger_source="drag_drop",
                        destination=destination,
                        total_files=len(paths),
                        valid_files=len(valid_paths),
                        file_types=file_types,
                        file_paths=valid_paths[:10],  # Log first 10 paths to avoid huge logs
                        raw_data_length=len(raw_data),
                        description=f"Dropped {len(paths)} files to {destination} section",
                    )

                    try:
                        if tags[0] == 'music':
                            self.library_manager.add_files_to_library(valid_paths)
                            # Update statistics immediately
                            self.status_bar.update_statistics()
                            self.load_library()
                        elif tags[0] == 'now_playing':
                            self.library_manager.add_files_to_library(valid_paths)
                            # Update statistics immediately
                            self.status_bar.update_statistics()
                            self.queue_manager.process_dropped_files(valid_paths)
                            # Refresh Now Playing view if currently visible
                            if self.active_view == 'now_playing':
                                self.now_playing_view.refresh_from_queue()

                        log_player_action(
                            "file_drop_success",
                            trigger_source="drag_drop",
                            destination=destination,
                            processed_files=len(valid_paths),
                            description=f"Successfully processed {len(valid_paths)} files",
                        )
                    except Exception as e:
                        log_player_action(
                            "file_drop_error",
                            trigger_source="drag_drop",
                            destination=destination,
                            error=str(e),
                            attempted_files=len(valid_paths),
                        )
            else:
                log_player_action(
                    "file_drop_no_destination", trigger_source="drag_drop", total_files=len(paths), reason="no_section_selected"
                )

    def handle_delete(self, event):
        """Handle delete key press - deletes from library, queue, or playlist based on current view."""
        with start_action(player_logger, "track_delete"):
            selected_items = self.queue_view.queue.selection()
            if not selected_items:
                log_player_action("track_delete_no_selection", trigger_source="keyboard", reason="no_items_selected")
                return

            deleted_tracks = []
            current_view = self.queue_view.current_view

            # Determine the view type
            is_queue_view = current_view == 'now_playing'
            is_playlist_view = current_view.startswith('playlist:')

            # Extract playlist_id if in playlist view
            playlist_id = None
            if is_playlist_view:
                try:
                    playlist_id = int(current_view.split(':')[1])
                except (IndexError, ValueError):
                    log_player_action(
                        "track_delete_invalid_playlist",
                        trigger_source="keyboard",
                        view=current_view,
                        reason="invalid_playlist_id",
                    )
                    return

            # For playlist views, collect track IDs to remove
            track_ids_to_remove = []

            for item in selected_items:
                values = self.queue_view.queue.item(item)['values']
                if values:
                    track_num, title, artist, album, year = values

                    # Get queue position before deletion (for queue view only)
                    queue_position = -1
                    if is_queue_view:
                        children = self.queue_view.queue.get_children()
                        queue_position = children.index(item) if item in children else -1

                    # Get file path for the track
                    filepath = None
                    if self.library_manager:
                        filepath = self.library_manager.find_file_by_metadata(title, artist, album, track_num)

                    track_info = {
                        "track_num": track_num,
                        "title": title,
                        "artist": artist,
                        "album": album,
                        "year": year,
                        "queue_position": queue_position,
                        "filepath": filepath,
                        "view": current_view,
                    }
                    deleted_tracks.append(track_info)

                    if is_playlist_view:
                        # Remove from playlist only - collect track IDs
                        if self.library_handler and hasattr(self.library_handler, '_item_track_id_map'):
                            track_id = self.library_handler._item_track_id_map.get(item)
                            if track_id:
                                track_ids_to_remove.append(track_id)
                                log_player_action(
                                    "track_delete_from_playlist",
                                    trigger_source="keyboard",
                                    playlist_id=playlist_id,
                                    track_id=track_id,
                                    track_info=track_info,
                                    description=f"Removed track from playlist: {title} by {artist}",
                                )
                    elif is_queue_view:
                        # Delete from queue only
                        log_player_action(
                            "track_delete_from_queue",
                            trigger_source="keyboard",
                            track_info=track_info,
                            description=f"Deleted track from queue: {title} by {artist}",
                        )
                        self.queue_manager.remove_from_queue(title, artist, album, track_num)
                    else:
                        # Delete from library (and favorites if present)
                        log_player_action(
                            "track_delete_from_library",
                            trigger_source="keyboard",
                            track_info=track_info,
                            description=f"Deleted track from library: {title} by {artist}",
                        )
                        if filepath:
                            success = self.library_manager.delete_from_library(filepath)
                            if success:
                                # Also remove from queue if it exists
                                self.queue_manager.remove_from_queue(title, artist, album, track_num)

                    # Remove from UI
                    self.queue_view.queue.delete(item)

            # Remove tracks from playlist if in playlist view
            if is_playlist_view and track_ids_to_remove:
                self.db.remove_tracks_from_playlist(playlist_id, track_ids_to_remove)

            # Log summary of deletion operation
            log_player_action(
                "track_delete_summary",
                trigger_source="keyboard",
                deleted_count=len(deleted_tracks),
                tracks_deleted=deleted_tracks,
                view=current_view,
                description=f"Deleted {len(deleted_tracks)} track(s) from {current_view}",
            )

            # Update statistics if deleting from library
            if not is_queue_view and not is_playlist_view:
                self.status_bar.update_statistics()

            self.refresh_colors()
            return "break"

    def on_song_select(self, event):
        """Handle song selection in queue view."""
        # This method can be used to update UI or track the currently selected song
        pass

    def toggle_favorite(self):
        """Toggle favorite status for currently playing track."""
        with start_action(player_logger, "toggle_favorite"):
            # Only allow favoriting if a track is actually playing (not just selected)
            if not self.player_core.media_player.get_media():
                # No track is loaded
                log_player_action(
                    "toggle_favorite_skipped",
                    trigger_source="gui",
                    reason="no_media_loaded",
                    description="No track loaded to favorite",
                )
                return

            # Check if player is actually playing or paused (but has media loaded)
            if not self.player_core.is_playing and self.player_core.media_player.get_state() not in [3, 4]:
                # Track is not playing or paused (states 3=Playing, 4=Paused)
                log_player_action(
                    "toggle_favorite_skipped",
                    trigger_source="gui",
                    reason="not_playing_or_paused",
                    player_state=self.player_core.media_player.get_state(),
                    description="Track not in playable state",
                )
                return

            # Get the currently playing file path directly from VLC
            media = self.player_core.media_player.get_media()
            if not media:
                return

            filepath = media.get_mrl()
            # Remove 'file://' prefix if present
            if filepath.startswith('file://'):
                filepath = filepath[7:]

            # URL decode the filepath
            filepath = urllib.parse.unquote(filepath)

            if not filepath or not os.path.exists(filepath):
                log_player_action(
                    "toggle_favorite_failed",
                    trigger_source="gui",
                    reason="invalid_filepath",
                    filepath=filepath,
                    description="Filepath does not exist",
                )
                return

            # Get current favorite state and track info before toggling
            old_state = self.favorites_manager.is_favorite(filepath)
            track_info = self.player_core._get_current_track_info()

            # Toggle favorite status
            is_favorite = self.favorites_manager.toggle_favorite(filepath)

            log_player_action(
                "toggle_favorite",
                trigger_source="gui",
                filepath=filepath,
                old_state=old_state,
                new_state=is_favorite,
                track_info=track_info,
                description=f"Track {'added to' if is_favorite else 'removed from'} favorites",
            )

            # Update button icon
            if self.progress_bar and hasattr(self.progress_bar, 'controls'):
                self.progress_bar.controls.update_favorite_button(is_favorite)

    def on_favorites_changed(self):
        """Callback when favorites list changes - refresh view if showing liked songs."""
        selected_item = self.library_view.library_tree.selection()
        if not selected_item:
            return

        tags = self.library_view.library_tree.item(selected_item[0])['tags']
        if tags and tags[0] == 'liked_songs':
            # Refresh the liked songs view
            self.load_liked_songs()

    def on_track_change(self):
        """Callback when current track changes - always refresh Now Playing view."""
        # Always refresh the Now Playing view when track changes to prevent stale data
        # This is especially important when queue becomes empty
        if self.now_playing_view:
            self.now_playing_view.refresh_from_queue()

            # Update lyrics for the new track
            if self.queue_manager.queue_items and self.queue_manager.current_index < len(self.queue_manager.queue_items):
                current_filepath = self.queue_manager.queue_items[self.queue_manager.current_index]
                # Get track metadata from database
                track_info = self.library_manager.get_track_by_filepath(current_filepath)
                if track_info:
                    artist = track_info.get('artist', '')
                    title = track_info.get('title', '')
                    album = track_info.get('album', '')
                    if artist and title:
                        self.now_playing_view.update_lyrics(artist, title, album)

    def perform_search(self, search_text):
        """Handle search functionality."""
        log_message(message_type="search_action", search_text=search_text, message="Performing search")

        # Get current section from library view
        selected_item = self.library_view.library_tree.selection()
        if not selected_item:
            return

        tags = self.library_view.library_tree.item(selected_item[0])['tags']
        if not tags:
            return

        tag = tags[0]

        # Search only works in library views, not Now Playing
        if tag == 'now_playing':
            return

        # Clear current view
        for item in self.queue_view.queue.get_children():
            self.queue_view.queue.delete(item)

        if tag == 'music':
            # Search in library
            rows = self.library_manager.search_library(search_text) if search_text else self.library_manager.get_library_items()
        else:
            return

        if rows:
            # Populate queue view with search results
            self.library_handler._populate_queue_view(rows)
            self.refresh_colors()

    def clear_search(self):
        """Clear search and reload current view."""
        log_message(message_type="search_action", message="Clearing search")

        # Reset search bar
        if hasattr(self, 'search_bar'):
            self.search_bar.search_var.set("")

        # Reload current section without search filter
        selected_item = self.library_view.library_tree.selection()
        if selected_item:
            tags = self.library_view.library_tree.item(selected_item[0])['tags']
            if tags:
                tag = tags[0]
                if tag == 'music':
                    self.load_library()
                elif tag == 'now_playing' and self.active_view == 'now_playing':
                    # Refresh Now Playing view
                    self.now_playing_view.refresh_from_queue()

    def toggle_stop_after_current(self):
        """Toggle stop-after-current flag."""
        if self.player_core:
            self.player_core.toggle_stop_after_current()
