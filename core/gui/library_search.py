import contextlib
import customtkinter as ctk
import sqlite3
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk


class LibraryView:
    """YouTube Music-inspired sidebar with navigation, divider, button, and playlists.

    Layout:
    ┌─────────────────────────┐
    │  Navigation Tree        │  ← Library / Music / Now Playing (fixed height)
    ├─────────────────────────┤
    │  ─────────────────────  │  ← Horizontal divider
    ├─────────────────────────┤
    │  [+ New playlist]       │  ← CTkButton (pill-shaped)
    ├─────────────────────────┤
    │  Playlists Tree         │  ← Dynamic + custom playlists (expandable)
    │  - Liked Songs          │
    │  - Recently Added       │
    │  - Recently Played      │
    │  - Top 25 Most Played   │
    └─────────────────────────┘
    """

    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks
        self._filler_items = []  # Track filler item IDs for playlists tree
        self._rename_entry = None  # Track active rename Entry widget
        self._rename_item = None  # Track item being renamed
        self._playlist_items = {}  # Map tree item IDs to playlist IDs
        self.setup_library_view()

    def setup_library_view(self):
        from config import THEME_CONFIG

        sidebar_bg = THEME_CONFIG['colors']['bg']  # #202020
        border_color = THEME_CONFIG['colors']['border']
        primary_color = THEME_CONFIG['colors']['primary']

        # Container frame with dark background
        self.container = tk.Frame(self.parent, bg=sidebar_bg)
        self.container.pack(expand=True, fill=tk.BOTH)

        # 1. Navigation tree (top section - Library, Music, Now Playing)
        self.nav_tree = ttk.Treeview(self.container, show='tree', selectmode='browse', height=3)
        self.nav_tree.tag_configure('sidebar_item', background=sidebar_bg)

        library_id = self.nav_tree.insert('', 'end', text='Library', open=True, tags=('sidebar_item',))
        music_item = self.nav_tree.insert(library_id, 'end', text='Music', tags=('music', 'sidebar_item'))
        self.nav_tree.insert(library_id, 'end', text='Now Playing', tags=('now_playing', 'sidebar_item'))

        self.nav_tree.pack(fill=tk.X, padx=0, pady=(0, 120))  # Increased bottom padding for visual gap
        self.nav_tree.bind('<<TreeviewSelect>>', self._on_nav_select)

        # 2. Horizontal divider
        self.divider = ttk.Separator(self.container, orient='horizontal')
        self.divider.pack(fill=tk.X, padx=10, pady=10)

        # 3. "+ New playlist" button
        self.new_playlist_btn = ctk.CTkButton(
            self.container,
            text="+ New playlist",
            command=self._on_new_playlist,
            corner_radius=15,
            height=28,
            font=("SF Pro Display", 12),
            fg_color=border_color,
            hover_color=primary_color,
            text_color="#ffffff",
            border_width=1,
            border_color=border_color,
            bg_color=sidebar_bg,
        )
        self.new_playlist_btn.pack(fill=tk.X, padx=10, pady=(0, 10))

        # 4. Playlists tree (dynamic playlists only for now)
        self.playlists_tree = ttk.Treeview(self.container, show='tree', selectmode='browse')
        self.playlists_tree.tag_configure('sidebar_item', background=sidebar_bg)

        # Add dynamic playlists
        self.playlists_tree.insert('', 'end', text='Liked Songs', tags=('liked_songs', 'dynamic', 'sidebar_item'))
        self.playlists_tree.insert('', 'end', text='Recently Added', tags=('recently_added', 'dynamic', 'sidebar_item'))
        self.playlists_tree.insert('', 'end', text='Recently Played', tags=('recently_played', 'dynamic', 'sidebar_item'))
        self.playlists_tree.insert('', 'end', text='Top 25 Most Played', tags=('top_played', 'dynamic', 'sidebar_item'))

        # Load custom playlists from database
        self._load_custom_playlists()

        self.playlists_tree.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)
        self.playlists_tree.bind('<<TreeviewSelect>>', self._on_playlist_select)
        self.playlists_tree.bind('<Button-2>', self._show_playlist_context_menu)  # Right-click (macOS)
        self.playlists_tree.bind('<Button-3>', self._show_playlist_context_menu)  # Right-click (Linux/Windows)

        # Bind to Configure event to update filler items when widget is resized
        self.playlists_tree.bind('<Configure>', self._on_tree_configure)

        # Schedule initial filler update after widget is fully initialized
        self.parent.after(100, self._update_filler_items)

        # Select Music by default
        self.nav_tree.selection_set(music_item)
        self.nav_tree.see(music_item)

        # Calculate optimal width based on content
        self._calculate_min_width()

        # Configure the parent frame with minimum width
        self.parent.configure(width=self.min_width)
        self.parent.pack_propagate(False)

        # Store reference for resize handling
        self._parent_frame = self.parent

        # For backwards compatibility - expose library_tree
        # Will be swapped between nav_tree and playlists_tree in selection handlers
        self.library_tree = self.nav_tree

    def _calculate_min_width(self):
        """Calculate minimum width based on longest text content."""
        items = [
            'Library',
            'Music',
            'Now Playing',
            'Liked Songs',
            'Recently Added',
            'Recently Played',
            'Top 25 Most Played',
            '+ New playlist',
        ]

        style = ttk.Style()
        font_spec = style.lookup('Treeview', 'font')
        if not font_spec:
            font_spec = 'TkDefaultFont'

        # Handle both font tuples and named fonts
        if isinstance(font_spec, (tuple, list)):
            font = tkfont.Font(family=font_spec[0], size=font_spec[1] if len(font_spec) > 1 else 12)
        else:
            font = tkfont.nametofont(font_spec)

        text_width = max(font.measure(text) for text in items)
        indent_width = 10
        icon_width = 10
        max_indent_level = 2
        side_padding = 0

        total_width = text_width + (indent_width * max_indent_level) + icon_width + side_padding

        # Set minimum width (breakpoint) - this is the width the panel should maintain
        self.min_width = total_width + 40

    def _load_custom_playlists(self):
        """Load custom playlists from database and add to tree."""
        if 'get_database' not in self.callbacks:
            return

        db = self.callbacks['get_database']()
        playlists = db.list_playlists()

        for playlist_id, name in playlists:
            item_id = self.playlists_tree.insert('', 'end', text=name, tags=('custom', 'sidebar_item'))
            self._playlist_items[item_id] = playlist_id

    def _on_new_playlist(self):
        """Handle new playlist button click - create playlist and enter rename mode."""
        if 'get_database' not in self.callbacks:
            return

        try:
            db = self.callbacks['get_database']()

            # Generate unique name
            unique_name = db.generate_unique_name("New playlist")

            # Create playlist in database
            playlist_id = db.create_playlist(unique_name)

            # Insert into tree after dynamic playlists (before filler items)
            # Find position: after last non-filler item
            all_items = self.playlists_tree.get_children()
            insert_pos = 'end'
            for i, item in enumerate(all_items):
                if 'filler' in self.playlists_tree.item(item)['tags']:
                    insert_pos = i
                    break

            if insert_pos == 'end':
                item_id = self.playlists_tree.insert('', 'end', text=unique_name, tags=('custom', 'sidebar_item'))
            else:
                item_id = self.playlists_tree.insert('', insert_pos, text=unique_name, tags=('custom', 'sidebar_item'))

            self._playlist_items[item_id] = playlist_id

            # Update filler items
            self._update_filler_items()

            # Enter inline rename mode
            self._start_inline_rename(item_id, playlist_id, unique_name)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create playlist: {e}")

    def _start_inline_rename(self, item_id, playlist_id, current_name):
        """Start inline rename mode for a playlist item.

        Args:
            item_id: Tree item ID
            playlist_id: Database playlist ID
            current_name: Current playlist name
        """
        # Get item bbox for positioning
        try:
            bbox = self.playlists_tree.bbox(item_id)
            if not bbox:
                # Item not visible, scroll to it first
                self.playlists_tree.see(item_id)
                self.playlists_tree.update()
                bbox = self.playlists_tree.bbox(item_id)
                if not bbox:
                    return
        except tk.TclError:
            return

        x, y, width, height = bbox

        # Create Entry overlay
        self._rename_entry = tk.Entry(
            self.playlists_tree,
            font=('TkDefaultFont', 12),
            bg='#2B2B2B',
            fg='#FFFFFF',
            insertbackground='#FFFFFF',
            relief='solid',
            borderwidth=1,
        )
        self._rename_entry.place(x=x, y=y, width=width, height=height)
        self._rename_entry.insert(0, current_name)
        self._rename_entry.select_range(0, tk.END)
        self._rename_entry.focus_set()

        self._rename_item = (item_id, playlist_id, current_name)

        # Bind events
        self._rename_entry.bind('<Return>', self._commit_rename)
        self._rename_entry.bind('<Escape>', self._cancel_rename)
        self._rename_entry.bind('<FocusOut>', self._commit_rename)

    def _commit_rename(self, event=None):
        """Commit the inline rename."""
        if not self._rename_entry or not self._rename_item:
            return

        item_id, playlist_id, old_name = self._rename_item
        new_name = self._rename_entry.get().strip()

        # Validate name
        if not new_name:
            messagebox.showerror("Error", "Playlist name cannot be empty.")
            self._rename_entry.focus_set()
            return

        if new_name == old_name:
            # No change, just close
            self._close_rename_entry()
            return

        # Try to rename in database
        try:
            db = self.callbacks['get_database']()
            db.rename_playlist(playlist_id, new_name)

            # Update tree item text
            self.playlists_tree.item(item_id, text=new_name)

            # Close rename entry
            self._close_rename_entry()

        except sqlite3.IntegrityError:
            # Duplicate name
            messagebox.showerror("Error", f"A playlist named '{new_name}' already exists.")
            self._rename_entry.focus_set()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename playlist: {e}")
            self._close_rename_entry()

    def _cancel_rename(self, event=None):
        """Cancel the inline rename."""
        self._close_rename_entry()

    def _close_rename_entry(self):
        """Close and cleanup the rename Entry widget."""
        if self._rename_entry:
            self._rename_entry.destroy()
            self._rename_entry = None
        self._rename_item = None

    def _show_playlist_context_menu(self, event):
        """Show context menu for playlist items (rename/delete)."""
        # Identify which item was clicked
        item = self.playlists_tree.identify_row(event.y)
        if not item:
            return

        tags = self.playlists_tree.item(item)['tags']

        # Only show menu for custom playlists
        if 'custom' not in tags or 'filler' in tags:
            return

        playlist_id = self._playlist_items.get(item)
        if not playlist_id:
            return

        # Get current name
        current_name = self.playlists_tree.item(item)['text']

        # Create context menu
        menu = tk.Menu(self.playlists_tree, tearoff=0)
        menu.add_command(label="Rename", command=lambda: self._start_inline_rename(item, playlist_id, current_name))
        menu.add_command(label="Delete", command=lambda: self._delete_playlist(item, playlist_id, current_name))

        # Show menu
        menu.tk_popup(event.x_root, event.y_root)

    def _delete_playlist(self, item_id, playlist_id, name):
        """Delete a custom playlist.

        Args:
            item_id: Tree item ID
            playlist_id: Database playlist ID
            name: Playlist name
        """
        # Confirm deletion
        if not messagebox.askyesno(
            "Delete Playlist", f"Are you sure you want to delete the playlist '{name}'?\n\nThis action cannot be undone."
        ):
            return

        try:
            db = self.callbacks['get_database']()
            db.delete_playlist(playlist_id)

            # Remove from tree
            self.playlists_tree.delete(item_id)
            del self._playlist_items[item_id]

            # Update filler items
            self._update_filler_items()

            # If this playlist was active, switch to Music view
            if self.callbacks.get('on_playlist_deleted'):
                self.callbacks['on_playlist_deleted'](playlist_id)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete playlist: {e}")

    def _on_nav_select(self, event):
        """Handle navigation tree selection (Library, Music, Now Playing)."""
        selection = self.nav_tree.selection()
        if not selection:
            return

        item = selection[0]
        tags = self.nav_tree.item(item)['tags']

        # Ignore spacer items
        if 'spacer' in tags:
            # Deselect spacer and reselect previous valid item
            self.nav_tree.selection_remove(item)
            return

        # Clear playlist selection when nav item is selected
        with contextlib.suppress(Exception):
            self.playlists_tree.selection_remove(self.playlists_tree.selection())

        # Temporarily set library_tree to nav_tree so callback sees correct tree
        old_library_tree = self.library_tree
        self.library_tree = self.nav_tree
        try:
            self.callbacks['on_section_select'](event)
        finally:
            self.library_tree = old_library_tree

    def _on_playlist_select(self, event):
        """Handle playlist tree selection."""
        selection = self.playlists_tree.selection()
        if not selection:
            return

        item = selection[0]
        tags = self.playlists_tree.item(item)['tags']

        # Ignore filler items
        if 'filler' in tags:
            self.playlists_tree.selection_remove(item)
            return

        # Clear nav selection when playlist is selected
        with contextlib.suppress(Exception):
            self.nav_tree.selection_remove(self.nav_tree.selection())

        # Check if this is a custom playlist
        if 'custom' in tags:
            # Load custom playlist
            playlist_id = self._playlist_items.get(item)
            if playlist_id and 'load_custom_playlist' in self.callbacks:
                self.callbacks['load_custom_playlist'](playlist_id)
            return

        # Dynamic playlist - use existing routing
        # Temporarily set library_tree to playlists_tree so callback sees correct items
        old_library_tree = self.library_tree
        self.library_tree = self.playlists_tree
        try:
            self.callbacks['on_section_select'](event)
        finally:
            self.library_tree = old_library_tree

    def check_playlist_drop(self, widget, x_root, y_root):
        """Check if a drop occurred on a custom playlist and return playlist ID.

        Args:
            widget: Widget under cursor
            x_root: Root X coordinate
            y_root: Root Y coordinate

        Returns:
            playlist_id (int) if dropped on a custom playlist, None otherwise
        """
        # Check if widget is the playlists tree or one of its children
        current = widget
        while current:
            if current == self.playlists_tree:
                # Convert root coordinates to widget-local coordinates
                x_local = self.playlists_tree.winfo_pointerx() - self.playlists_tree.winfo_rootx()
                y_local = self.playlists_tree.winfo_pointery() - self.playlists_tree.winfo_rooty()

                # Identify item under cursor
                item = self.playlists_tree.identify_row(y_local)
                if item:
                    tags = self.playlists_tree.item(item)['tags']
                    # Check if this is a custom playlist (not dynamic, not filler)
                    if 'custom' in tags and 'filler' not in tags:
                        playlist_id = self._playlist_items.get(item)
                        if playlist_id:
                            return playlist_id
                return None
            try:
                current = current.master
            except AttributeError:
                break
        return None

    def highlight_playlist_at(self, x_root: int, y_root: int) -> bool:
        """Highlight playlist row during drag-to-playlist operation."""
        from config import THEME_CONFIG

        self.clear_playlist_highlight()

        try:
            widget_x = self.playlists_tree.winfo_rootx()
            widget_y = self.playlists_tree.winfo_rooty()
            widget_width = self.playlists_tree.winfo_width()
            widget_height = self.playlists_tree.winfo_height()

            if not (widget_x <= x_root <= widget_x + widget_width and widget_y <= y_root <= widget_y + widget_height):
                return False

            y_local = y_root - widget_y
            item = self.playlists_tree.identify_row(y_local)
            if not item:
                return False

            tags = self.playlists_tree.item(item)['tags']

            if 'custom' in tags and 'filler' not in tags:
                primary_color = THEME_CONFIG['colors']['primary']
                self.playlists_tree.tag_configure('drop_highlight', background=primary_color)

                self._highlighted_item = item
                current_tags = list(tags)
                if 'drop_highlight' not in current_tags:
                    current_tags.append('drop_highlight')
                    self.playlists_tree.item(item, tags=current_tags)
                return True

        except tk.TclError:
            pass

        return False

    def clear_playlist_highlight(self):
        """Clear playlist highlight from drag operation."""
        if hasattr(self, '_highlighted_item') and self._highlighted_item:
            try:
                tags = list(self.playlists_tree.item(self._highlighted_item)['tags'])
                if 'drop_highlight' in tags:
                    tags.remove('drop_highlight')
                    self.playlists_tree.item(self._highlighted_item, tags=tags)
            except tk.TclError:
                pass
            self._highlighted_item = None

    def _on_tree_configure(self, event=None):
        """Handle tree resize events to update filler items."""
        # Cancel any pending update
        if hasattr(self, '_update_timer'):
            self.parent.after_cancel(self._update_timer)
        # Schedule update after a short delay to avoid too many updates during resize
        self._update_timer = self.parent.after(100, self._update_filler_items)

    def _update_filler_items(self):
        """Fill empty space below visible items with dummy items to control background color.

        This workaround addresses macOS aqua theme limitation where Treeview fieldbackground
        cannot be styled. By filling all visible space with tagged items, we ensure the
        #202020 background color is displayed instead of the default #323232.
        """
        from config import THEME_CONFIG

        # Get tree height in pixels
        try:
            tree_height = self.playlists_tree.winfo_height()
        except tk.TclError:
            # Widget not yet realized, skip update
            return

        if tree_height <= 1:
            # Widget not fully initialized yet
            return

        # Estimate item height (typical row height is ~20px)
        # We'll use a conservative estimate
        item_height = 20

        # Calculate how many rows would fill the visible area
        visible_rows = (tree_height // item_height) + 2  # +2 for safety margin

        # Count real items (non-filler items currently in the tree)
        all_items = self.playlists_tree.get_children()
        real_item_count = sum(1 for item in all_items if 'filler' not in self.playlists_tree.item(item)['tags'])

        # Calculate needed filler items
        # We want enough fillers to fill the visible space
        needed_fillers = max(0, visible_rows - real_item_count)

        # Remove existing filler items
        for filler_id in self._filler_items:
            with contextlib.suppress(tk.TclError):
                self.playlists_tree.delete(filler_id)
        self._filler_items.clear()

        # Add new filler items at the end with the correct background color
        sidebar_bg = THEME_CONFIG['colors']['bg']
        for _ in range(needed_fillers):
            # Insert empty items with sidebar_item tag for correct background
            filler_id = self.playlists_tree.insert('', 'end', text='', tags=('filler', 'sidebar_item'))
            self._filler_items.append(filler_id)

    def _is_filler_item(self, item_id):
        """Check if an item is a filler item."""
        if not item_id:
            return False
        tags = self.playlists_tree.item(item_id).get('tags', [])
        return 'filler' in tags


class SearchBar:
    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks
        self.search_var = tk.StringVar()
        self.search_timer = None
        self.setup_search_bar()

    def setup_search_bar(self):
        # Create search frame container - continuous black bar across full width
        self.search_frame = ctk.CTkFrame(
            self.parent,
            height=40,
            corner_radius=0,
            fg_color="#000000",  # Pure black like MusicBee
            border_width=0,
        )
        self.search_frame.pack(fill=tk.X, padx=0, pady=0)
        self.search_frame.pack_propagate(False)

        # Add stoplight buttons on the left side (only on macOS)
        import sys

        if sys.platform == 'darwin':
            from core.stoplight import StoplightButtons

            # Get the window reference from the parent
            window = self.parent
            # Get the window state change callback if provided
            on_state_change = self.callbacks.get('on_window_state_change', None)
            self.stoplight_buttons = StoplightButtons(window, self.search_frame, integrated=True, on_state_change=on_state_change)

        # Create inner frame right-justified but expanded left to Album column
        self.inner_frame = ctk.CTkFrame(self.search_frame, fg_color="transparent")
        self.inner_frame.pack(side=tk.RIGHT, padx=10, pady=5)

        # Search icon label - using Unicode magnifying glass instead of emoji
        self.search_icon = ctk.CTkLabel(
            self.inner_frame,
            text="\u2315",  # Unicode magnifying glass (U+2315)
            width=20,
            font=("SF Pro Display", 30),
            text_color="#CCCCCC",  # Light gray for visibility on black
        )
        self.search_icon.pack(side=tk.LEFT, padx=(0, 5))

        # Search entry widget with dark styling to match black bar
        self.search_entry = ctk.CTkEntry(
            self.inner_frame,
            placeholder_text="Search library...",
            width=400,  # Expanded width so magnifying glass aligns with Album column
            height=28,
            corner_radius=6,
            font=("SF Pro Display", 12),
            textvariable=self.search_var,
            fg_color="#2B2B2B",  # Dark gray background
            border_color="#404040",  # Subtle border
            placeholder_text_color="#999999",  # Gray placeholder
        )
        self.search_entry.pack(side=tk.LEFT)

        # Bind events for real-time search
        self.search_var.trace('w', self.on_search_change)
        self.search_entry.bind('<Return>', self.on_search_submit)
        self.search_entry.bind('<Escape>', self.clear_search)
        self.search_entry.bind('<Control-f>', lambda e: self.search_entry.focus_set())

        # Make the search frame draggable for window movement on macOS
        import sys

        if sys.platform == 'darwin':
            self.make_search_frame_draggable()

    def on_search_change(self, *args):
        """Handle search text changes with debouncing."""
        if self.search_timer:
            self.parent.after_cancel(self.search_timer)

        # Debounce search by 300ms
        self.search_timer = self.parent.after(300, self.perform_search)

    def perform_search(self):
        """Execute the actual search."""
        search_text = self.search_var.get().strip()
        if hasattr(self.callbacks, 'search') or 'search' in self.callbacks:
            self.callbacks['search'](search_text)

    def on_search_submit(self, event):
        """Handle Enter key press."""
        self.perform_search()

    def clear_search(self, event=None):
        """Clear search and reset filters."""
        self.search_var.set("")
        if hasattr(self.callbacks, 'clear_search') or 'clear_search' in self.callbacks:
            self.callbacks['clear_search']()

    def get_search_text(self):
        """Get current search text."""
        return self.search_var.get().strip()

    def set_focus(self):
        """Set focus to search entry."""
        self.search_entry.focus_set()

    def make_search_frame_draggable(self):
        """Make the search frame draggable to move the window and double-clickable to maximize."""

        def start_drag(event):
            # Get the window from the parent hierarchy
            widget = event.widget
            while widget:
                if hasattr(widget, 'winfo_toplevel'):
                    window = widget.winfo_toplevel()
                    break
                widget = widget.master
            else:
                return

            # Store drag start positions
            self.drag_start_x = event.x_root
            self.drag_start_y = event.y_root
            self.window_start_x = window.winfo_x()
            self.window_start_y = window.winfo_y()
            self.dragging_window = window

        def drag_window(event):
            if hasattr(self, 'dragging_window') and self.dragging_window:
                # Calculate new window position
                delta_x = event.x_root - self.drag_start_x
                delta_y = event.y_root - self.drag_start_y
                new_x = self.window_start_x + delta_x
                new_y = self.window_start_y + delta_y
                self.dragging_window.geometry(f"+{new_x}+{new_y}")

        def stop_drag(event):
            # Clear drag state
            if hasattr(self, 'dragging_window'):
                self.dragging_window = None

        def double_click_maximize(event):
            # Get the stoplight buttons instance to trigger maximize
            if hasattr(self, 'stoplight_buttons') and self.stoplight_buttons:
                self.stoplight_buttons.toggle_maximize()

        # Bind drag events to the search frame and inner frame (but not the search entry)
        self.search_frame.bind("<Button-1>", start_drag)
        self.search_frame.bind("<B1-Motion>", drag_window)
        self.search_frame.bind("<ButtonRelease-1>", stop_drag)
        self.search_frame.bind("<Double-Button-1>", double_click_maximize)

        # Also bind to the icon so it's draggable and double-clickable
        self.search_icon.bind("<Button-1>", start_drag)
        self.search_icon.bind("<B1-Motion>", drag_window)
        self.search_icon.bind("<ButtonRelease-1>", stop_drag)
        self.search_icon.bind("<Double-Button-1>", double_click_maximize)
