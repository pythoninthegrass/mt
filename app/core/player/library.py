"""Library management for the music player - handles loading and displaying library content."""

import os
import sys
from config import AUDIO_EXTENSIONS
from core.logging import library_logger, log_player_action, player_logger
from eliot import start_action
from pathlib import Path
from tkinter import filedialog
from utils.files import find_audio_files


class PlayerLibraryManager:
    """Manages library loading, display, and file operations."""

    def __init__(
        self,
        window,
        db,
        library_manager,
        favorites_manager,
        library_view,
        queue_view,
        status_bar,
        now_playing_view,
        refresh_colors_callback,
    ):
        """Initialize the library manager.

        Args:
            window: The main Tkinter window
            db: Database instance
            library_manager: LibraryManager instance
            favorites_manager: FavoritesManager instance
            library_view: LibraryView instance
            queue_view: QueueView instance
            status_bar: StatusBar instance
            now_playing_view: NowPlayingView instance
            refresh_colors_callback: Callback to refresh colors
        """
        self.window = window
        self.db = db
        self.library_manager = library_manager
        self.favorites_manager = favorites_manager
        self.library_view = library_view
        self.queue_view = queue_view
        self.status_bar = status_bar
        self.now_playing_view = now_playing_view
        self.refresh_colors = refresh_colors_callback
        self._item_filepath_map = {}
        self._item_track_id_map = {}  # Maps tree item IDs to library track IDs for playlist operations
        self.active_view = 'library'

    def load_library(self):
        """Load and display library items."""
        # Reset to standard 5-column layout
        self._reset_to_standard_columns()

        # Clear current view
        for item in self.queue_view.queue.get_children():
            self.queue_view.queue.delete(item)

        # Reset column header to "#"
        self.queue_view.set_track_column_header('#')

        # Set current view and restore column widths
        self.queue_view.set_current_view('music')

        rows = self.library_manager.get_library_items()
        if not rows:
            return

        self._populate_queue_view(rows)
        self.refresh_colors()

    def load_liked_songs(self):
        """Load and display liked songs."""
        # Reset to standard 5-column layout
        self._reset_to_standard_columns()

        # Initialize filepath mapping if needed
        if not hasattr(self, '_item_filepath_map'):
            self._item_filepath_map = {}

        # Clear current view and mapping
        for item in self.queue_view.queue.get_children():
            self.queue_view.queue.delete(item)
        self._item_filepath_map.clear()

        # Reset column header to "#"
        self.queue_view.set_track_column_header('#')

        # Set current view and restore column widths
        self.queue_view.set_current_view('liked_songs')

        rows = self.favorites_manager.get_liked_songs()
        for i, (filepath, artist, title, album, track_num, date) in enumerate(rows):
            formatted_track = self._format_track_number(track_num)
            year = self._extract_year(date)
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            item_id = self.queue_view.queue.insert(
                '', 'end', values=(formatted_track, title or '', artist or '', album or '', year or ''), tags=(row_tag,)
            )
            # Store filepath mapping
            self._item_filepath_map[item_id] = filepath

    def load_top_25_most_played(self):
        """Load and display top 25 most played tracks."""
        # Reset to standard 5-column layout
        self._reset_to_standard_columns()

        # Initialize filepath mapping if needed
        if not hasattr(self, '_item_filepath_map'):
            self._item_filepath_map = {}

        # Clear current view and mapping
        for item in self.queue_view.queue.get_children():
            self.queue_view.queue.delete(item)
        self._item_filepath_map.clear()

        # Change column header to "Play Count"
        self.queue_view.set_track_column_header('Play Count')

        # Set current view and restore column widths
        self.queue_view.set_current_view('top_played')

        rows = self.library_manager.get_top_25_most_played()
        if not rows:
            return

        # Format with play count instead of track number
        for i, (filepath, artist, title, album, play_count, date) in enumerate(rows):
            year = self._extract_year(date)
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            item_id = self.queue_view.queue.insert(
                '', 'end', values=(str(play_count), title or '', artist or '', album or '', year or ''), tags=(row_tag,)
            )
            # Store filepath mapping
            self._item_filepath_map[item_id] = filepath
        self.refresh_colors()

    def load_recently_added(self):
        """Load and display recently added tracks (last 14 days)."""
        with start_action(player_logger, "load_recently_added"):
            # Initialize filepath mapping if needed
            if not hasattr(self, '_item_filepath_map'):
                self._item_filepath_map = {}

            # Clear current view and mapping
            for item in self.queue_view.queue.get_children():
                self.queue_view.queue.delete(item)
            self._item_filepath_map.clear()

            # Reconfigure treeview to include 'added' column
            self.queue_view.queue.configure(columns=('track', 'title', 'artist', 'album', 'year', 'added'))

            # Configure all columns including the new 'added' column
            self.queue_view.queue.heading('track', text='#')
            self.queue_view.queue.heading('title', text='Title')
            self.queue_view.queue.heading('artist', text='Artist')
            self.queue_view.queue.heading('album', text='Album')
            self.queue_view.queue.heading('year', text='Year')
            self.queue_view.queue.heading('added', text='Added')

            # Set column widths
            self.queue_view.queue.column('track', width=50, anchor='center')
            self.queue_view.queue.column('title', width=200, minwidth=100)
            self.queue_view.queue.column('artist', width=150, minwidth=80)
            self.queue_view.queue.column('album', width=150, minwidth=80)
            self.queue_view.queue.column('year', width=80, minwidth=60, anchor='center')
            self.queue_view.queue.column('added', width=150, minwidth=120, anchor='center')

            # Set current view and restore column widths
            self.queue_view.set_current_view('recently_added')

            rows = self.library_manager.get_recently_added()
            if not rows:
                log_player_action(
                    "load_recently_added_empty", trigger_source="gui", description="No recently added tracks found (last 14 days)"
                )
                return

            # Format with standard track number display and added timestamp
            for i, (filepath, artist, title, album, track_num, date, added_date) in enumerate(rows):
                formatted_track = self._format_track_number(track_num)
                year = self._extract_year(date)

                # Format added_date timestamp
                added_str = self._format_added_date(added_date) if added_date else ''

                row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                item_id = self.queue_view.queue.insert(
                    '',
                    'end',
                    values=(formatted_track, title or '', artist or '', album or '', year or '', added_str),
                    tags=(row_tag,),
                )
                # Store filepath mapping
                self._item_filepath_map[item_id] = filepath

            self.refresh_colors()

            log_player_action(
                "load_recently_added_success",
                trigger_source="gui",
                loaded_items=len(rows),
                description=f"Loaded {len(rows)} recently added tracks (last 14 days)",
            )

    def load_recently_played(self):
        """Load and display recently played tracks (last 14 days)."""
        with start_action(player_logger, "load_recently_played"):
            # Initialize filepath mapping if needed
            if not hasattr(self, '_item_filepath_map'):
                self._item_filepath_map = {}

            # Clear current view and mapping
            for item in self.queue_view.queue.get_children():
                self.queue_view.queue.delete(item)
            self._item_filepath_map.clear()

            # Reconfigure treeview to include 'played' column
            self.queue_view.queue.configure(columns=('track', 'title', 'artist', 'album', 'year', 'played'))

            # Configure all columns including the new 'played' column
            self.queue_view.queue.heading('track', text='#')
            self.queue_view.queue.heading('title', text='Title')
            self.queue_view.queue.heading('artist', text='Artist')
            self.queue_view.queue.heading('album', text='Album')
            self.queue_view.queue.heading('year', text='Year')
            self.queue_view.queue.heading('played', text='Last Played')

            # Set column widths
            self.queue_view.queue.column('track', width=50, anchor='center')
            self.queue_view.queue.column('title', width=200, minwidth=100)
            self.queue_view.queue.column('artist', width=150, minwidth=80)
            self.queue_view.queue.column('album', width=150, minwidth=80)
            self.queue_view.queue.column('year', width=80, minwidth=60, anchor='center')
            self.queue_view.queue.column('played', width=150, minwidth=120, anchor='center')

            # Set current view and restore column widths
            self.queue_view.set_current_view('recently_played')

            rows = self.library_manager.get_recently_played()
            if not rows:
                log_player_action(
                    "load_recently_played_empty",
                    trigger_source="gui",
                    description="No recently played tracks found (last 14 days)",
                )
                return

            # Format with standard track number display and last_played timestamp
            for i, (filepath, artist, title, album, track_num, date, last_played) in enumerate(rows):
                formatted_track = self._format_track_number(track_num)
                year = self._extract_year(date)

                # Format last_played timestamp
                played_str = self._format_added_date(last_played) if last_played else ''

                row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                item_id = self.queue_view.queue.insert(
                    '',
                    'end',
                    values=(formatted_track, title or '', artist or '', album or '', year or '', played_str),
                    tags=(row_tag,),
                )
                # Store filepath mapping
                self._item_filepath_map[item_id] = filepath

            self.refresh_colors()

            log_player_action(
                "load_recently_played_success",
                trigger_source="gui",
                loaded_items=len(rows),
                description=f"Loaded {len(rows)} recently played tracks (last 14 days)",
            )

    def load_custom_playlist(self, playlist_id: int):
        """Load and display a custom user-created playlist.

        Args:
            playlist_id: Database ID of the playlist
        """
        with start_action(player_logger, "load_custom_playlist", playlist_id=playlist_id):
            self._reset_to_standard_columns()

            for item in self.queue_view.queue.get_children():
                self.queue_view.queue.delete(item)
            self._item_filepath_map.clear()
            self._item_track_id_map.clear()

            self.queue_view.set_current_view(f"playlist:{playlist_id}")
            self._apply_music_view_column_widths()

            rows = self.db.get_playlist_items(playlist_id)
            if not rows:
                playlist_name = self.db.get_playlist_name(playlist_id)
                log_player_action(
                    "load_custom_playlist_empty",
                    trigger_source="gui",
                    playlist_id=playlist_id,
                    playlist_name=playlist_name or "Unknown",
                    description="Playlist is empty",
                )
                return

            for position, (filepath, artist, title, album, _track_num, date, track_id) in enumerate(rows, start=1):
                year = self._extract_year(date)
                row_tag = 'evenrow' if position % 2 == 1 else 'oddrow'
                item_id = self.queue_view.queue.insert(
                    '', 'end', values=(str(position), title or '', artist or '', album or '', year or ''), tags=(row_tag,)
                )
                self._item_filepath_map[item_id] = filepath
                self._item_track_id_map[item_id] = track_id

            self.refresh_colors()

            playlist_name = self.db.get_playlist_name(playlist_id)
            log_player_action(
                "load_custom_playlist_complete",
                trigger_source="gui",
                playlist_id=playlist_id,
                playlist_name=playlist_name or "Unknown",
                count=len(rows),
                description=f"Loaded {len(rows)} tracks from custom playlist '{playlist_name}'",
            )

    def _apply_music_view_column_widths(self):
        import contextlib

        music_widths = self.queue_view.load_column_preferences('music')
        if music_widths:
            for col_name, width in music_widths.items():
                with contextlib.suppress(Exception):
                    self.queue_view.queue.column(col_name, width=width)

    def _populate_queue_view(self, rows):
        """Populate queue view with rows of data."""
        # Keep a mapping of item_id to filepath for later use
        if not hasattr(self, '_item_filepath_map'):
            self._item_filepath_map = {}

        # Clear the mapping for this view
        self._item_filepath_map.clear()

        for i, (filepath, artist, title, album, track_number, date) in enumerate(rows):
            if os.path.exists(filepath):
                # Always store the formatted track number for metadata matching
                # In now_playing view, it will be replaced visually by refresh_colors
                formatted_track = self._format_track_number(track_number)

                # Use filename as fallback, but if that's empty too, use "Unknown Title"
                title = title or os.path.basename(filepath) or 'Unknown Title'
                artist = artist or 'Unknown Artist'
                year = self._extract_year(date)

                # Apply alternating row tags
                row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'

                # Create the item
                item_id = self.queue_view.queue.insert(
                    '', 'end', values=(formatted_track, title, artist, album or '', year), tags=(row_tag,)
                )

                # Store the filepath mapping
                self._item_filepath_map[item_id] = filepath

        # Select first item if any were added
        if self.queue_view.queue.get_children():
            first_item = self.queue_view.queue.get_children()[0]
            self.queue_view.queue.selection_set(first_item)
            self.queue_view.queue.see(first_item)

        # Apply playing track highlight if needed
        self.refresh_colors()

    def _format_track_number(self, track_number):
        """Format track number for display."""
        if not track_number:
            return ''
        try:
            track_num = track_number.split('/')[0]
            return f"{int(track_num):02d}"
        except (ValueError, IndexError):
            return ''

    def _extract_year(self, date):
        """Extract year from date string."""
        if not date:
            return ''
        try:
            return date.split('-')[0] if '-' in date else date[:4]
        except Exception:
            return ''

    def _format_added_date(self, added_date):
        """Format added_date timestamp for display.

        Converts "2025-10-21 16:20:30" to "Oct 21, 4:20 PM"
        """
        if not added_date:
            return ''
        try:
            from datetime import datetime

            # Parse the timestamp
            dt = datetime.strptime(added_date, '%Y-%m-%d %H:%M:%S')

            # Format as "Oct 21, 4:20 PM"
            return dt.strftime('%b %d, %-I:%M %p')
        except Exception:
            # If parsing fails, return as-is or empty
            return added_date if added_date else ''

    def _reset_to_standard_columns(self):
        """Reset treeview to standard 5-column layout."""
        self.queue_view.queue.configure(columns=('track', 'title', 'artist', 'album', 'year'))

        # Configure column headings
        self.queue_view.queue.heading('track', text='#')
        self.queue_view.queue.heading('title', text='Title')
        self.queue_view.queue.heading('artist', text='Artist')
        self.queue_view.queue.heading('album', text='Album')
        self.queue_view.queue.heading('year', text='Year')

        # Set column widths
        self.queue_view.queue.column('track', width=50, anchor='center')
        self.queue_view.queue.column('title', width=200, minwidth=100)
        self.queue_view.queue.column('artist', width=150, minwidth=80)
        self.queue_view.queue.column('album', width=150, minwidth=80)
        self.queue_view.queue.column('year', width=80, minwidth=60, anchor='center')

    def add_files_to_library(self):
        """Open file dialog and add selected files to library."""
        with start_action(player_logger, "add_files_to_library"):
            log_player_action(
                "add_files_dialog_opened", trigger_source="gui", description="User opened file dialog to add files to library"
            )

        home_dir = Path.home()
        music_dir = home_dir / 'Music'
        start_dir = str(music_dir if music_dir.exists() else home_dir)

        if sys.platform == 'darwin':
            try:
                # Try to import AppKit for native macOS file dialog
                from AppKit import NSURL, NSModalResponseOK, NSOpenPanel

                # Create and configure the open panel
                panel = NSOpenPanel.alloc().init()
                panel.setCanChooseFiles_(True)
                panel.setCanChooseDirectories_(True)
                panel.setAllowsMultipleSelection_(True)
                panel.setTitle_("Select Audio Files and Folders")
                panel.setMessage_("Select audio files and/or folders to add to your library")
                panel.setDirectoryURL_(NSURL.fileURLWithPath_(start_dir))

                # Run the panel
                if panel.runModal() == NSModalResponseOK:
                    # Get selected paths
                    paths = [str(url.path()) for url in panel.URLs()]
                    if paths:
                        selected_paths = []
                        for path in paths:
                            path_obj = Path(path)
                            if path_obj.is_dir():
                                mixed_paths = find_audio_files(path_obj)
                                if mixed_paths:
                                    selected_paths.extend([Path(p) for p in mixed_paths])
                            else:
                                selected_paths.append(path_obj)
                        if selected_paths:
                            log_player_action(
                                "add_files_to_library_processing",
                                trigger_source="gui",
                                file_count=len(selected_paths),
                                description=f"Adding {len(selected_paths)} files to library",
                            )

                            self.library_manager.add_files_to_library(selected_paths)

                            log_player_action(
                                "add_files_to_library_success",
                                trigger_source="gui",
                                file_count=len(selected_paths),
                                description=f"Successfully added {len(selected_paths)} files to library",
                            )

                            # Update statistics immediately
                            self.status_bar.update_statistics()
                            # Refresh view based on what's currently selected
                            self._refresh_current_section()
                return
            except ImportError:
                pass  # Fall back to tkinter dialog if AppKit is not available

        # Configure file types for standard dialog
        file_types = []
        for ext in sorted(AUDIO_EXTENSIONS):
            ext = ext.lstrip('.')
            file_types.extend([f'*.{ext}', f'*.{ext.upper()}'])

        # Use standard file dialog as fallback
        paths = filedialog.askopenfilenames(
            title="Select Audio Files", initialdir=start_dir, filetypes=[("Audio Files", ' '.join(file_types))]
        )

        if paths:
            selected_paths = [Path(p) for p in paths]
            if selected_paths:
                log_player_action(
                    "add_files_to_library_processing",
                    trigger_source="gui",
                    file_count=len(selected_paths),
                    description=f"Adding {len(selected_paths)} files to library",
                )

                self.library_manager.add_files_to_library(selected_paths)

                log_player_action(
                    "add_files_to_library_success",
                    trigger_source="gui",
                    file_count=len(selected_paths),
                    description=f"Successfully added {len(selected_paths)} files to library",
                )

                # Update statistics immediately
                self.status_bar.update_statistics()
                # Refresh view if needed
                selected_item = self.library_view.library_tree.selection()
                if selected_item:
                    tags = self.library_view.library_tree.item(selected_item[0])['tags']
                    if tags and tags[0] == 'music':
                        self.load_library()

    def _refresh_current_section(self):
        """Refresh the currently selected library section."""
        selected_item = self.library_view.library_tree.selection()
        if selected_item:
            tags = self.library_view.library_tree.item(selected_item[0])['tags']
            if tags:
                section = tags[0]
                # Reload the current section
                if section == 'music':
                    self.load_library()
                elif section == 'liked_songs':
                    self.load_liked_songs()
                elif section == 'recently_added':
                    self.load_recently_added()
                elif section == 'recently_played':
                    self.load_recently_played()
                elif section == 'top_played':
                    self.load_top_25_most_played()
        else:
            # No selection, default to loading music library
            self.load_library()

    def remove_tracks_from_library(self, item_ids: list[str]):
        """Remove selected tracks from library.

        Args:
            item_ids: List of Treeview item IDs
        """
        for item_id in item_ids:
            if item_id in self._item_filepath_map:
                filepath = self._item_filepath_map[item_id]
                self.library_manager.delete_from_library(filepath)

        # Refresh current view
        self._refresh_current_section()

    def remove_track_from_library(self, filepath: str):
        """Remove a single track from library (called from Now Playing view).

        Args:
            filepath: Path to track file
        """
        self.library_manager.delete_from_library(filepath)

    def edit_track_metadata(self, item_id: str):
        """Open metadata editor for a track or multiple selected tracks.

        Args:
            item_id: Treeview item ID of the track (used to get all selections)
        """
        from core.metadata import MetadataEditor

        with start_action(library_logger, "edit_metadata"):
            # Get all selected items
            selected_items = self.queue_view.queue.selection()

            # Get filepaths for all selected items
            filepaths = []
            for item in selected_items:
                filepath = self._item_filepath_map.get(item)
                if filepath:
                    filepaths.append(filepath)

            if not filepaths:
                return

            def on_save(file_path: str):
                """Callback after metadata is saved."""
                # Give the file system a moment to ensure metadata is written
                # This is especially important for m4a files
                import time

                time.sleep(0.1)

                # Update database with new metadata
                self.library_manager.update_track_metadata(file_path)

                # Refresh the current view
                if self.active_view == 'now_playing':
                    # Refresh Now Playing view
                    self.now_playing_view.refresh_from_queue()
                else:
                    # Refresh the current library view (music, liked_songs, top_played)
                    current_view = self.queue_view.current_view
                    if current_view == 'music':
                        self.load_library()
                    elif current_view == 'liked_songs':
                        self.load_liked_songs()
                    elif current_view == 'top_played':
                        self.load_top_25_most_played()

            # For batch editing, disable navigation
            if len(filepaths) > 1:
                MetadataEditor(self.window, filepaths, on_save, navigation_callback=None, has_prev=False, has_next=False)
            else:
                # Single file editing with navigation
                filepath = filepaths[0]

                def navigate_track(current_filepath: str, direction: int):
                    """Navigate to adjacent track in the library view."""
                    # Get all items in current order
                    all_items = self.queue_view.queue.get_children()

                    # Find current item index by filepath
                    current_index = None
                    for i, item in enumerate(all_items):
                        if self._item_filepath_map.get(item) == current_filepath:
                            current_index = i
                            break

                    if current_index is None:
                        return None, False, False

                    # Calculate new index
                    new_index = current_index + direction

                    # Check bounds
                    if new_index < 0 or new_index >= len(all_items):
                        return None, False, False

                    # Get new item and filepath
                    new_item = all_items[new_index]
                    new_filepath = self._item_filepath_map.get(new_item)

                    if not new_filepath:
                        return None, False, False

                    # Calculate has_prev and has_next for new position
                    has_prev = new_index > 0
                    has_next = new_index < len(all_items) - 1

                    return new_filepath, has_prev, has_next

                # Calculate has_prev and has_next for initial track
                all_items = self.queue_view.queue.get_children()
                current_index = None
                for i, item in enumerate(all_items):
                    if self._item_filepath_map.get(item) == filepath:
                        current_index = i
                        break

                has_prev = current_index > 0 if current_index is not None else False
                has_next = current_index < len(all_items) - 1 if current_index is not None else False

                MetadataEditor(self.window, filepath, on_save, navigate_track, has_prev, has_next)

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
