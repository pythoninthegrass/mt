"""Main music player - composes all components and manages application lifecycle."""

import os
import sys
import tkinter as tk
from .handlers import PlayerEventHandlers
from .library import PlayerLibraryManager
from .progress import PlayerProgressController
from .queue import PlayerQueueHandler
from .ui import PlayerUIManager
from .window import PlayerWindowManager
from config import (
    DB_NAME,
    RELOAD,
    WINDOW_SIZE,
    WINDOW_TITLE,
)
from core.controls import PlayerCore
from core.db import DB_TABLES, MusicDatabase
from core.favorites import FavoritesManager
from core.gui import (
    LibraryView,
    ProgressBar,
    QueueView,
    SearchBar,
    StatusBar,
)
from core.library import LibraryManager
from core.queue import QueueManager
from tkinter import ttk
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
    """Main music player class that composes all functionality modules."""

    def __init__(self, window):
        """Initialize the music player.

        Args:
            window: Main Tkinter window
        """
        self.window = window
        self.window.title(WINDOW_TITLE)

        self.window.geometry(WINDOW_SIZE)
        self.window.update()  # Force update after setting initial geometry
        self.window.minsize(1280, 720)

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

        # Track currently active view (used by multiple managers)
        self.active_view = 'library'

        # Track item to filepath mapping (shared across managers)
        self._item_filepath_map = {}

    def setup_components(self):
        """Initialize and setup all components."""
        from eliot import log_message

        log_message(message_type="component_init", message="Starting component initialization")

        # Initialize database and managers
        self.db = MusicDatabase(DB_NAME, DB_TABLES)
        self.queue_manager = QueueManager(self.db)
        self.library_manager = LibraryManager(self.db)
        self.favorites_manager = FavoritesManager(self.db)

        # Initialize lyrics manager
        from core.lyrics import LyricsManager

        self.lyrics_manager = LyricsManager(self.db)

        log_message(message_type="component_init", component="database", message="Database and managers initialized")

        # Load window size and position before creating UI components to prevent visible resize
        saved_size = self.db.get_window_size()
        if saved_size:
            width, height = saved_size
            self.window.geometry(f"{width}x{height}")
            self.window.update()

        # Create search bar with integrated stoplight buttons (spans full width)
        self.search_bar = SearchBar(
            self.window,
            {
                'search': lambda text: self.event_handlers.perform_search(text),
                'clear_search': lambda: self.event_handlers.clear_search(),
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

        # Setup views with callbacks
        self.setup_views()

        # Set minimum width for left panel based on library view content
        if hasattr(self.library_view, 'min_width'):
            # Set the left panel width to the calculated minimum
            self.left_panel.configure(width=self.library_view.min_width)

        # Initialize player core after views are set up
        self.player_core = PlayerCore(self.db, self.queue_manager, self.queue_view.queue)
        self.player_core.window = self.window  # Set window reference for thread-safe callbacks
        self.player_core.favorites_manager = self.favorites_manager  # Set favorites manager reference

        # Give Now Playing view reference to player_core so it can check media state
        self.now_playing_view.player_core = self.player_core

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

        # Get saved volume from database
        initial_volume = self.db.get_volume()

        # Initialize manager modules
        self._init_manager_modules()

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
                'add': self.library_handler.add_files_to_library,
                'favorite': self.event_handlers.toggle_favorite,
                'start_drag': self.progress_controller.start_drag,
                'drag': self.progress_controller.drag,
                'end_drag': self.progress_controller.end_drag,
                'click_progress': self.progress_controller.click_progress,
                'on_resize': self.progress_controller.on_resize,
                'volume_change': self.progress_controller.volume_change,
            },
            initial_loop_enabled=self.player_core.loop_enabled,
            initial_repeat_one=self.player_core.repeat_one,
            initial_shuffle_enabled=self.player_core.shuffle_enabled,
            initial_volume=initial_volume,
        )

        # Connect progress bar to player core, progress controller, queue handler, and event handlers
        self.player_core.progress_bar = self.progress_bar
        self.progress_controller.progress_bar = self.progress_bar
        self.queue_handler.progress_bar = self.progress_bar
        self.event_handlers.progress_bar = self.progress_bar

        # Connect track change callback to refresh Now Playing view
        self.player_core.on_track_change = self.event_handlers.on_track_change

        # Connect play count callback to reset tracking flag
        self.player_core.play_count_updated_callback = self.progress_controller.set_play_count_updated

        # Update Now Playing view with player_core's initial loop state
        if hasattr(self.now_playing_view, 'set_loop_enabled'):
            self.now_playing_view.set_loop_enabled(self.player_core.loop_enabled)

        # Setup favorites callback to refresh view when favorites change
        self.favorites_manager.set_on_favorites_changed_callback(self.event_handlers.on_favorites_changed)

        # Load and apply saved UI preferences
        self.ui_manager.load_ui_preferences()

        # Load window position
        self.window_manager.load_window_position()

        # Start progress update
        self.progress_controller.update_progress()

        # Initialize VLC volume after a delay to ensure it's ready
        # UI volume is already set during ProgressBar initialization
        self.window.after(1000, lambda: self.player_core.set_volume(initial_volume))

        # If media key controller exists, set this instance as the player
        if hasattr(self, 'media_key_controller'):
            self.media_key_controller.set_player(self)

        # Bind events to save UI preferences
        self.window.bind('<Configure>', self.window_manager.on_window_configure)
        self.main_container.bind('<ButtonRelease-1>', self.window_manager.on_paned_resize)

        # Save preferences on window close
        self.window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close())

        # Make the close method available to stoplight buttons via search bar
        self.window.on_window_close = lambda: self.on_window_close()

    def _init_manager_modules(self):
        """Initialize all manager modules for delegation."""
        # UI Manager
        self.ui_manager = PlayerUIManager(
            window=self.window,
            db=self.db,
            library_view=self.library_view,
            queue_view=self.queue_view,
            now_playing_view=self.now_playing_view,
            queue_manager=self.queue_manager,
            main_container=self.main_container,
            left_panel=self.left_panel,
        )
        # Share the item filepath map
        self.ui_manager._item_filepath_map = self._item_filepath_map

        # Window Manager
        self.window_manager = PlayerWindowManager(
            window=self.window, db=self.db, main_container=self.main_container, queue_view=self.queue_view
        )

        # Library Manager
        self.library_handler = PlayerLibraryManager(
            window=self.window,
            db=self.db,
            library_manager=self.library_manager,
            favorites_manager=self.favorites_manager,
            library_view=self.library_view,
            queue_view=self.queue_view,
            status_bar=self.status_bar,
            now_playing_view=self.now_playing_view,
            refresh_colors_callback=lambda: self.ui_manager.refresh_colors(self.player_core),
        )
        # Share the item filepath map
        self.library_handler._item_filepath_map = self._item_filepath_map

        # Queue Handler (progress_bar will be set later)
        self.queue_handler = PlayerQueueHandler(
            queue_manager=self.queue_manager,
            player_core=self.player_core,
            queue_view=self.queue_view,
            now_playing_view=self.now_playing_view,
            progress_bar=None,  # Will be set after ProgressBar creation
            favorites_manager=self.favorites_manager,
            refresh_colors_callback=lambda: self.ui_manager.refresh_colors(self.player_core),
            item_filepath_map=self._item_filepath_map,
        )
        # Share the active view tracking
        self.queue_handler.active_view = self.active_view

        # Connect queue handler and active view to player_core for media key queue population
        self.player_core.queue_handler = self.queue_handler
        self.player_core.active_view = self.active_view

        # Progress Controller
        self.progress_controller = PlayerProgressController(
            window=self.window,
            db=self.db,
            player_core=self.player_core,
            progress_bar=None,  # Will be set after ProgressBar creation
            queue_view=self.queue_view,
            load_recently_played_callback=lambda: self.library_handler.load_recently_played(),
        )

        # Event Handlers
        self.event_handlers = PlayerEventHandlers(
            window=self.window,
            db=self.db,
            player_core=self.player_core,
            library_view=self.library_view,
            queue_view=self.queue_view,
            now_playing_view=self.now_playing_view,
            library_manager=self.library_manager,
            queue_manager=self.queue_manager,
            favorites_manager=self.favorites_manager,
            progress_bar=None,  # Will be set after ProgressBar creation
            status_bar=self.status_bar,
            load_library_callback=lambda: self.library_handler.load_library(),
            load_liked_songs_callback=lambda: self.library_handler.load_liked_songs(),
            load_recently_played_callback=lambda: self.library_handler.load_recently_played(),
            refresh_colors_callback=lambda: self.ui_manager.refresh_colors(self.player_core),
            _item_filepath_map=self._item_filepath_map,
            library_handler=self.library_handler,
        )
        # Share the active view tracking
        self.event_handlers.active_view = self.active_view

    def setup_api_server(self):
        """Initialize and start the API server if enabled."""
        from api import APIServer
        from config import API_SERVER_ENABLED, API_SERVER_PORT
        from eliot import log_message

        if not API_SERVER_ENABLED:
            log_message(message_type="api_server_disabled", message="API server is disabled in configuration")
            return

        try:
            # Create and start the API server
            self.api_server = APIServer(self, port=API_SERVER_PORT)
            result = self.api_server.start()

            if result['status'] == 'success':
                log_message(
                    message_type="api_server_initialized", port=API_SERVER_PORT, message="API server successfully started"
                )
            else:
                log_message(
                    message_type="api_server_failed",
                    error=result.get('message', 'Unknown error'),
                    message="Failed to start API server",
                )
                self.api_server = None

        except Exception as e:
            log_message(message_type="api_server_exception", error=str(e), message="Exception during API server initialization")
            self.api_server = None

    def setup_views(self):
        """Setup library and queue views with their callbacks."""
        from core.now_playing import NowPlayingView

        # Setup library view
        self.library_view = LibraryView(
            self.left_panel,
            {
                'on_section_select': self.on_section_select,
                'get_database': lambda: self.db,
                'load_custom_playlist': self.load_custom_playlist,
                'on_playlist_deleted': self.on_playlist_deleted,
            },
        )

        # Setup queue view for library browsing (search bar is now at window level)
        self.queue_view = QueueView(
            self.right_panel,
            {
                'play_selected': self.play_selected,
                'handle_delete': self.handle_delete,
                'on_song_select': self.on_song_select,
                'handle_drop': self.handle_drop,
                'save_column_widths': self.save_column_widths,
                'insert_after_current': self.insert_tracks_after_current,
                'add_to_queue_end': self.add_tracks_to_queue,
                'on_remove_from_library': self.remove_tracks_from_library,
                'stop_after_current': self.toggle_stop_after_current,
                'edit_metadata': self.edit_track_metadata,
                'get_playlists': self.get_playlists,
                'add_to_playlist': self.add_to_playlist,
                'remove_from_playlist': self.remove_from_playlist,
            },
        )

        # Setup Now Playing view for queue visualization (initially hidden)
        # Note: player_core is initialized later, so we use default loop_enabled=True
        self.now_playing_view = NowPlayingView(
            self.right_panel,
            callbacks={
                'on_queue_empty': self.on_queue_empty,
                'on_remove_from_library': self.remove_track_from_library,
                'on_play_track': self.play_track_at_index,
                'get_playlists': self.get_playlists,
                'add_track_to_playlist': self.add_track_to_playlist,
            },
            queue_manager=self.queue_manager,
            loop_enabled=True,  # Default to True; will be updated after player_core init
            lyrics_manager=self.lyrics_manager,  # Pass lyrics manager for lyrics fetching
        )

    def setup_file_watcher(self):
        """Setup file watcher for hot-reloading during development."""
        if self.reload_enabled:
            observer = Observer()
            event_handler = ConfigFileHandler(self.window)
            observer.schedule(event_handler, path='config.py', recursive=False)
            observer.start()
            self.observer = observer  # Store reference to prevent garbage collection

    def play_pause(self):
        """Toggle play/pause state."""
        self.player_core.play_pause()

    def on_window_state_change(self, is_maximized):
        """Handle window state changes (maximize/unmaximize) to adjust column widths."""
        if hasattr(self, 'queue_view'):
            self.queue_view.on_window_state_change(is_maximized)

    def on_window_close(self):
        """Handle window close event - save final UI state and clean up."""
        # Delegate to window manager
        api_server = getattr(self, 'api_server', None)
        self.window_manager.on_window_close(api_server)

    # Delegation methods to UI Manager
    def load_ui_preferences(self):
        """Load and apply saved UI preferences."""
        self.ui_manager.load_ui_preferences()

    def show_library_view(self):
        """Switch to library view (Treeview)."""
        self.ui_manager.show_library_view()
        self.active_view = self.ui_manager.active_view

    def show_now_playing_view(self):
        """Switch to Now Playing view (custom widgets)."""
        self.ui_manager.show_now_playing_view()
        self.active_view = self.ui_manager.active_view

    def on_section_select(self, event):
        """Handle library section selection."""
        self.ui_manager.on_section_select(
            event,
            self.library_handler.load_library,
            self.library_handler.load_liked_songs,
            self.library_handler.load_top_25_most_played,
            self.library_handler.load_recently_added,
            self.library_handler.load_recently_played,
        )

    def refresh_colors(self):
        """Update the background colors of all items in the queue view."""
        self.ui_manager.refresh_colors(self.player_core)

    # Delegation methods to Window Manager
    def save_column_widths(self, widths):
        """Save queue column widths for the current view."""
        self.window_manager.save_column_widths(widths)

    def save_window_size(self, width, height):
        """Save window size to database."""
        self.window_manager.save_window_size(width, height)

    def save_window_position(self):
        """Save window position to database."""
        self.window_manager.save_window_position()

    def load_window_position(self):
        """Load and apply saved window position."""
        self.window_manager.load_window_position()

    # Delegation methods to Library Manager
    def load_library(self):
        """Load and display library items."""
        self.library_handler.load_library()

    def load_liked_songs(self):
        """Load and display liked songs."""
        self.library_handler.load_liked_songs()

    def load_top_25_most_played(self):
        """Load and display top 25 most played tracks."""
        self.library_handler.load_top_25_most_played()

    def load_recently_added(self):
        """Load and display recently added tracks (last 14 days)."""
        self.library_handler.load_recently_added()

    def load_recently_played(self):
        """Load and display recently played tracks."""
        self.library_handler.load_recently_played()

    def load_custom_playlist(self, playlist_id: int):
        """Load a custom user-created playlist.

        Args:
            playlist_id: Database ID of the playlist to load
        """
        self.library_handler.load_custom_playlist(playlist_id)

    def on_playlist_deleted(self, playlist_id: int):
        """Handle deletion of a custom playlist.

        Args:
            playlist_id: Database ID of the deleted playlist
        """
        # Check if the deleted playlist is currently active
        current_view = self.queue_view.current_view
        if current_view == f"playlist:{playlist_id}":
            # Switch to Music view
            self.load_library()

    def get_playlists(self) -> list[tuple[int, str]]:
        """Get list of all custom playlists.

        Returns:
            List of (playlist_id, name) tuples
        """
        return self.db.list_playlists()

    def add_to_playlist(self, playlist_id: int, item_ids: list[str]):
        """Add selected tracks to a playlist.

        Args:
            playlist_id: Database ID of the playlist
            item_ids: List of tree item IDs (need to resolve to track IDs)
        """
        from tkinter import messagebox

        # Get track IDs from item IDs
        track_ids = []
        for item_id in item_ids:
            # Get filepath from the item mapping
            filepath = self.library_handler._item_filepath_map.get(item_id)
            if filepath:
                # Resolve filepath to track_id
                track_id = self.db.get_track_id_by_filepath(filepath)
                if track_id:
                    track_ids.append(track_id)

        if not track_ids:
            messagebox.showwarning("No Tracks", "No valid tracks selected.")
            return

        # Add tracks to playlist
        try:
            added_count = self.db.add_tracks_to_playlist(playlist_id, track_ids)
            playlist_name = self.db.get_playlist_name(playlist_id)

            if added_count > 0:
                messagebox.showinfo(
                    "Added to Playlist",
                    f"Added {added_count} track(s) to '{playlist_name}'."
                )
            else:
                messagebox.showinfo(
                    "Already in Playlist",
                    f"All selected tracks are already in '{playlist_name}'."
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add tracks to playlist: {e}")

    def add_track_to_playlist(self, playlist_id: int, filepath: str):
        """Add a single track to a playlist (from Now Playing view).

        Args:
            playlist_id: Database ID of the playlist
            filepath: File path of the track to add
        """
        from tkinter import messagebox

        # Resolve filepath to track_id
        track_id = self.db.get_track_id_by_filepath(filepath)
        if not track_id:
            messagebox.showwarning("Track Not Found", "Could not find track in library.")
            return

        # Add track to playlist
        try:
            added_count = self.db.add_tracks_to_playlist(playlist_id, [track_id])
            playlist_name = self.db.get_playlist_name(playlist_id)

            if added_count > 0:
                messagebox.showinfo(
                    "Added to Playlist",
                    f"Added track to '{playlist_name}'."
                )
            else:
                messagebox.showinfo(
                    "Already in Playlist",
                    f"Track is already in '{playlist_name}'."
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add track to playlist: {e}")

    def remove_from_playlist(self, item_ids: list[str]):
        """Remove selected tracks from the current playlist.

        Args:
            item_ids: List of tree item IDs to remove from playlist
        """
        from tkinter import messagebox

        # Get current playlist_id from view
        current_view = self.queue_view.current_view
        if not current_view.startswith('playlist:'):
            messagebox.showwarning("Not a Playlist", "This operation is only available in playlist views.")
            return

        try:
            playlist_id = int(current_view.split(':')[1])
        except (IndexError, ValueError):
            messagebox.showerror("Error", "Invalid playlist view.")
            return

        # Get track IDs from item IDs using the track_id map
        track_ids = []
        for item_id in item_ids:
            track_id = self.library_handler._item_track_id_map.get(item_id)
            if track_id:
                track_ids.append(track_id)

        if not track_ids:
            messagebox.showwarning("No Tracks", "No valid tracks selected.")
            return

        # Remove tracks from playlist
        try:
            self.db.remove_tracks_from_playlist(playlist_id, track_ids)
            playlist_name = self.db.get_playlist_name(playlist_id)

            # Remove items from UI
            for item_id in item_ids:
                self.queue_view.queue.delete(item_id)

            # Refresh colors
            self.refresh_colors()

            messagebox.showinfo(
                "Removed from Playlist",
                f"Removed {len(track_ids)} track(s) from '{playlist_name}'."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove tracks from playlist: {e}")

    def add_files_to_library(self):
        """Open file dialog and add selected files to library."""
        self.library_handler.add_files_to_library()

    def edit_track_metadata(self, item_id: str):
        """Open metadata editor for track(s)."""
        self.library_handler.edit_track_metadata(item_id)

    def remove_tracks_from_library(self, item_ids: list[str]):
        """Remove selected tracks from library."""
        self.library_handler.remove_tracks_from_library(item_ids)

    def remove_track_from_library(self, filepath: str):
        """Remove a single track from library (called from Now Playing view)."""
        self.library_handler.remove_track_from_library(filepath)

    # Delegation methods to Queue Handler
    def insert_tracks_after_current(self, item_ids: list[str]):
        """Insert selected tracks after currently playing track."""
        self.queue_handler.insert_tracks_after_current(item_ids)

    def add_tracks_to_queue(self, item_ids: list[str]):
        """Append selected tracks to end of queue."""
        self.queue_handler.add_tracks_to_queue(item_ids)

    def on_queue_empty(self):
        """Handle queue becoming empty."""
        self.queue_handler.on_queue_empty()

    def play_track_at_index(self, index: int):
        """Play track at specific index in queue (called from Now Playing view)."""
        self.queue_handler.play_track_at_index(index)

    def play_selected(self, event=None):
        """Play the selected track and populate queue from current view."""
        return self.queue_handler.play_selected(event)

    # Delegation methods to Progress Controller
    def set_play_count_updated(self, value: bool):
        """Set the play count updated flag."""
        self.progress_controller.set_play_count_updated(value)

    def update_progress(self):
        """Update progress bar position and time display."""
        self.progress_controller.update_progress()

    def start_drag(self, event):
        """Start dragging the progress circle."""
        self.progress_controller.start_drag(event)

    def drag(self, event):
        """Handle progress circle drag."""
        self.progress_controller.drag(event)

    def end_drag(self, event):
        """End dragging the progress circle and seek to the position."""
        self.progress_controller.end_drag(event)

    def click_progress(self, event):
        """Handle click on progress bar."""
        self.progress_controller.click_progress(event)

    def on_resize(self, event):
        """Handle window resize."""
        self.progress_controller.on_resize(event)

    def volume_change(self, volume):
        """Handle volume slider changes."""
        self.progress_controller.volume_change(volume)

    # Delegation methods to Event Handlers
    def handle_drop(self, event):
        """Handle drag and drop of files."""
        self.event_handlers.handle_drop(event)

    def handle_delete(self, event):
        """Handle delete key press - deletes from library or queue based on current view."""
        return self.event_handlers.handle_delete(event)

    def on_song_select(self, event):
        """Handle song selection in queue view."""
        self.event_handlers.on_song_select(event)

    def toggle_favorite(self):
        """Toggle favorite status for currently playing track."""
        self.event_handlers.toggle_favorite()

    def on_favorites_changed(self):
        """Callback when favorites list changes - refresh view if showing liked songs."""
        self.event_handlers.on_favorites_changed()

    def on_track_change(self):
        """Callback when current track changes - always refresh Now Playing view."""
        self.event_handlers.on_track_change()

    def perform_search(self, search_text):
        """Handle search functionality."""
        self.event_handlers.perform_search(search_text)

    def clear_search(self):
        """Clear search and reload current view."""
        self.event_handlers.clear_search()

    def toggle_stop_after_current(self):
        """Toggle stop-after-current flag."""
        self.event_handlers.toggle_stop_after_current()

    def __del__(self):
        """Cleanup when player instance is destroyed."""
        # Stop file watcher observer if it exists
        if hasattr(self, 'observer') and self.observer:
            self.observer.stop()
            self.observer.join()
