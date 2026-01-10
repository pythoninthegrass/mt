import contextlib
import customtkinter as ctk
import tkinter as tk
import tkinter.font as tkfont
from config import (
    BUTTON_SYMBOLS,
    COLORS,
    PROGRESS_BAR,
    THEME_CONFIG,
)
from core.controls import PlayerCore
from core.progress import ProgressControl
from core.volume import VolumeControl
from tkinter import ttk
from utils.icons import load_icon


class QueueView:
    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks
        self.current_view = 'music'  # Default view
        self.setup_queue_view()
        self.setup_type_to_jump()

    def load_column_preferences(self, view: str = None):
        """Load saved column widths from database for a specific view."""
        if view is None:
            view = self.current_view
        try:
            from config import DB_NAME
            from core.db import DB_TABLES, MusicDatabase

            db = MusicDatabase(DB_NAME, DB_TABLES)
            saved_widths = db.get_queue_column_widths(view)
            db.close()
            return saved_widths
        except Exception:
            return None

    def setup_queue_view(self):
        # Create queue frame and treeview
        self.queue_frame = ttk.Frame(self.parent)
        self.queue_frame.pack(expand=True, fill=tk.BOTH)

        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(self.queue_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create treeview with columns
        self.queue = ttk.Treeview(
            self.queue_frame,
            columns=('track', 'title', 'artist', 'album', 'year'),
            show='headings',
            selectmode='extended',
            yscrollcommand=self.scrollbar.set,
            style='Treeview',  # Explicit style name
        )

        # Enable alternating row colors
        self.queue.tag_configure('evenrow', background=THEME_CONFIG['colors']['bg'])
        self.queue.tag_configure('oddrow', background=THEME_CONFIG['colors'].get('row_alt', '#242424'))

        # Configure columns
        self.queue.heading('track', text='#')
        self.queue.heading('title', text='Title')
        self.queue.heading('artist', text='Artist')
        self.queue.heading('album', text='Album')
        self.queue.heading('year', text='Year')

        # Set minimal default widths - will be overridden by saved preferences
        self.queue.column('track', width=50, anchor='center')
        self.queue.column('title', width=200, minwidth=100)
        self.queue.column('artist', width=150, minwidth=80)
        self.queue.column('album', width=150, minwidth=80)
        self.queue.column('year', width=80, minwidth=60, anchor='center')

        # Load and apply saved column preferences immediately
        saved_widths = self.load_column_preferences()
        if saved_widths:
            for col_name, width in saved_widths.items():
                with contextlib.suppress(Exception):
                    self.queue.column(col_name, width=width)

        self.queue.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.scrollbar.config(command=self.queue.yview)

        # Add bindings
        # Add column auto-resize on double-click separator (must be first to check before play_selected)
        self.queue.bind('<Double-Button-1>', self.auto_resize_column)
        self.queue.bind('<Double-Button-1>', self.callbacks['play_selected'], add='+')
        self.queue.bind('<Delete>', self.callbacks['handle_delete'])
        self.queue.bind('<BackSpace>', self.callbacks['handle_delete'])
        self.queue.bind('<<TreeviewSelect>>', self.callbacks['on_song_select'])
        # Add select all keyboard shortcuts
        self.queue.bind('<Command-a>', self.select_all)  # macOS
        self.queue.bind('<Control-a>', self.select_all)  # Windows/Linux

        # Add queue next keyboard shortcuts (Cmd-D / Ctrl-D)
        self.queue.bind('<Command-d>', lambda e: self.on_context_play_next())  # macOS
        self.queue.bind('<Control-d>', lambda e: self.on_context_play_next())  # Windows/Linux

        # Add stop after current keyboard shortcuts (Cmd-S / Ctrl-S)
        self.queue.bind('<Command-s>', lambda e: self.on_context_stop_after_current())  # macOS
        self.queue.bind('<Control-s>', lambda e: self.on_context_stop_after_current())  # Windows/Linux

        # Setup context menu
        self.setup_context_menu()

        # Setup column separator hover feedback
        self.setup_column_separator_hover()

        # Add column resize handling with periodic check
        self._last_column_widths = self.get_column_widths()
        self._column_check_timer = None
        # Don't start periodic check yet - will be started after preferences are loaded

        # Bind to Map event to apply saved preferences when widget becomes visible
        self.queue.bind('<Map>', self._on_treeview_mapped)

    def set_track_column_header(self, text: str):
        """Update the track column header text."""
        self.queue.heading('track', text=text)

    def setup_context_menu(self):
        """Setup right-click context menu for library views."""
        from config import THEME_CONFIG

        self.context_menu = tk.Menu(
            self.queue,
            tearoff=0,
            bg=THEME_CONFIG['colors']['bg'],
            fg=THEME_CONFIG['colors']['fg'],
            activebackground=THEME_CONFIG['colors']['primary'],
            activeforeground="#ffffff",
            selectcolor=THEME_CONFIG['colors']['primary'],
            borderwidth=1,
            relief="flat",
            activeborderwidth=0
        )

        # Add menu items
        self.context_menu.add_command(label="Play", command=self.on_context_play)
        self.context_menu.add_command(label="Play Next", command=self.on_context_play_next)
        self.context_menu.add_command(label="Add to Queue", command=self.on_context_add_to_queue)
        self.context_menu.add_command(label="Stop After Current", command=self.on_context_stop_after_current)
        self.context_menu.add_separator()

        # Create "Add to playlist" submenu
        self.add_to_playlist_menu = tk.Menu(
            self.context_menu,
            tearoff=0,
            bg=THEME_CONFIG['colors']['bg'],
            fg=THEME_CONFIG['colors']['fg'],
            activebackground=THEME_CONFIG['colors']['primary'],
            activeforeground="#ffffff",
            selectcolor=THEME_CONFIG['colors']['primary'],
            borderwidth=1,
            relief="flat",
            activeborderwidth=0
        )
        self.context_menu.add_cascade(label="Add to playlist", menu=self.add_to_playlist_menu)

        # Add "Remove from playlist" option (only shown in playlist views)
        self._remove_from_playlist_index = self.context_menu.index('end') + 1
        self.context_menu.add_command(label="Remove from playlist", command=self.on_context_remove_from_playlist)

        self.context_menu.add_separator()
        self.context_menu.add_command(label="Edit Tag", command=self.on_context_edit_metadata)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Remove from Library", command=self.on_context_remove_from_library)

        # Bind right-click events
        self.queue.bind('<Button-2>', self.show_context_menu)  # macOS/Linux right-click
        self.queue.bind('<Control-Button-1>', self.show_context_menu)  # macOS Ctrl+click

    def show_context_menu(self, event):
        """Show context menu at cursor position.

        Args:
            event: Mouse button event
        """
        # Select the item under cursor if not already selected
        item = self.queue.identify_row(event.y)
        if item and item not in self.queue.selection():
            self.queue.selection_set(item)

        # Show menu if there's a selection
        if self.queue.selection():
            # Refresh playlist submenu
            self._refresh_playlist_submenu()

            # Show/hide "Remove from playlist" option based on current view
            is_playlist_view = self.current_view.startswith('playlist:')
            if is_playlist_view:
                # Show "Remove from playlist" option in playlist views
                self.context_menu.entryconfigure(self._remove_from_playlist_index, state='normal')
            else:
                # Hide it in other views
                self.context_menu.entryconfigure(self._remove_from_playlist_index, state='disabled')

            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def _refresh_playlist_submenu(self):
        """Refresh the 'Add to playlist' submenu with current playlists."""
        # Clear existing items
        self.add_to_playlist_menu.delete(0, 'end')

        # Get playlists from database via callback
        if 'get_playlists' in self.callbacks:
            playlists = self.callbacks['get_playlists']()
            if playlists:
                for playlist_id, name in playlists:
                    self.add_to_playlist_menu.add_command(
                        label=name,
                        command=lambda pid=playlist_id: self.on_add_to_playlist(pid)
                    )
            else:
                # No playlists yet
                self.add_to_playlist_menu.add_command(
                    label="(No playlists)",
                    state='disabled'
                )
        else:
            self.add_to_playlist_menu.add_command(
                label="(Not available)",
                state='disabled'
            )

    def on_add_to_playlist(self, playlist_id: int):
        """Handle 'Add to playlist' action.

        Args:
            playlist_id: Database ID of the playlist to add tracks to
        """
        if 'add_to_playlist' in self.callbacks:
            tracks = self.get_selected_tracks()
            if tracks:
                self.callbacks['add_to_playlist'](playlist_id, tracks)

    def get_selected_tracks(self) -> list[str]:
        """Get filepaths of selected items.

        Returns:
            List of selected track filepaths
        """
        selection = self.queue.selection()
        tracks = []
        for item in selection:
            values = self.queue.item(item)['values']
            if values:
                # Filepath should be stored as last value or we need to look it up
                # For now, we'll need to get it from the view's data structure
                # This will be handled by the player when it passes the callback
                tracks.append(item)  # Return item IDs for now
        return tracks

    def on_context_play(self):
        """Handle 'Play' context menu action."""
        if 'play_selected' in self.callbacks:
            # Trigger the same action as double-click
            self.callbacks['play_selected'](None)

    def on_context_play_next(self):
        """Handle 'Play Next' context menu action."""
        if 'insert_after_current' in self.callbacks:
            tracks = self.get_selected_tracks()
            if tracks:
                self.callbacks['insert_after_current'](tracks)

    def on_context_add_to_queue(self):
        """Handle 'Add to Queue' context menu action."""
        if 'add_to_queue_end' in self.callbacks:
            tracks = self.get_selected_tracks()
            if tracks:
                self.callbacks['add_to_queue_end'](tracks)

    def on_context_remove_from_library(self):
        """Handle 'Remove from Library' context menu action."""
        if 'on_remove_from_library' in self.callbacks:
            tracks = self.get_selected_tracks()
            if tracks:
                self.callbacks['on_remove_from_library'](tracks)

    def on_context_stop_after_current(self):
        """Handle 'Stop After Current' context menu action."""
        if 'stop_after_current' in self.callbacks:
            self.callbacks['stop_after_current']()

    def on_context_edit_metadata(self):
        """Handle 'Edit Tag' context menu action."""
        if 'edit_metadata' in self.callbacks:
            tracks = self.get_selected_tracks()
            if tracks:
                self.callbacks['edit_metadata'](tracks[0])

    def on_context_remove_from_playlist(self):
        """Handle 'Remove from playlist' context menu action."""
        if 'remove_from_playlist' in self.callbacks:
            selected_items = self.queue.selection()
            if selected_items:
                self.callbacks['remove_from_playlist'](list(selected_items))

    def set_current_view(self, view: str):
        """Set the current view and load its column preferences."""
        self.current_view = view
        saved_widths = self.load_column_preferences(view)
        if saved_widths:
            for col_name, width in saved_widths.items():
                with contextlib.suppress(Exception):
                    self.queue.column(col_name, width=width)
            self._last_column_widths = self.get_column_widths()

    def _on_treeview_mapped(self, event=None):
        # Apply saved preferences if available
        if hasattr(self, '_pending_column_widths') and self._pending_column_widths:
            for col_name, width in self._pending_column_widths.items():
                with contextlib.suppress(Exception):
                    self.queue.column(col_name, width=width)
            self._last_column_widths = self.get_column_widths()
            self._pending_column_widths = None
            self._pending_column_widths = None

    def start_column_check(self):
        """Start the periodic column width checking."""
        self.schedule_column_check()

        # Setup drag and drop
        self.queue.drop_target_register('DND_Files')
        self.queue.dnd_bind('<<Drop>>', self.callbacks['handle_drop'])

    def select_all(self, event=None):
        """Select all items in the queue."""
        self.queue.selection_set(self.queue.get_children())
        return "break"  # Prevent default handling

    def setup_type_to_jump(self):
        """Setup type-to-jump functionality for quick navigation by artist name."""
        self._type_buffer = ""
        self._type_timer = None
        self._type_timeout = 1000  # 1.0 seconds between keypresses

        # Bind all alphanumeric keys for type-to-jump
        self.queue.bind('<KeyPress>', self.on_key_press_jump)  # Tcl variable might not exist

    def on_key_press_jump(self, event):
        """Handle keypress for type-to-jump navigation."""
        from core.logging import library_logger
        from eliot import start_action

        # Ignore modifier keys and special keys - let them use default behavior
        if event.keysym in (
            'Shift_L',
            'Shift_R',
            'Control_L',
            'Control_R',
            'Alt_L',
            'Alt_R',
            'Meta_L',
            'Meta_R',
            'Super_L',
            'Super_R',
            'Up',
            'Down',
            'Left',
            'Right',
            'Return',
            'Escape',
            'Tab',
            'BackSpace',
            'Delete',
            'Home',
            'End',
            'Page_Up',
            'Page_Down',
        ):
            return None  # Let default behavior handle these keys

        # Ignore if modifiers are pressed (Ctrl, Alt, Command)
        if event.state & 0x4:  # Control
            return None
        if event.state & 0x8:  # Alt
            return None
        if event.state & 0x10:  # Command (macOS)
            return None

        # Only handle single character input
        if len(event.char) != 1 or not event.char.isprintable():
            return "break"

        # Cancel previous timer
        if self._type_timer:
            self.queue.after_cancel(self._type_timer)

        # Add character to buffer
        self._type_buffer += event.char.lower()

        with start_action(library_logger, "type_to_jump"):
            # Find matching item
            self._jump_to_artist(self._type_buffer)

            # Reset buffer after timeout
            self._type_timer = self.queue.after(self._type_timeout, self._reset_type_buffer)

        return "break"  # Prevent default handling

    @staticmethod
    def _strip_artist_prefix(artist: str) -> str:
        """Strip common prefixes from artist name for matching.

        Removes prefixes like 'The', 'A', 'Le', 'La' for type-to-jump matching
        while keeping the original display name unchanged.

        Special handling:
        - "La's" (with apostrophe) is NOT treated as a prefix (e.g., "The La's")
        - Only "La " (with space after) is removed

        Args:
            artist: The artist name to process (should be lowercase for matching)

        Returns:
            The artist name with common prefixes removed
        """
        # Define common prefixes to ignore (already lowercase since we match on lowercase)
        # Note: Must have space after to avoid matching "La's"
        prefixes = ['the ', 'a ', 'le ', 'la ']

        # Try each prefix
        for prefix in prefixes:
            if artist.startswith(prefix):
                return artist[len(prefix) :]

        return artist

    def _jump_to_artist(self, search_text: str):
        """Jump to first artist matching the typed text."""
        from core.logging import log_player_action

        if not search_text:
            return

        # Get all items in the queue/library view
        items = self.queue.get_children()
        if not items:
            return

        # Search for matching artist
        for item_id in items:
            item_values = self.queue.item(item_id)['values']
            if len(item_values) < 3:  # Need at least track, title, artist
                continue

            artist = str(item_values[2]).lower()  # Artist is column index 2

            # Strip common prefixes for matching (e.g., "the beatles" -> "beatles")
            artist_for_matching = self._strip_artist_prefix(artist)

            if artist_for_matching.startswith(search_text):
                # Select and scroll to the item
                self.queue.selection_set(item_id)
                self.queue.see(item_id)
                self.queue.focus(item_id)

                log_player_action(
                    "type_to_jump",
                    trigger_source="keyboard",
                    search_text=search_text,
                    matched_artist=artist,
                    artist_for_matching=artist_for_matching,
                    prefix_stripped=artist != artist_for_matching,
                    buffer_length=len(search_text),
                    description=f"Jumped to artist '{artist}' via type-to-jump",
                )
                return

        # No match found
        log_player_action(
            "type_to_jump_no_match",
            trigger_source="keyboard",
            search_text=search_text,
            buffer_length=len(search_text),
            total_items=len(items),
            description=f"No artist found starting with '{search_text}'",
        )

    def _reset_type_buffer(self):
        """Reset the type buffer after timeout."""
        self._type_buffer = ""

    def get_column_widths(self):
        """Get current column widths."""
        widths = {}
        for col in ['track', 'title', 'artist', 'album', 'year']:
            with contextlib.suppress(Exception):
                widths[col] = self.queue.column(col, 'width')
        return widths

    def schedule_column_check(self):
        """Schedule periodic check for column width changes."""
        if self._column_check_timer:
            self.queue.after_cancel(self._column_check_timer)
        self._column_check_timer = self.queue.after(1000, self.check_column_changes)  # Check every second

    def check_column_changes(self):
        """Check if column widths have changed and save if needed."""
        from core.logging import controls_logger, log_player_action
        from eliot import start_action

        with start_action(controls_logger, "column_width_check"):
            current_widths = self.get_column_widths()
            # Check if any column width has changed
            if current_widths != self._last_column_widths:
                old_widths = self._last_column_widths.copy()
                self._last_column_widths = current_widths

                # Calculate changes for logging
                changed_columns = {}
                for col_name in current_widths:
                    if col_name in old_widths and current_widths[col_name] != old_widths[col_name]:
                        changed_columns[col_name] = {'old_width': old_widths[col_name], 'new_width': current_widths[col_name]}

                log_player_action(
                    "column_width_change",
                    trigger_source="user_resize",
                    old_widths=old_widths,
                    new_widths=current_widths,
                    changed_columns=changed_columns,
                    column_count=len(current_widths),
                    description=f"Column widths changed for {len(changed_columns)} columns",
                )

                # Save column widths if callback is available
                if 'save_column_widths' in self.callbacks:
                    self.callbacks['save_column_widths'](current_widths)
            # Schedule next check
            self.schedule_column_check()

    def on_column_resize(self, event=None):
        """Handle column resize events (fallback method)."""
        # This is kept for compatibility but the periodic check is the main method
        self.check_column_changes()

    def cleanup(self):
        """Clean up timers and resources."""
        if self._column_check_timer:
            self.queue.after_cancel(self._column_check_timer)
            self._column_check_timer = None

    def auto_resize_column(self, event):
        """Auto-resize column to fit content on double-click of separator."""
        region = self.queue.identify_region(event.x, event.y)
        if region != 'separator':
            return

        # Get the column to the left of the separator
        col_id = self.queue.identify_column(event.x)
        if not col_id:
            return

        # Convert column ID from '#N' format to actual column name
        try:
            col_index = int(col_id.replace('#', '')) - 1
            columns = self.queue['columns']
            if col_index < 0 or col_index >= len(columns):
                return
            col_name = columns[col_index]
        except (ValueError, IndexError):
            return

        # Calculate optimal width for this column
        optimal_width = self._calculate_optimal_column_width(col_name)
        if optimal_width:
            self.queue.column(col_name, width=optimal_width)
            # Save the new width
            self.on_column_resize(None)

        # Stop event propagation to prevent play_selected from being triggered
        return 'break'

    def _calculate_optimal_column_width(self, col_name):
        """Calculate optimal width for a column based on its content."""

        # Get the font used by the treeview
        style = ttk.Style()
        font_spec = style.lookup('Treeview', 'font')
        if not font_spec:
            font_spec = 'TkDefaultFont'

        # Handle both font tuples and named fonts
        if isinstance(font_spec, (tuple, list)):
            font = tkfont.Font(family=font_spec[0], size=font_spec[1] if len(font_spec) > 1 else 12)
        else:
            font = tkfont.nametofont(font_spec)

        # Get heading font
        heading_font_spec = style.lookup('Treeview.Heading', 'font')
        if not heading_font_spec:
            heading_font_spec = font_spec

        # Handle both font tuples and named fonts for heading
        if isinstance(heading_font_spec, (tuple, list)):
            heading_font = tkfont.Font(family=heading_font_spec[0], size=heading_font_spec[1] if len(heading_font_spec) > 1 else 12)
        else:
            heading_font = tkfont.nametofont(heading_font_spec)

        # Get column index
        columns = self.queue['columns']
        try:
            col_index = columns.index(col_name)
        except ValueError:
            return None

        # Measure heading text
        heading_text = self.queue.heading(col_name, 'text')
        max_width = heading_font.measure(heading_text) + 20  # Add padding

        # Measure all items in the column
        for item_id in self.queue.get_children():
            values = self.queue.item(item_id, 'values')
            if col_index < len(values):
                text = str(values[col_index])
                text_width = font.measure(text)
                max_width = max(max_width, text_width)

        # Add padding for content
        max_width += 30

        # Get current column width
        current_width = self.queue.column(col_name, 'width')

        # Set reasonable limits based on column type
        # Track, year and any 'added' columns: allow shrinking to fit content
        # Title, artist, album: only allow expanding, never shrink below current width
        if col_name == 'track':
            # Track number can shrink to fit
            max_width = min(max_width, 30)
            max_width = max(max_width, 15)
        elif col_name == 'year':
            # Year column can shrink to fit
            max_width = min(max_width, 100)
            max_width = max(max_width, 60)
        elif col_name in ('title', 'artist', 'album'):
            # Title, artist, album: only expand, never shrink below current
            max_width = min(max_width, 400)
            max_width = max(max_width, current_width)
        else:
            # Any other columns (like 'added' if it exists): can shrink to fit
            max_width = min(max_width, 200)
            max_width = max(max_width, 60)

        return max_width

    def setup_column_separator_hover(self):
        """Setup visual feedback for hovering over column separators."""
        def on_motion(event):
            region = self.queue.identify_region(event.x, event.y)
            if region == 'separator':
                # Tkinter automatically shows resize cursor, but we could add additional feedback
                pass
            return

        self.queue.bind('<Motion>', on_motion, add='+')

    def on_window_state_change(self, is_maximized):
        """Handle window maximize/unmaximize events to adjust column widths."""
        from core.logging import controls_logger, log_player_action
        from eliot import start_action

        with start_action(controls_logger, "column_width_state_change"):
            if is_maximized:
                # Save current (unmaximized) column widths before maximizing
                if not hasattr(self, '_unmaximized_column_widths'):
                    self._unmaximized_column_widths = {}

                self._unmaximized_column_widths = self.get_column_widths()

                log_player_action(
                    "column_widths_saved_for_maximize",
                    trigger_source="window_maximize",
                    saved_widths=self._unmaximized_column_widths,
                    description="Saved unmaximized column widths before applying dynamic widths",
                )

                # Apply dynamic widths immediately so they animate with window
                self._apply_maximized_column_widths()
            else:
                # Restore unmaximized column widths immediately
                if hasattr(self, '_unmaximized_column_widths') and self._unmaximized_column_widths:
                    for col_name, width in self._unmaximized_column_widths.items():
                        with contextlib.suppress(Exception):
                            self.queue.column(col_name, width=width)

                    log_player_action(
                        "column_widths_restored_from_maximize",
                        trigger_source="window_unmaximize",
                        restored_widths=self._unmaximized_column_widths,
                        description="Restored unmaximized column widths",
                    )

                    # Update last known widths to prevent immediate save
                    self._last_column_widths = self.get_column_widths()

    def _check_and_apply_maximized_widths(self):
        """Check if window has actually resized before applying maximized widths."""
        if not hasattr(self, '_pending_maximize') or not self._pending_maximize:
            return

        # Force update to get current geometry
        self.queue.update()
        viewport_width = self.queue.winfo_width()

        # Get saved unmaximized width for comparison
        old_width = self._unmaximized_column_widths.get('title', 0)

        # Only apply if viewport has grown significantly (at least 200px wider)
        # This ensures window has actually maximized
        if viewport_width > 1000:  # Reasonable minimum for maximized state
            self._pending_maximize = False
            self._apply_maximized_column_widths()
        else:
            # Retry if window hasn't resized yet
            self.queue.after(100, self._check_and_apply_maximized_widths)

    def _apply_maximized_column_widths(self):
        """Apply dynamic column widths for maximized window mode."""
        from core.logging import log_player_action

        try:
            # Get screen width to calculate maximized viewport
            screen_width = self.queue.winfo_screenwidth()

            # Estimate viewport width for maximized window
            # Account for left panel (library view) and margins
            estimated_viewport_width = screen_width - 250  # Approximate left panel + margins

            # Calculate dynamic widths based on maximized size
            # Pin first column (#/track) to left edge with fixed width
            track_width = 50

            # Pin last column (year) to right edge with fixed width
            year_width = 80

            # Calculate remaining width for middle columns
            # Account for some padding/margins
            remaining_width = estimated_viewport_width - track_width - year_width - 40

            # Distribute remaining width: Title gets 33%, Artist and Album split the rest
            title_width = int(remaining_width * 0.33)
            artist_width = int(remaining_width * 0.33)
            album_width = remaining_width - title_width - artist_width

            # Apply the calculated widths
            new_widths = {
                'track': track_width,
                'title': title_width,
                'artist': artist_width,
                'album': album_width,
                'year': year_width,
            }

            for col_name, width in new_widths.items():
                with contextlib.suppress(Exception):
                    self.queue.column(col_name, width=width)

            log_player_action(
                "column_widths_maximized",
                trigger_source="window_maximize",
                screen_width=screen_width,
                estimated_viewport_width=estimated_viewport_width,
                new_widths=new_widths,
                description=f"Applied dynamic column widths for maximized mode (screen: {screen_width}px)",
            )

            # Update last known widths to prevent immediate save
            self._last_column_widths = self.get_column_widths()

        except Exception as e:
            log_player_action(
                "column_widths_maximized_error",
                trigger_source="window_maximize",
                error=str(e),
                description="Error applying maximized column widths",
            )
