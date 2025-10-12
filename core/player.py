import importlib
import json
import mutagen
import os
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
import vlc
from config import (
    AUDIO_EXTENSIONS,
    BUTTON_STYLE,
    COLORS,
    DB_NAME,
    DEFAULT_LOOP_ENABLED,
    LISTBOX_CONFIG,
    MAX_SCAN_DEPTH,
    PROGRESS_BAR,
    PROGRESS_UPDATE_INTERVAL,
    RELOAD,
    THEME_CONFIG,
    WINDOW_SIZE,
    WINDOW_TITLE,
)
from contextlib import suppress
from core.controls import PlayerCore
from core.db import DB_TABLES, MusicDatabase
from core.favorites import FavoritesManager
from core.gui import (
    BUTTON_SYMBOLS,
    LibraryView,
    PlayerControls,
    ProgressBar,
    QueueView,
    SearchBar,
    StatusBar,
)
from core.library import LibraryManager
from core.logging import log_error, log_file_operation, log_player_action, player_logger
from core.progress import ProgressControl
from core.queue import QueueManager
from core.stoplight import StoplightButtons
from core.theme import setup_theme
from core.volume import VolumeControl
from eliot import start_action
from pathlib import Path
from tkinter import filedialog, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from utils.files import find_audio_files, normalize_path
from utils.reload import ConfigFileHandler
from watchdog.observers import Observer

# Import AppKit for media key support on macOS
if sys.platform == 'darwin':
    try:
        import Quartz
        from utils.mediakeys import MediaKeyController

        MEDIA_KEY_SUPPORT = True
    except ImportError:
        MEDIA_KEY_SUPPORT = False
else:
    MEDIA_KEY_SUPPORT = False


class MusicPlayer:
    def __init__(self, window):
        self.window = window
        self.window.title(WINDOW_TITLE)

        self.window.geometry(WINDOW_SIZE)
        self.window.update()  # Force update after setting initial geometry
        self.window.minsize(1280, 720)

        # Setup theme and styles first
        # setup_theme(self.window)  # Commented out - theme should be set up before creating MusicPlayer

        # Configure macOS specific appearance
        if sys.platform == 'darwin':
            # Remove title bar for seamless black appearance
            self.window.wm_attributes('-fullscreen', False)
            self.window.overrideredirect(True)
            # Set document style with dark appearance
            self.window.tk.call('::tk::unsupported::MacWindowStyle', 'style', self.window._w, 'document')
            self.window.tk.call('::tk::unsupported::MacWindowStyle', 'appearance', self.window._w, 'dark')
            self.window.createcommand('tk::mac::Quit', self.window.destroy)

        self.reload_enabled = RELOAD

        # Initialize file watcher if enabled
        self.setup_file_watcher()

        # Setup media key support
        if sys.platform == 'darwin' and MEDIA_KEY_SUPPORT:
            self.media_key_controller = MediaKeyController(self.window)

    def setup_components(self):
        """Initialize and setup all components."""
        from eliot import log_message

        log_message(message_type="component_init", message="Starting component initialization")

        # Initialize database and managers
        self.db = MusicDatabase(DB_NAME, DB_TABLES)
        self.queue_manager = QueueManager(self.db)
        self.library_manager = LibraryManager(self.db)
        self.favorites_manager = FavoritesManager(self.db)

        log_message(message_type="component_init", component="database", message="Database and managers initialized")

        # Load window size and position before creating UI components to prevent visible resize
        saved_size = self.db.get_window_size()
        if saved_size:
            width, height = saved_size
            self.window.geometry(f"{width}x{height}")
            self.window.update()

        # Load saved window position
        self.load_window_position()

        # Create search bar with integrated stoplight buttons (spans full width)
        self.search_bar = SearchBar(
            self.window,
            {
                'search': self.perform_search,
                'clear_search': self.clear_search,
                'on_window_state_change': self.on_window_state_change,
            },
        )

        # Create main container below the search bar
        self.main_container = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        self.main_container.pack(expand=True, fill=tk.BOTH)

        # Create left panel (Library/Playlists)
        self.left_panel = ttk.Frame(self.main_container)
        self.main_container.add(self.left_panel, weight=0)  # weight=0 means it won't expand

        # Create right panel (Content)
        self.right_panel = ttk.Frame(self.main_container)
        self.main_container.add(self.right_panel, weight=1)  # weight=1 means it will expand

        # Setup views with callbacks (without search bar since it's now at window level)
        self.setup_views()

        # Set minimum width for left panel based on library view content
        if hasattr(self.library_view, 'min_width'):
            # Set the left panel width to the calculated minimum
            self.left_panel.configure(width=self.library_view.min_width)

        # Load and apply saved UI preferences (after setting minimum width)
        self.load_ui_preferences()

        # Initialize player core after views are set up
        self.player_core = PlayerCore(self.db, self.queue_manager, self.queue_view.queue)
        self.player_core.window = self.window  # Set window reference for thread-safe callbacks
        self.player_core.favorites_manager = self.favorites_manager  # Set favorites manager reference

        # Create frame for progress bar with black background
        self.progress_frame = tk.Frame(self.window, height=80, bg="#000000")
        self.progress_frame.pack(
            side=tk.BOTTOM,
            fill=tk.X,
            padx=0,  # Remove padding to eliminate grey outline
            pady=0,  # Remove padding to eliminate grey outline
        )

        # Create status bar just above the progress bar
        self.status_bar = StatusBar(self.window, self.library_manager)

        # Setup progress bar with callbacks
        self.progress_bar = ProgressBar(
            self.window,
            self.progress_frame,
            {
                'previous': self.player_core.previous_song,
                'play': self.play_pause,
                'next': self.player_core.next_song,
                'loop': self.player_core.toggle_loop,
                'shuffle': self.player_core.toggle_shuffle,
                'add': self.add_files_to_library,
                'favorite': self.toggle_favorite,
                'start_drag': self.start_drag,
                'drag': self.drag,
                'end_drag': self.end_drag,
                'click_progress': self.click_progress,
                'on_resize': self.on_resize,
                'volume_change': self.volume_change,
            },
            initial_loop_enabled=self.player_core.loop_enabled,
            initial_shuffle_enabled=self.player_core.shuffle_enabled,
        )

        # Connect progress bar to player core
        self.player_core.progress_bar = self.progress_bar

        # Setup favorites callback to refresh view when favorites change
        self.favorites_manager.set_on_favorites_changed_callback(self.on_favorites_changed)

        # Start progress update
        self.update_progress()

        # Initialize the volume after a delay to ensure VLC is ready
        self.window.after(1000, lambda: self.player_core.set_volume(80))

        # If media key controller exists, set this instance as the player
        if hasattr(self, 'media_key_controller'):
            self.media_key_controller.set_player(self)

        # Bind events to save UI preferences
        self.window.bind('<Configure>', self.on_window_configure)
        self.main_container.bind('<ButtonRelease-1>', self.on_paned_resize)

        # Save preferences on window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # Make the close method available to stoplight buttons via search bar
        self.window.on_window_close = self.on_window_close

        # Track playback context (which view we're playing from)
        self.playback_context = 'music'  # Default to music library

    def setup_api_server(self):
        """Initialize and start the API server if enabled."""
        from api.api import APIServer
        from config import API_SERVER_ENABLED, API_SERVER_PORT
        from eliot import log_message

        if not API_SERVER_ENABLED:
            log_message(message_type="api_server_disabled",
                       message="API server is disabled in configuration")
            return

        try:
            # Create and start the API server
            self.api_server = APIServer(self, port=API_SERVER_PORT)
            result = self.api_server.start()

            if result['status'] == 'success':
                log_message(message_type="api_server_initialized",
                           port=API_SERVER_PORT,
                           message="API server successfully started")
            else:
                log_message(message_type="api_server_failed",
                           error=result.get('message', 'Unknown error'),
                           message="Failed to start API server")
                self.api_server = None

        except Exception as e:
            log_message(message_type="api_server_exception",
                       error=str(e),
                       message="Exception during API server initialization")
            self.api_server = None

    def setup_views(self):
        """Setup library and queue views with their callbacks."""
        # Setup library view
        self.library_view = LibraryView(
            self.left_panel,
            {
                'on_section_select': self.on_section_select,
            },
        )

        # Setup queue view (search bar is now at window level)
        self.queue_view = QueueView(
            self.right_panel,
            {
                'play_selected': self.play_selected,
                'handle_delete': self.handle_delete,
                'on_song_select': self.on_song_select,
                'handle_drop': self.handle_drop,
                'save_column_widths': self.save_column_widths,
            },
        )

    def load_ui_preferences(self):
        """Load and apply saved UI preferences."""
        try:
            # Window size is now loaded in setup_components() before UI creation

            # Load left panel width - always use scheduled setting to ensure proper timing
            saved_left_width = self.db.get_left_panel_width()
            if saved_left_width:
                # Schedule setting after window geometry is fully applied and UI is ready
                self.window.after(500, lambda: self._set_left_panel_width(saved_left_width))

            # Load queue column widths - let Treeview Map event handle application
            saved_column_widths = self.db.get_queue_column_widths()
            if saved_column_widths and hasattr(self.queue_view, '_pending_column_widths'):
                # Store for Map event handler to apply when Treeview becomes visible
                self.queue_view._pending_column_widths = saved_column_widths

            # Start periodic column width checking after preferences are loaded
            if hasattr(self.queue_view, 'start_column_check'):
                self.window.after(500, lambda: self.queue_view.start_column_check())
        except Exception:
            pass

    def _set_left_panel_width(self, width):
        """Set the left panel width by adjusting the sash position."""
        if hasattr(self.library_view, 'min_width') and hasattr(self, 'main_container'):
            # Use the larger of saved width and minimum width
            final_width = max(width, self.library_view.min_width)
            try:
                # Ensure the paned window is ready before setting sash position
                if self.main_container.winfo_exists():
                    self.main_container.sashpos(0, final_width)
                    # Force update to ensure the change takes effect
                    self.window.update_idletasks()
            except Exception as e:
                # If sashpos fails, try setting frame width
                with suppress(Exception):
                    self.left_panel.configure(width=final_width)

    def _apply_column_widths(self, saved_column_widths):
        """Apply saved column widths to the queue Treeview."""
        if saved_column_widths and hasattr(self, 'queue_view'):
            for col_name, width in saved_column_widths.items():
                with suppress(Exception):
                    self.queue_view.queue.column(col_name, width=width)
            # Update the last known widths so periodic check doesn't save immediately
            if hasattr(self.queue_view, '_last_column_widths'):
                self.queue_view._last_column_widths = self.queue_view.get_column_widths()

    def setup_file_watcher(self):
        """Setup file watcher for development mode."""
        if self.reload_enabled:
            print("Development mode: watching for file changes...")
            self.observer = Observer()
            event_handler = ConfigFileHandler(self)
            self.observer.schedule(event_handler, path='.', recursive=False)
            self.observer.start()
        else:
            self.observer = None

    def play_pause(self):
        """Handle play/pause button click."""
        with start_action(player_logger, "play_pause_action"):
            log_player_action("play_pause", was_playing=self.player_core.is_playing)

        was_playing = self.player_core.is_playing
        self.player_core.play_pause()

        # Update play button appearance
        self.progress_bar.controls.update_play_button(self.player_core.is_playing)

        # Refresh colors to update play/pause indicator in Now Playing view
        self.refresh_colors()

        # Show playback elements if we started playing, hide if we stopped
        if not was_playing and self.player_core.is_playing:
            self.progress_bar.progress_control.show_playback_elements()
            from eliot import log_message

            log_message(message_type="playback_state", state="started", message="Playback started")
        elif was_playing and not self.player_core.is_playing:
            # Optional: hide playback elements when paused
            # self.progress_bar.progress_control.hide_playback_elements()
            from eliot import log_message

            log_message(message_type="playback_state", state="paused", message="Playback paused")
            pass

    def toggle_favorite(self):
        """Toggle favorite status for currently playing track."""
        # Only allow favoriting if a track is actually playing (not just selected)
        if not self.player_core.media_player.get_media():
            # No track is loaded
            return

        # Check if player is actually playing or paused (but has media loaded)
        if not self.player_core.is_playing and self.player_core.media_player.get_state() not in [3, 4]:
            # Track is not playing or paused (states 3=Playing, 4=Paused)
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
        import urllib.parse

        filepath = urllib.parse.unquote(filepath)

        if not filepath or not os.path.exists(filepath):
            return

        # Toggle favorite status
        is_favorite = self.favorites_manager.toggle_favorite(filepath)

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

    def on_section_select(self, event):
        """Handle library section selection."""
        with start_action(player_logger, "section_switch"):
            selected_item = self.library_view.library_tree.selection()[0]
            tags = self.library_view.library_tree.item(selected_item)['tags']

            if not tags:
                log_player_action("section_switch_no_tags", trigger_source="gui", reason="no_tags_found")
                return

            # Get previous view state
            previous_children_count = len(self.queue_view.queue.get_children())

            new_section = tags[0]

            log_player_action(
                "section_switch",
                trigger_source="gui",
                new_section=new_section,
                previous_item_count=previous_children_count,
                description=f"Switched to {new_section} section",
            )

            # Clear current view
            for item in self.queue_view.queue.get_children():
                self.queue_view.queue.delete(item)

            if new_section == 'music':
                self.load_library()
                new_count = len(self.queue_view.queue.get_children())
                log_player_action(
                    "section_switch_complete",
                    trigger_source="gui",
                    section="music",
                    loaded_items=new_count,
                    description=f"Loaded {new_count} library items",
                )
            elif new_section == 'now_playing':
                self.load_queue()
                new_count = len(self.queue_view.queue.get_children())
                log_player_action(
                    "section_switch_complete",
                    trigger_source="gui",
                    section="now_playing",
                    loaded_items=new_count,
                    description=f"Loaded {new_count} queue items",
                )
            elif new_section == 'liked_songs':
                self.load_liked_songs()
                new_count = len(self.queue_view.queue.get_children())
                log_player_action(
                    "section_switch_complete",
                    trigger_source="gui",
                    section="liked_songs",
                    loaded_items=new_count,
                    description=f"Loaded {new_count} liked songs",
                )
            elif new_section == 'top_played':
                self.load_top_25_most_played()
                new_count = len(self.queue_view.queue.get_children())
                log_player_action(
                    "section_switch_complete",
                    trigger_source="gui",
                    section="top_played",
                    loaded_items=new_count,
                    description=f"Loaded {new_count} top played tracks",
                )

    def load_library(self):
        """Load and display library items."""
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

    def load_queue(self):
        """Load and display queue items - mirrors the current playback context."""
        # Set column header to "Playing"
        self.queue_view.set_track_column_header('Playing')

        # Adjust column width for "Playing" header (needs more space than "#")
        self.queue_view.queue.column('track', width=80, minwidth=70)

        # Set current view and restore column widths
        self.queue_view.set_current_view('now_playing')

        # Initialize filepath mapping if needed
        if not hasattr(self, '_item_filepath_map'):
            self._item_filepath_map = {}

        # Clear current view and mapping
        for item in self.queue_view.queue.get_children():
            self.queue_view.queue.delete(item)
        self._item_filepath_map.clear()

        # Load tracks based on playback context (what view we're playing from)
        if self.playback_context == 'music':
            # Playing from library - show all library tracks
            rows = self.library_manager.get_library_items()
            if rows:
                self._populate_queue_view(rows)
        elif self.playback_context == 'liked_songs':
            # Playing from liked songs - show liked songs
            rows = self.favorites_manager.get_liked_songs()
            for i, (filepath, artist, title, album, track_num, date) in enumerate(rows):
                formatted_track = self._format_track_number(track_num)
                year = self._extract_year(date)
                row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                # Store the actual track number for matching, will be replaced by indicator in refresh_colors
                item_id = self.queue_view.queue.insert(
                    '', 'end', values=(formatted_track, title or '', artist or '', album or '', year or ''), tags=(row_tag,)
                )
                # Store filepath mapping
                self._item_filepath_map[item_id] = filepath
        elif self.playback_context == 'top_played':
            # Playing from top 25 - show top 25
            rows = self.library_manager.get_top_25_most_played()
            if rows:
                for i, (filepath, artist, title, album, _play_count, date) in enumerate(rows):
                    # For top_played, track_number isn't available, so we pass empty string
                    # This view shows play count in the first column instead
                    year = self._extract_year(date)
                    row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                    item_id = self.queue_view.queue.insert(
                        '', 'end', values=('', title or '', artist or '', album or '', year or ''), tags=(row_tag,)
                    )
                    # Store filepath mapping
                    self._item_filepath_map[item_id] = filepath
        else:
            # Fallback: use queue table (legacy behavior)
            rows = self.queue_manager.get_queue_items()
            if rows:
                self._populate_queue_view(rows)

        self.refresh_colors()

    def load_liked_songs(self):
        """Load and display liked songs."""
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
                '',
                'end',
                values=(formatted_track, title or '', artist or '', album or '', year or ''),
                tags=(row_tag,)
            )
            # Store filepath mapping
            self._item_filepath_map[item_id] = filepath

    def load_top_25_most_played(self):
        """Load and display top 25 most played tracks."""
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
                '',
                'end',
                values=(str(play_count), title or '', artist or '', album or '', year or ''),
                tags=(row_tag,)
            )
            # Store filepath mapping
            self._item_filepath_map[item_id] = filepath
        self.refresh_colors()

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

    def add_files_to_library(self):
        """Open file dialog and add selected files to library."""
        home_dir = Path.home()
        music_dir = home_dir / 'Music'
        start_dir = str(music_dir if music_dir.exists() else home_dir)

        if sys.platform == 'darwin':
            try:
                # Try to import AppKit for native macOS file dialog
                from AppKit import NSURL, NSApplication, NSModalResponseOK, NSOpenPanel

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
                            self.library_manager.add_files_to_library(selected_paths)
                            # Update statistics immediately
                            self.status_bar.update_statistics()
                            # Refresh view if needed
                            selected_item = self.library_view.library_tree.selection()
                            if selected_item:
                                tags = self.library_view.library_tree.item(selected_item[0])['tags']
                                if tags and tags[0] == 'music':
                                    self.load_library()
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
                self.library_manager.add_files_to_library(selected_paths)
                # Update statistics immediately
                self.status_bar.update_statistics()
                # Refresh view if needed
                selected_item = self.library_view.library_tree.selection()
                if selected_item:
                    tags = self.library_view.library_tree.item(selected_item[0])['tags']
                    if tags and tags[0] == 'music':
                        self.load_library()

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
            success = False

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
                            success = True
                        elif tags[0] == 'now_playing':
                            self.library_manager.add_files_to_library(valid_paths)
                            # Update statistics immediately
                            self.status_bar.update_statistics()
                            self.queue_manager.process_dropped_files(valid_paths)
                            self.load_queue()
                            success = True

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

    def play_selected(self, event=None):
        """Play the selected track."""
        from eliot import log_message, start_action

        with start_action(player_logger, "play_selected_action"):
            selected_items = self.queue_view.queue.selection()
            if not selected_items:
                return "break"

            item_values = self.queue_view.queue.item(selected_items[0])['values']
            if not item_values:
                return "break"

            track_num, title, artist, album, year = item_values

            # Format track number to ensure it's zero-padded for database matching
            # Tkinter may strip leading zeros, so we need to reformat
            if track_num:
                try:
                    track_num = f"{int(track_num):02d}"
                except (ValueError, TypeError):
                    pass  # Keep original if formatting fails

            # Use strict matching to ensure we play the exact track that was selected
            # This prevents fallback to title-only matching which could load wrong versions
            filepath = self.db.find_file_by_metadata_strict(title, artist, album, track_num)

            # Log the double-click action with track details
            log_player_action("play_selected", title=title, artist=artist, album=album, filepath=filepath)

            if filepath and os.path.exists(filepath):
                # Track playback context (which view we're playing from)
                self.playback_context = self.queue_view.current_view

                was_playing = self.player_core.is_playing
                self.player_core._play_file(filepath)
                self.progress_bar.controls.update_play_button(True)

                # Update favorite button icon based on track's favorite status
                is_favorite = self.favorites_manager.is_favorite(filepath)
                self.progress_bar.controls.update_favorite_button(is_favorite)

                # Refresh colors to highlight the playing track
                self.refresh_colors()

                # Log playback state change like play/pause does
                if not was_playing:
                    log_message(message_type="playback_state", state="started", message="Playback started from library selection")
                else:
                    log_message(
                        message_type="playback_state", state="track_changed", message="Track changed from library selection"
                    )

        return "break"

    def handle_delete(self, event):
        """Handle delete key press - deletes from library or queue based on current view."""
        with start_action(player_logger, "track_delete"):
            selected_items = self.queue_view.queue.selection()
            if not selected_items:
                log_player_action("track_delete_no_selection", trigger_source="keyboard", reason="no_items_selected")
                return

            deleted_tracks = []
            current_view = self.queue_view.current_view

            # Determine if we're deleting from library or queue
            is_queue_view = current_view == 'now_playing'

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
                    if hasattr(self, 'library_manager') and self.library_manager:
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

                    if is_queue_view:
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
            if not is_queue_view and hasattr(self, 'status_bar'):
                self.status_bar.update_statistics()

            self.refresh_colors()
            return "break"

    def on_song_select(self, event):
        """Handle song selection in queue view."""
        # This method can be used to update UI or track the currently selected song
        pass

    def perform_search(self, search_text):
        """Handle search functionality."""
        from eliot import log_message

        log_message(message_type="search_action", search_text=search_text, message="Performing search")

        # Get current section from library view
        selected_item = self.library_view.library_tree.selection()
        if not selected_item:
            return

        tags = self.library_view.library_tree.item(selected_item[0])['tags']
        if not tags:
            return

        tag = tags[0]

        # Clear current view
        for item in self.queue_view.queue.get_children():
            self.queue_view.queue.delete(item)

        if tag == 'music':
            # Search in library
            rows = self.library_manager.search_library(search_text) if search_text else self.library_manager.get_library_items()
        elif tag == 'now_playing':
            # Search in queue
            rows = self.queue_manager.search_queue(search_text) if search_text else self.queue_manager.get_queue_items()
        else:
            return

        if rows:
            self._populate_queue_view(rows)
            self.refresh_colors()

    def clear_search(self):
        """Clear search and reload current view."""
        from eliot import log_message

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
                elif tag == 'now_playing':
                    self.load_queue()

    def on_window_state_change(self, is_maximized):
        """Handle window state changes (maximize/unmaximize) to adjust column widths."""
        if hasattr(self, 'queue_view'):
            self.queue_view.on_window_state_change(is_maximized)

    def refresh_colors(self):
        """Update the background colors of all items in the queue view."""
        # Get the currently playing filepath if available (even if paused)
        current_filepath = None
        if hasattr(self, 'player_core'):
            # Check if there's media loaded (works for both playing and paused)
            media = self.player_core.media_player.get_media()
            if media:
                current_filepath = media.get_mrl()
                # Convert file:// URL to normal path
                if current_filepath.startswith('file://'):
                    current_filepath = current_filepath[7:]
                # On macOS, decode URL characters
                import urllib.parse
                current_filepath = urllib.parse.unquote(current_filepath)

        # Check if we're in now_playing view to update play/pause indicators
        is_now_playing_view = self.queue_view.current_view == 'now_playing'
        is_currently_playing = hasattr(self, 'player_core') and self.player_core.is_playing

        # Configure all the tag styles before applying them
        # Define playing tag - strong teal highlight
        playing_bg = THEME_CONFIG['colors'].get('playing_bg', '#00343a')
        playing_fg = THEME_CONFIG['colors'].get('playing_fg', '#33eeff')

        # Configure the tag style for the playing track
        self.queue_view.queue.tag_configure('playing', background=playing_bg, foreground=playing_fg)

        # Configure even/odd row tag styles
        self.queue_view.queue.tag_configure('evenrow', background=THEME_CONFIG['colors']['bg'])
        self.queue_view.queue.tag_configure('oddrow', background=THEME_CONFIG['colors'].get('row_alt', '#242424'))

        # Process each row in the queue view
        for i, item in enumerate(self.queue_view.queue.get_children()):
            values = self.queue_view.queue.item(item, 'values')
            if not values or len(values) < 3:  # Need at least track, title, artist
                continue

            # Get the stored filepath directly from our mapping
            item_filepath = self._item_filepath_map.get(item) if hasattr(self, '_item_filepath_map') else None

            # If no mapping exists, fallback to metadata matching (backwards compatibility)
            if not item_filepath:
                track_num, title, artist, album, year = values
                # Format track number only if it's not an indicator
                track_for_matching = track_num
                if track_for_matching and track_for_matching not in ['▶', '⏸', '']:
                    try:
                        track_for_matching = f"{int(track_for_matching):02d}"
                    except (ValueError, TypeError):
                        pass
                item_filepath = self.db.find_file_by_metadata_strict(title, artist, album, track_for_matching)

            # Check if this item is the currently playing track
            is_current = False
            if current_filepath and item_filepath:
                if os.path.normpath(item_filepath) == os.path.normpath(current_filepath):
                    is_current = True

            # Update the first column with play/pause indicator if in now_playing view
            if is_now_playing_view:
                track_num, title, artist, album, year = values
                indicator = ('▶' if is_currently_playing else '⏸') if is_current else ''
                # Update the first column value with indicator
                self.queue_view.queue.item(item, values=(indicator, title, artist, album, year))

            if is_current:
                # This is the currently playing track - highlight with teal
                self.queue_view.queue.item(item, tags=('playing',))
            else:
                # Determine if this is an even or odd row for alternating colors
                row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.queue_view.queue.item(item, tags=(row_tag,))  # Debug log  # Debug log  # Debug log  # Debug log  # Debug log  # Debug log  # Debug log

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
            and (current_time - self.progress_bar.last_drag_time) > 0.1
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
            max_width = self.progress_bar.canvas.winfo_width() - 260

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
            max_width = self.progress_bar.canvas.winfo_width() - 260
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
        max_x = self.progress_bar.canvas.winfo_width() - 260

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
        width = self.progress_bar.canvas.winfo_width() - controls_width - 260

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

        # Use consistent calculation: event.width - 260
        # The 260 value accounts for time display (right_margin of 160) plus volume control (approx 100px)
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
                except Exception as e:
                    log_player_action("volume_change_error", trigger_source="gui", attempted_volume=new_volume, error=str(e))

    def on_window_configure(self, event):
        """Handle window resize/configure events."""
        # Only save if this is the main window and not during initial setup
        if event.widget == self.window and hasattr(self, 'db'):
            # Skip saving if dimensions are too small (likely during initialization)
            if event.width <= 100 or event.height <= 100:
                return

            # Skip saving during the first few seconds after startup to avoid
            # overriding loaded preferences
            if not hasattr(self, '_startup_time'):
                from time import time

                self._startup_time = time()

            from time import time

            if time() - self._startup_time < 2.0:  # Skip for first 2 seconds
                return

            # Debounce saves to avoid excessive database writes
            if not hasattr(self, '_window_save_timer'):
                self._window_save_timer = None

            if self._window_save_timer:
                self.window.after_cancel(self._window_save_timer)

            # Save both size and position after 500ms of no resize events
            self._window_save_timer = self.window.after(
                500, lambda: (self.save_window_size(event.width, event.height), self.save_window_position())
            )

    def on_paned_resize(self, event):
        """Handle paned window resize (left panel width changes)."""
        from core.logging import controls_logger, log_player_action
        from eliot import start_action

        with start_action(controls_logger, "panel_resize"):
            if hasattr(self, 'db'):
                # Get current sash position
                sash_pos = self.main_container.sashpos(0)
                if sash_pos > 0:
                    # Get existing panel width for comparison
                    existing_width = self.db.get_left_panel_width() or 0
                    window_geometry = self.window.geometry()

                    log_player_action(
                        "panel_resize",
                        trigger_source="user_drag",
                        old_panel_width=existing_width,
                        new_panel_width=sash_pos,
                        width_change=sash_pos - existing_width,
                        window_geometry=window_geometry,
                        panel_type="left_library_panel",
                        description=f"Left panel resized from {existing_width}px to {sash_pos}px",
                    )

                    self.db.set_left_panel_width(sash_pos)

    def save_column_widths(self, widths):
        """Save queue column widths for the current view."""
        from core.logging import controls_logger, log_player_action
        from eliot import start_action

        with start_action(controls_logger, "save_column_preferences"):
            if hasattr(self, 'db') and hasattr(self, 'queue_view'):
                # Get current view name
                current_view = self.queue_view.current_view

                # Get existing widths for comparison
                existing_widths = self.db.get_queue_column_widths(current_view) or {}

                # Calculate what's actually being persisted
                persisted_changes = {}
                for col_name, width in widths.items():
                    old_width = existing_widths.get(col_name, 0)
                    if width != old_width:
                        persisted_changes[col_name] = {'old_width': old_width, 'new_width': width}
                        self.db.set_queue_column_width(col_name, width, current_view)

                log_player_action(
                    "column_preferences_saved",
                    trigger_source="periodic_check",
                    view=current_view,
                    widths_saved=widths,
                    existing_widths=existing_widths,
                    persisted_changes=persisted_changes,
                    columns_changed=len(persisted_changes),
                    total_columns=len(widths),
                    description=f"Column preferences persisted for {len(persisted_changes)} changed columns in {current_view} view",
                )

    def save_window_size(self, width, height):
        """Save window size to database."""
        # Only save reasonable window sizes
        if hasattr(self, 'db') and width > 100 and height > 100:
            self.db.set_window_size(width, height)

    def save_window_position(self):
        """Save window position to database."""
        if hasattr(self, 'db') and hasattr(self, 'window'):
            # Don't save position if window is maximized, minimized, or iconified
            state = self.window.wm_state()
            if state in ('zoomed', 'iconic', 'withdrawn'):
                return

            # Get current window position
            position = self.window.winfo_geometry()
            if position:
                self.db.set_window_position(position)

    def load_window_position(self):
        """Load and apply saved window position."""
        if hasattr(self, 'db') and hasattr(self, 'window'):
            saved_position = self.db.get_window_position()
            if saved_position:
                try:
                    self.window.geometry(saved_position)
                    self.window.update()
                except Exception:
                    # If position is invalid, ignore it
                    pass

        # Stop API server if running
        if hasattr(self, 'api_server') and self.api_server:
            self.api_server.stop()

    def on_window_close(self):
        """Handle window close event - save final UI state."""
        # Save current column widths before closing
        if hasattr(self, 'queue_view') and hasattr(self.queue_view, 'queue'):
            columns = ['track', 'title', 'artist', 'album', 'year']
            for col in columns:
                try:
                    width = self.queue_view.queue.column(col, 'width')
                    self.db.set_queue_column_width(col, width)
                except Exception:
                    pass

        # Save final window size and position (only if window is not minimized/iconified)
        # Check if window is iconified (minimized)
        if hasattr(self, 'window') and self.window.wm_state() != 'iconic':
            geometry = self.window.geometry()
            # Parse geometry string like "1400x800+100+100"
            if 'x' in geometry:
                size_part = geometry.split('+')[0]  # Get "1400x800" part
                try:
                    width, height = size_part.split('x')
                    # Only save if dimensions are reasonable (not 1x1)
                    if int(width) > 100 and int(height) > 100:
                        self.db.set_window_size(int(width), int(height))
                except ValueError:
                    pass

            # Save final window position
            self.save_window_position()

        # Close the window
        self.window.destroy()

    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'observer') and self.observer:
            self.observer.stop()
            self.observer.join()

        if hasattr(self, 'db'):
            self.db.close()
