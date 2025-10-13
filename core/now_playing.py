"""Now Playing view with custom widgets for queue visualization."""

import tkinter as tk
from core.widgets import QueueRowWidget, ScrollableFrame
from tkinter import ttk


class NowPlayingView(ttk.Frame):
    """Now Playing view showing the active queue with drag-and-drop reordering.

    Attributes:
        queue_manager: QueueManager instance for queue data
        callbacks: Dictionary of callback functions for actions
        row_widgets: List of QueueRowWidget instances
    """

    def __init__(self, parent, callbacks: dict, queue_manager):
        """Initialize the Now Playing view.

        Args:
            parent: Parent widget
            callbacks: Dict of callbacks:
                - on_queue_empty(): Called when queue becomes empty
                - on_remove_from_library(filepath): Remove track from library
                - on_play_track(index): Play track at index
            queue_manager: QueueManager instance
        """
        super().__init__(parent)
        self.queue_manager = queue_manager
        self.callbacks = callbacks
        self.row_widgets = []

        # Drag state
        self._drag_state = {
            'active': False,
            'widget': None,
            'start_y': 0,
            'original_index': -1,
            'target_index': -1,
            'ghost_widget': None,
        }

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI components."""
        # Scrollable container for queue rows
        self.scrollable = ScrollableFrame(self)
        self.scrollable.pack(fill=tk.BOTH, expand=True)

        # Empty state label (hidden by default)
        self.empty_label = tk.Label(
            self,
            text="Queue is empty\n\nDouble-click a track in Library to start playing",
            font=('Helvetica', 14),
            fg='#888888',
            bg='#202020',
            justify=tk.CENTER,
        )

        # Context menu
        self.setup_context_menu()

        # Initially show empty state
        self.show_empty_state()

    def setup_context_menu(self):
        """Setup right-click context menu for queue items."""
        self.context_menu = tk.Menu(self, tearoff=0)
        self._selected_row = None  # Track which row was right-clicked

        # Add menu items
        self.context_menu.add_command(label="Play Next", command=self.on_context_play_next)
        self.context_menu.add_command(label="Move to End", command=self.on_context_move_to_end)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Remove from Queue", command=self.on_context_remove_from_queue)
        self.context_menu.add_command(label="Remove from Library", command=self.on_context_remove_from_library)
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Save to Playlist",
            command=self.on_context_save_to_playlist,
            state='disabled',  # Stub for future feature
        )

    def refresh_from_queue(self):
        """Rebuild view from queue_manager data."""
        # Clear existing widgets
        for widget in self.row_widgets:
            widget.destroy()
        self.row_widgets.clear()

        # Get queue items (respects shuffle state)
        if self.queue_manager.shuffle_enabled:
            items = self.queue_manager.get_shuffled_queue_items()
        else:
            items = self.queue_manager.get_queue_items()

        current_index = self.queue_manager.current_index

        if not items:
            self.show_empty_state()
            return

        self.hide_empty_state()

        # In shuffle mode, don't rotate - show in shuffled order
        # In normal mode, rotate so current track is at top
        if self.queue_manager.shuffle_enabled:
            display_items = items
            # In shuffle, need to find which display position has the current track
            current_filepath = (
                self.queue_manager.queue_items[current_index] if current_index < len(self.queue_manager.queue_items) else None
            )
        else:
            # Rotate display so current track is at top
            display_items = items[current_index:] + items[:current_index]
            current_filepath = None

        # Create row widgets
        for display_i, (filepath, artist, title, album, track_num, date) in enumerate(display_items):
            # Determine if this is the current track
            if self.queue_manager.shuffle_enabled:
                is_current = filepath == current_filepath
            else:
                is_current = display_i == 0  # First item in rotated display is always current

            # Find actual index in original queue for operations
            actual_index = (
                self.queue_manager.queue_items.index(filepath) if filepath in self.queue_manager.queue_items else display_i
            )

            row = QueueRowWidget(
                self.scrollable.scrollable_frame,
                title=title,
                artist=artist,
                filepath=filepath,
                index=actual_index,
                is_current=is_current,
                callbacks={
                    'on_drag_start': self.on_drag_start,
                    'on_drag_motion': self.on_drag_motion,
                    'on_drag_release': self.on_drag_release,
                    'on_context_menu': self.show_context_menu_for_row,
                    'on_double_click': self.on_row_double_click,
                },
            )
            row.pack(fill=tk.X, pady=1)
            self.row_widgets.append(row)

    def show_empty_state(self):
        """Show empty queue message."""
        self.scrollable.pack_forget()
        self.empty_label.pack(expand=True, fill=tk.BOTH)

    def hide_empty_state(self):
        """Hide empty queue message."""
        self.empty_label.pack_forget()
        self.scrollable.pack(fill=tk.BOTH, expand=True)

    def on_drag_start(self, row_widget, event):
        """Handle drag start from a row widget.

        Args:
            row_widget: The QueueRowWidget being dragged
            event: Mouse event
        """
        self._drag_state['active'] = True
        self._drag_state['widget'] = row_widget
        self._drag_state['start_y'] = event.y_root
        self._drag_state['original_index'] = row_widget.index

        # Apply visual feedback: lighter background to show it's being dragged
        row_widget.container.config(bg='#3a3a3a')
        row_widget.info_frame.config(bg='#3a3a3a')
        row_widget.title_label.config(bg='#3a3a3a', fg='#cccccc')
        row_widget.artist_label.config(bg='#3a3a3a', fg='#999999')
        row_widget.drag_handle.config(bg='#3a3a3a', fg='#999999')

    def on_drag_motion(self, row_widget, event):
        """Handle drag motion with visual feedback.

        Args:
            row_widget: The QueueRowWidget being dragged
            event: Mouse event
        """
        if not self._drag_state['active']:
            return

        current_y = event.y_root

        # Find target row based on cursor position
        target_index = -1
        for i, target_widget in enumerate(self.row_widgets):
            if target_widget == row_widget:
                continue

            # Get widget position
            try:
                target_y = target_widget.winfo_rooty()
                target_height = target_widget.winfo_height()

                # Check if cursor is over this widget
                if target_y <= current_y <= target_y + target_height:
                    # Determine if inserting before or after
                    midpoint = target_y + target_height / 2
                    target_index = i if current_y < midpoint else i + 1
                    # Highlight target row with a clear indicator
                    if target_widget != row_widget:
                        target_widget.container.config(bg='#004455')  # Blue tint to show drop target
                        target_widget.info_frame.config(bg='#004455')
                        target_widget.title_label.config(bg='#004455')
                        target_widget.artist_label.config(bg='#004455')
                        target_widget.drag_handle.config(bg='#004455')
                else:
                    # Reset other rows
                    if target_widget != row_widget:
                        if target_widget.is_current:
                            target_widget._apply_playing_style()
                        else:
                            target_widget._apply_normal_style()
            except tk.TclError:
                pass

        # Store current target for release
        self._drag_state['target_index'] = target_index

    def on_drag_release(self, row_widget, event):
        """Handle drag release to complete reordering.

        Args:
            row_widget: The QueueRowWidget being dragged
            event: Mouse event
        """
        if not self._drag_state['active']:
            return

        self._drag_state['active'] = False
        original_index = self._drag_state['original_index']
        target_index = self._drag_state['target_index']

        # Perform reordering if position changed
        if target_index != -1 and target_index != original_index:
            # Adjust target index if needed
            if target_index > original_index:
                target_index -= 1

            self.queue_manager.reorder_queue(original_index, target_index)
            self.refresh_from_queue()
        else:
            # No position change - just reset styles
            for widget in self.row_widgets:
                if widget.is_current:
                    widget._apply_playing_style()
                else:
                    widget._apply_normal_style()

        # Reset drag state
        self._drag_state['widget'] = None
        self._drag_state['original_index'] = -1
        self._drag_state['target_index'] = -1

    def show_context_menu_for_row(self, row_widget, event):
        """Show context menu for a row widget.

        Args:
            row_widget: The clicked row widget
            event: Mouse event
        """
        # Store selected row for context menu actions
        self._selected_row = row_widget

        # Show context menu at cursor position
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def on_row_double_click(self, row_widget, event):
        """Handle double-click on a row to play that track.

        Args:
            row_widget: The double-clicked row widget
            event: Mouse event
        """
        if 'on_play_track' in self.callbacks:
            self.callbacks['on_play_track'](row_widget.index)

    def on_context_play_next(self):
        """Handle 'Play Next' context menu action."""
        if not self._selected_row:
            return

        index = self._selected_row.index
        if index != self.queue_manager.current_index:
            # Move to after current track
            track = self.queue_manager.queue_items.pop(index)
            insert_pos = self.queue_manager.current_index + 1
            self.queue_manager.queue_items.insert(insert_pos, track)

            # Adjust current_index if needed
            if index < self.queue_manager.current_index:
                self.queue_manager.current_index -= 1

            self.refresh_from_queue()

    def on_context_move_to_end(self):
        """Handle 'Move to End' context menu action."""
        if not self._selected_row:
            return

        index = self._selected_row.index
        if index < len(self.queue_manager.queue_items) - 1:
            # Move to end
            track = self.queue_manager.queue_items.pop(index)
            self.queue_manager.queue_items.append(track)

            # Adjust current_index if needed
            if index < self.queue_manager.current_index:
                self.queue_manager.current_index -= 1
            elif index == self.queue_manager.current_index:
                self.queue_manager.current_index = len(self.queue_manager.queue_items) - 1

            self.refresh_from_queue()

    def on_context_remove_from_queue(self):
        """Handle 'Remove from Queue' context menu action."""
        if not self._selected_row:
            return

        index = self._selected_row.index
        self.queue_manager.remove_from_queue_at_index(index)
        self.refresh_from_queue()

        # Notify if queue is now empty
        if not self.queue_manager.queue_items and 'on_queue_empty' in self.callbacks:
            self.callbacks['on_queue_empty']()

    def on_context_remove_from_library(self):
        """Handle 'Remove from Library' context menu action."""
        if not self._selected_row:
            return

        filepath = self._selected_row.filepath
        if 'on_remove_from_library' in self.callbacks:
            self.callbacks['on_remove_from_library'](filepath)

        # Also remove from queue
        index = self._selected_row.index
        self.queue_manager.remove_from_queue_at_index(index)
        self.refresh_from_queue()

    def on_context_save_to_playlist(self):
        """Handle 'Save to Playlist' context menu action (stub)."""
        # Future feature - currently disabled in menu
        pass

    def scroll_to_current(self):
        """Scroll to make the currently playing track visible."""
        if self.queue_manager.current_index < len(self.row_widgets):
            current_widget = self.row_widgets[self.queue_manager.current_index]
            self.scrollable.scroll_to_widget(current_widget)
