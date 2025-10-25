import contextlib
import customtkinter as ctk
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk


class LibraryView:
    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks
        self.setup_library_view()

    def setup_library_view(self):
        # Create treeview for library/playlists
        self.library_tree = ttk.Treeview(self.parent, show='tree', selectmode='browse')
        self.library_tree.pack(expand=True, fill=tk.BOTH)

        # Library section
        library_id = self.library_tree.insert('', 'end', text='Library', open=True)
        music_item = self.library_tree.insert(library_id, 'end', text='Music', tags=('music',))
        self.library_tree.insert(library_id, 'end', text='Now Playing', tags=('now_playing',))

        # Playlists section
        playlists_id = self.library_tree.insert('', 'end', text='Playlists', open=True)
        self.library_tree.insert(playlists_id, 'end', text='Liked Songs', tags=('liked_songs',))
        self.library_tree.insert(playlists_id, 'end', text='Recently Added', tags=('recent_added',))
        self.library_tree.insert(playlists_id, 'end', text='Recently Played', tags=('recent_played',))
        self.library_tree.insert(playlists_id, 'end', text='Top 25 Most Played', tags=('top_played',))

        # Select Music by default
        self.library_tree.selection_set(music_item)
        self.library_tree.see(music_item)
        # Trigger the selection event to load the library
        self.library_tree.event_generate('<<TreeviewSelect>>')

        # Calculate optimal width based on content
        items = [
            'Library',
            'Music',
            'Now Playing',
            'Playlists',
            'Liked Songs',
            'Recently Added',
            'Recently Played',
            'Top 25 Most Played',
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

        # Configure the parent frame with minimum width
        self.parent.configure(width=self.min_width)
        self.parent.pack_propagate(False)

        # Store reference for resize handling
        self._parent_frame = self.parent

        # Bind selection event
        self.library_tree.bind('<<TreeviewSelect>>', self.callbacks['on_section_select'])




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
