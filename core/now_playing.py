"""Now Playing view with custom widgets for queue visualization."""

import tkinter as tk
from core.widgets import QueueRowWidget, ScrollableFrame
from tkinter import ttk


class NowPlayingView(ttk.Frame):
    """Split Now Playing view with fixed current track and scrollable next tracks.

    Attributes:
        queue_manager: QueueManager instance for queue data
        callbacks: Dictionary of callback functions for actions
        current_row_widget: QueueRowWidget for currently playing track
        next_row_widgets: List of QueueRowWidget instances for upcoming tracks
    """

    def __init__(self, parent, callbacks: dict, queue_manager, loop_enabled: bool = True):
        """Initialize the Now Playing view.

        Args:
            parent: Parent widget
            callbacks: Dict of callbacks:
                - on_queue_empty(): Called when queue becomes empty
                - on_remove_from_library(filepath): Remove track from library
                - on_play_track(index): Play track at index
            queue_manager: QueueManager instance
            loop_enabled: Whether loop mode is currently enabled (default: True)
        """
        super().__init__(parent)
        self.queue_manager = queue_manager
        self.callbacks = callbacks
        self.current_row_widget = None
        self.next_row_widgets = []
        self.loop_enabled = loop_enabled
        self.player_core = None  # Will be set later by MusicPlayer

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
        """Setup the UI components with split layout."""
        # Current track section (fixed, non-scrollable)
        self.current_section = tk.Frame(self, bg='#202020', height=80)
        self.current_section.pack(fill=tk.X, padx=0, pady=0)
        self.current_section.pack_propagate(False)

        self.current_label = tk.Label(
            self.current_section,
            text="Now Playing",
            font=('Helvetica', 10, 'bold'),
            fg='#888888',
            bg='#202020',
            anchor='w',
        )
        self.current_label.pack(anchor=tk.W, fill=tk.X, padx=10, pady=(8, 2))

        self.current_container = tk.Frame(self.current_section, bg='#202020')
        self.current_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Divider line
        divider1 = tk.Frame(self, bg='#404040', height=1)
        divider1.pack(fill=tk.X, padx=0, pady=0)

        # Next tracks section (scrollable)
        self.next_section = tk.Frame(self, bg='#202020')
        self.next_section.pack(fill=tk.BOTH, expand=True)

        self.next_label = tk.Label(
            self.next_section,
            text="Next",
            font=('Helvetica', 10, 'bold'),
            fg='#888888',
            bg='#202020',
            anchor='w',
        )
        self.next_label.pack(anchor=tk.W, fill=tk.X, padx=10, pady=(8, 2))

        # Scrollable container for next tracks
        self.scrollable = ScrollableFrame(self.next_section)
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
        self._selected_row = None

        self.context_menu.add_command(label="Play Next", command=self.on_context_play_next)
        self.context_menu.add_command(label="Move to End", command=self.on_context_move_to_end)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Remove from Queue", command=self.on_context_remove_from_queue)
        self.context_menu.add_command(label="Remove from Library", command=self.on_context_remove_from_library)
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Save to Playlist",
            command=self.on_context_save_to_playlist,
            state='disabled',
        )

    def refresh_from_queue(self):
        """Rebuild view from queue_manager data, showing only viewport-fitting tracks."""
        # Check if there's actual media loaded in the player
        # Show empty state if no media is loaded, even if queue has items
        has_media = False
        if hasattr(self, 'player_core') and self.player_core:
            media = self.player_core.media_player.get_media()
            has_media = media is not None
        
        # Show empty state if queue is empty OR no media is loaded
        if not self.queue_manager.queue_items or not has_media:
            # Clear old widgets before showing empty state to prevent stale data
            if self.current_row_widget:
                self.current_row_widget.destroy()
                self.current_row_widget = None

            for widget in self.next_row_widgets:
                widget.destroy()
            self.next_row_widgets.clear()

            self.show_empty_state()
            return

        self.hide_empty_state()

        # Get queue items
        if self.queue_manager.shuffle_enabled:
            items = self.queue_manager.get_shuffled_queue_items()
            current_filepath = (
                self.queue_manager.queue_items[self.queue_manager.current_index]
                if self.queue_manager.current_index < len(self.queue_manager.queue_items)
                else None
            )
            # In shuffle mode, find current track in shuffled items
            current_display_index = None
            for i, (filepath, _, _, _, _, _) in enumerate(items):
                if filepath == current_filepath:
                    current_display_index = i
                    break
            display_items = items
        else:
            items = self.queue_manager.get_queue_items()
            current_display_index = self.queue_manager.current_index

            # When loop is OFF, only show tracks from current onwards (no wraparound)
            # When loop is ON, show current track followed by remaining tracks, wrapping around
            if self.loop_enabled:
                # Rotate display so current track is at top
                display_items = items[current_display_index:] + items[:current_display_index]
            else:
                # Linear mode: only show current and remaining tracks (no wraparound)
                display_items = items[current_display_index:]

        if not display_items:
            # Clear old widgets before showing empty state to prevent stale data
            if self.current_row_widget:
                self.current_row_widget.destroy()
                self.current_row_widget = None

            for widget in self.next_row_widgets:
                widget.destroy()
            self.next_row_widgets.clear()

            self.show_empty_state()
            return

        # Clear old widgets
        if self.current_row_widget:
            self.current_row_widget.destroy()
            self.current_row_widget = None

        for widget in self.next_row_widgets:
            widget.destroy()
        self.next_row_widgets.clear()

        # Create current track widget (first item in display)
        filepath, artist, title, album, track_num, date = display_items[0]
        actual_index = self.queue_manager.queue_items.index(filepath) if filepath in self.queue_manager.queue_items else 0

        self.current_row_widget = QueueRowWidget(
            self.current_container,
            title=title,
            artist=artist,
            filepath=filepath,
            index=actual_index,
            is_current=True,
            callbacks={
                'on_drag_start': self.on_drag_start,
                'on_drag_motion': self.on_drag_motion,
                'on_drag_release': self.on_drag_release,
                'on_context_menu': self.show_context_menu_for_row,
                'on_double_click': self.on_row_double_click,
            },
        )
        self.current_row_widget.pack(fill=tk.BOTH, expand=True, pady=0)

        # Calculate how many next tracks fit in the viewport
        max_visible_tracks = self._calculate_max_visible_tracks()

        # Create next tracks widgets (remaining items, limited by viewport)
        for display_i in range(1, min(len(display_items), max_visible_tracks + 1)):
            filepath, artist, title, album, track_num, date = display_items[display_i]
            actual_index = (
                self.queue_manager.queue_items.index(filepath) if filepath in self.queue_manager.queue_items else display_i
            )

            row = QueueRowWidget(
                self.scrollable.scrollable_frame,
                title=title,
                artist=artist,
                filepath=filepath,
                index=actual_index,
                is_current=False,
                callbacks={
                    'on_drag_start': self.on_drag_start,
                    'on_drag_motion': self.on_drag_motion,
                    'on_drag_release': self.on_drag_release,
                    'on_context_menu': self.show_context_menu_for_row,
                    'on_double_click': self.on_row_double_click,
                },
            )
            row.pack(fill=tk.X, pady=1)
            self.next_row_widgets.append(row)

    def _calculate_max_visible_tracks(self):
        """Calculate how many next tracks fit in the viewport without scrolling.

        Returns:
            int: Maximum number of visible next tracks based on available height
        """
        # Force update of widget geometry
        self.update_idletasks()

        # Get heights
        total_height = self.next_section.winfo_height()
        label_height = self.next_label.winfo_reqheight()

        # Each row is 70px + 1px padding
        row_height = 70 + 1

        # Calculate available space for tracks
        available_height = total_height - label_height - 10  # 10px for margins

        # Calculate how many tracks fit
        max_tracks = max(1, int(available_height / row_height))

        return max_tracks

    def show_empty_state(self):
        """Show empty queue message."""
        # Destroy any existing widgets to ensure clean state
        if self.current_row_widget:
            self.current_row_widget.destroy()
            self.current_row_widget = None

        for widget in self.next_row_widgets:
            widget.destroy()
        self.next_row_widgets.clear()

        # Hide all sections
        self.current_section.pack_forget()
        self.scrollable.pack_forget()
        self.next_label.pack_forget()
        self.next_section.pack_forget()

        # Show empty state
        self.empty_label.pack(expand=True, fill=tk.BOTH)
        self.update_idletasks()  # Force UI update

    def hide_empty_state(self):
        """Hide empty queue message."""
        self.empty_label.pack_forget()
        self.current_section.pack(fill=tk.X, padx=0, pady=0)
        self.current_section.pack_propagate(False)
        divider = tk.Frame(self, bg='#404040', height=1)
        divider.pack(fill=tk.X, padx=0, pady=0)
        self.next_label.pack(anchor=tk.W, fill=tk.X, padx=10, pady=(8, 2))
        self.next_section.pack(fill=tk.BOTH, expand=True)
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
        all_widgets = [self.current_row_widget] + self.next_row_widgets if self.current_row_widget else self.next_row_widgets

        target_index = -1
        for i, target_widget in enumerate(all_widgets):
            if target_widget == row_widget:
                continue

            try:
                target_y = target_widget.winfo_rooty()
                target_height = target_widget.winfo_height()

                if target_y <= current_y <= target_y + target_height:
                    midpoint = target_y + target_height / 2
                    target_index = i if current_y < midpoint else i + 1
                    if target_widget != row_widget:
                        target_widget.container.config(bg='#004455')
                        target_widget.info_frame.config(bg='#004455')
                        target_widget.title_label.config(bg='#004455')
                        target_widget.artist_label.config(bg='#004455')
                        target_widget.drag_handle.config(bg='#004455')
                else:
                    if target_widget != row_widget:
                        if target_widget.is_current:
                            target_widget._apply_playing_style()
                        else:
                            target_widget._apply_normal_style()
            except tk.TclError:
                pass

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

        if target_index != -1 and target_index != original_index:
            if target_index > original_index:
                target_index -= 1

            self.queue_manager.reorder_queue(original_index, target_index)
            self.refresh_from_queue()
        else:
            all_widgets = [self.current_row_widget] + self.next_row_widgets if self.current_row_widget else self.next_row_widgets
            for widget in all_widgets:
                if widget.is_current:
                    widget._apply_playing_style()
                else:
                    widget._apply_normal_style()

        self._drag_state['widget'] = None
        self._drag_state['original_index'] = -1
        self._drag_state['target_index'] = -1

    def show_context_menu_for_row(self, row_widget, event):
        """Show context menu for a row widget.

        Args:
            row_widget: The clicked row widget
            event: Mouse event
        """
        self._selected_row = row_widget

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
            track = self.queue_manager.queue_items.pop(index)
            insert_pos = self.queue_manager.current_index + 1
            self.queue_manager.queue_items.insert(insert_pos, track)

            if index < self.queue_manager.current_index:
                self.queue_manager.current_index -= 1

            self.refresh_from_queue()

    def on_context_move_to_end(self):
        """Handle 'Move to End' context menu action."""
        if not self._selected_row:
            return

        index = self._selected_row.index
        if index < len(self.queue_manager.queue_items) - 1:
            track = self.queue_manager.queue_items.pop(index)
            self.queue_manager.queue_items.append(track)

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

        if not self.queue_manager.queue_items and 'on_queue_empty' in self.callbacks:
            self.callbacks['on_queue_empty']()

    def on_context_remove_from_library(self):
        """Handle 'Remove from Library' context menu action."""
        if not self._selected_row:
            return

        filepath = self._selected_row.filepath
        if 'on_remove_from_library' in self.callbacks:
            self.callbacks['on_remove_from_library'](filepath)

        index = self._selected_row.index
        self.queue_manager.remove_from_queue_at_index(index)
        self.refresh_from_queue()

    def on_context_save_to_playlist(self):
        """Handle 'Save to Playlist' context menu action (stub)."""
        pass

    def scroll_to_current(self):
        """Scroll to make the currently playing track visible."""
        if self.current_row_widget:
            self.current_row_widget.pack(fill=tk.BOTH, expand=True)

    def set_loop_enabled(self, enabled: bool) -> None:
        """Update loop enabled state and refresh the view.

        Args:
            enabled: Whether loop mode is enabled
        """
        self.loop_enabled = enabled
        self.refresh_from_queue()
