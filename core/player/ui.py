"""UI management for the music player - handles view switching and UI preferences."""

import os
import tkinter as tk
from config import THEME_CONFIG
from contextlib import suppress
from core.logging import log_player_action, player_logger
from eliot import start_action


class PlayerUIManager:
    """Manages UI state, view switching, and UI preferences."""

    def __init__(self, window, db, library_view, queue_view, now_playing_view, queue_manager, main_container, left_panel):
        """Initialize the UI manager.

        Args:
            window: The main Tkinter window
            db: Database instance
            library_view: LibraryView instance
            queue_view: QueueView instance
            now_playing_view: NowPlayingView instance
            queue_manager: QueueManager instance
            main_container: Main PanedWindow container
            left_panel: Left panel Frame
        """
        self.window = window
        self.db = db
        self.library_view = library_view
        self.queue_view = queue_view
        self.now_playing_view = now_playing_view
        self.queue_manager = queue_manager
        self.main_container = main_container
        self.left_panel = left_panel
        self.active_view = 'library'
        self._item_filepath_map = {}

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
            except Exception:
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

    def show_library_view(self):
        """Switch to library view (Treeview)."""
        if self.active_view == 'library':
            return  # Already showing library view

        # Hide Now Playing view
        self.now_playing_view.pack_forget()

        # Show library view
        self.queue_view.queue_frame.pack(expand=True, fill=tk.BOTH)

        self.active_view = 'library'

    def show_now_playing_view(self):
        """Switch to Now Playing view (custom widgets)."""
        if self.active_view == 'now_playing':
            # Just refresh the view
            self.now_playing_view.refresh_from_queue()
            # Update tab underline position in case it wasn't positioned correctly
            self.now_playing_view._update_tab_styles()
            return

        # Hide library view
        self.queue_view.queue_frame.pack_forget()

        # Show Now Playing view
        self.now_playing_view.pack(expand=True, fill=tk.BOTH)

        # Refresh from queue
        self.now_playing_view.refresh_from_queue()

        # Update tab underline position now that geometry is calculated
        # Use after() to ensure pack() geometry has been processed
        self.now_playing_view.after(10, self.now_playing_view._update_tab_styles)

        self.active_view = 'now_playing'

    def on_section_select(self, event, load_library_callback, load_liked_songs_callback, load_top_25_callback, load_recently_added_callback, load_recently_played_callback):
        """Handle library section selection.

        Args:
            event: Tkinter event
            load_library_callback: Callback to load library
            load_liked_songs_callback: Callback to load liked songs
            load_top_25_callback: Callback to load top 25 most played
            load_recently_added_callback: Callback to load recently added
            load_recently_played_callback: Callback to load recently played
        """
        with start_action(player_logger, "section_switch"):
            selected_item = self.library_view.library_tree.selection()[0]
            tags = self.library_view.library_tree.item(selected_item)['tags']

            if not tags:
                log_player_action("section_switch_no_tags", trigger_source="gui", reason="no_tags_found")
                return

            new_section = tags[0]

            log_player_action(
                "section_switch",
                trigger_source="gui",
                new_section=new_section,
                description=f"Switching to {new_section} section",
            )

            # Switch to Now Playing view or library view
            if new_section == 'now_playing':
                self.show_now_playing_view()
                log_player_action(
                    "section_switch_complete",
                    trigger_source="gui",
                    section="now_playing",
                    view="custom_widgets",
                    queue_size=len(self.queue_manager.queue_items),
                    description=f"Switched to Now Playing view with {len(self.queue_manager.queue_items)} tracks",
                )
            else:
                # Switch to library view and load content
                self.show_library_view()

                # Get previous view state
                previous_children_count = len(self.queue_view.queue.get_children())

                # Clear current view
                for item in self.queue_view.queue.get_children():
                    self.queue_view.queue.delete(item)

                if new_section == 'music':
                    load_library_callback()
                    new_count = len(self.queue_view.queue.get_children())
                    log_player_action(
                        "section_switch_complete",
                        trigger_source="gui",
                        section="music",
                        loaded_items=new_count,
                        description=f"Loaded {new_count} library items",
                    )
                elif new_section == 'liked_songs':
                    load_liked_songs_callback()
                    new_count = len(self.queue_view.queue.get_children())
                    log_player_action(
                        "section_switch_complete",
                        trigger_source="gui",
                        section="liked_songs",
                        loaded_items=new_count,
                        description=f"Loaded {new_count} liked songs",
                    )
                elif new_section == 'top_played':
                    load_top_25_callback()
                    new_count = len(self.queue_view.queue.get_children())
                    log_player_action(
                        "section_switch_complete",
                        trigger_source="gui",
                        section="top_played",
                        loaded_items=new_count,
                        description=f"Loaded {new_count} top played tracks",
                    )
                elif new_section == 'recent_added':
                    load_recently_added_callback()
                    new_count = len(self.queue_view.queue.get_children())
                    log_player_action(
                        "section_switch_complete",
                        trigger_source="gui",
                        section="recent_added",
                        loaded_items=new_count,
                        description=f"Loaded {new_count} recently added tracks",
                    )
                elif new_section == 'recent_played':
                    load_recently_played_callback()
                    new_count = len(self.queue_view.queue.get_children())
                    log_player_action(
                        "section_switch_complete",
                        trigger_source="gui",
                        section="recent_played",
                        loaded_items=new_count,
                        description=f"Loaded {new_count} recently played tracks",
                    )

    def refresh_colors(self, player_core):
        """Update the background colors of all items in the queue view.

        Args:
            player_core: PlayerCore instance
        """
        # Get the currently playing filepath if available (even if paused)
        current_filepath = None
        if player_core:
            # Check if there's media loaded (works for both playing and paused)
            media = player_core.media_player.get_media()
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
        is_currently_playing = player_core and player_core.is_playing

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
                    with suppress(ValueError, TypeError):
                        track_for_matching = f"{int(track_for_matching):02d}"
                item_filepath = self.db.find_file_by_metadata_strict(title, artist, album, track_for_matching)

            # Check if this item is the currently playing track
            is_current = False
            if current_filepath and item_filepath and os.path.normpath(item_filepath) == os.path.normpath(current_filepath):
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
                self.queue_view.queue.item(item, tags=(row_tag,))
