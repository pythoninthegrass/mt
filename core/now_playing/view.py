"""Now Playing view with custom widgets for queue visualization and lyrics display."""

import tkinter as tk
from core.logging import log_player_action
from core.widgets import QueueRowWidget
from core.widgets.lyrics_panel import LyricsPanel
from tkinter import ttk


class NowPlayingView(tk.Frame):
    """Split Now Playing view with fixed current track and scrollable next tracks.

    Attributes:
        queue_manager: QueueManager instance for queue data
        callbacks: Dictionary of callback functions for actions
        current_row_widget: QueueRowWidget for currently playing track
        next_row_widgets: List of QueueRowWidget instances for upcoming tracks
    """

    def __init__(self, parent, callbacks: dict, queue_manager, loop_enabled: bool = True, lyrics_manager=None):
        """Initialize the Now Playing view.

        Args:
            parent: Parent widget
            callbacks: Dict of callbacks:
                - on_queue_empty(): Called when queue becomes empty
                - on_remove_from_library(filepath): Remove track from library
                - on_play_track(index): Play track at index
            queue_manager: QueueManager instance
            loop_enabled: Whether loop mode is currently enabled (default: True)
            lyrics_manager: LyricsManager instance for lyrics fetching (optional)
        """
        super().__init__(parent, bg='#000000', relief=tk.FLAT, borderwidth=0)
        self.queue_manager = queue_manager
        self.callbacks = callbacks
        self.lyrics_manager = lyrics_manager
        self.current_row_widget = None
        self.next_row_widgets = []
        self.loop_enabled = loop_enabled
        self.player_core = None  # Will be set later by MusicPlayer

        # Active tab state
        self.active_tab = "up_next"  # or "lyrics"

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
        """Setup the UI components with 2-column tabbed layout."""
        # Main container with horizontal layout
        self.main_container = tk.Frame(self, bg='#000000')
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # LEFT COLUMN: Album art stub with more space
        # Right column will be ~857px (67% of original 1280px)
        # Album art column gets remaining space (~873px)
        self.album_art_column = tk.Frame(self.main_container, bg='#000000')
        self.album_art_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.setup_album_art_stub()

        # RIGHT COLUMN: Tabbed content - shrunk by 33% to ~857px
        self.content_column = tk.Frame(self.main_container, bg='#000000', width=857)
        self.content_column.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15), pady=0)
        self.content_column.pack_propagate(False)

        # Tab bar with grey line at bottom
        self.setup_tab_bar()

        # White underline container (packed after tab bar, before content)
        self.white_underline_container = tk.Frame(self.content_column, bg='#000000', height=4)
        self.white_underline_container.pack(fill=tk.X, padx=0, pady=0)
        self.white_underline_container.pack_propagate(False)

        # Active tab white underline (positioned dynamically)
        self.active_underline = tk.Frame(
            self.white_underline_container,
            bg='#FFFFFF',
            height=4
        )
        # Start hidden until properly positioned when view is shown
        self.active_underline.place(x=0, y=0, width=0)

        # Content frame for switching between tabs
        self.content_frame = tk.Frame(self.content_column, bg='#000000')
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # UP NEXT content (queue view)
        self.up_next_frame = tk.Frame(self.content_frame, bg='#000000')
        self.setup_up_next_content()

        # LYRICS content
        self.lyrics_frame = tk.Frame(self.content_frame, bg='#000000')
        self.lyrics_panel = LyricsPanel(self.lyrics_frame)
        self.lyrics_panel.pack(fill=tk.BOTH, expand=True)

        # Empty state label (for up_next tab)
        self.empty_label = tk.Label(
            self.up_next_frame,
            text="Queue is empty\n\nDouble-click a track in Library to start playing",
            font=('Helvetica', 14),
            fg='#888888',
            bg='#000000',
            justify=tk.CENTER,
        )

        # Context menu
        self.setup_context_menu()

        # Show initial tab (up_next)
        self.switch_tab("up_next")

        # Initially show empty state
        self.show_empty_state()

    def setup_album_art_stub(self):
        """Setup placeholder album art with musical note icon centered in column."""
        # Create large square container for album art
        square_size = 400

        # Use place to center both horizontally and vertically in the album art column
        art_container = tk.Frame(
            self.album_art_column,
            bg='#000000',
            width=square_size,
            height=square_size
        )
        art_container.pack_propagate(False)
        # Center both horizontally and vertically
        art_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Musical note icon (large, centered in square)
        self.album_art_icon = tk.Label(
            art_container,
            text="🎵",
            font=('Helvetica', 120),
            fg='#666666',
            bg='#000000'
        )
        self.album_art_icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def setup_tab_bar(self):
        """Setup tab buttons for switching between UP NEXT and LYRICS."""
        self.tab_bar = tk.Frame(self.content_column, bg='#000000', height=50)
        self.tab_bar.pack(fill=tk.X, padx=0, pady=0)
        self.tab_bar.pack_propagate(False)

        # Container for tab labels (centered horizontally at top)
        self.tabs_container = tk.Frame(self.tab_bar, bg='#000000')
        self.tabs_container.pack(side=tk.TOP, pady=(10, 0))  # Pack at top with small top margin

        # UP NEXT tab button - centered with more padding
        self.up_next_tab = tk.Label(
            self.tabs_container,
            text="UP NEXT",
            font=('Helvetica', 11, 'bold'),
            fg='#FFFFFF',
            bg='#000000',
            padx=15,
            pady=8
        )
        self.up_next_tab.pack(side=tk.LEFT, padx=30)  # Generous spacing
        self.up_next_tab.bind('<Button-1>', lambda e: self.switch_tab("up_next"))

        # LYRICS tab button - centered with more padding
        self.lyrics_tab = tk.Label(
            self.tabs_container,
            text="LYRICS",
            font=('Helvetica', 11, 'bold'),
            fg='#FFFFFF',
            bg='#000000',
            padx=15,
            pady=8
        )
        self.lyrics_tab.pack(side=tk.LEFT, padx=30)  # Generous spacing
        self.lyrics_tab.bind('<Button-1>', lambda e: self.switch_tab("lyrics"))

        # Grey underline at the bottom edge of tab bar
        self.grey_underline = tk.Frame(self.tab_bar, bg='#555555', height=2)
        self.grey_underline.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)

    def setup_up_next_content(self):
        """Setup the UP NEXT tab content (queue view)."""
        # Current track section
        self.current_section = tk.Frame(self.up_next_frame, bg='#000000', height=100)
        self.current_section.pack(fill=tk.X, padx=0, pady=0)
        self.current_section.pack_propagate(False)

        self.current_label = tk.Label(
            self.current_section,
            text="Now Playing",
            font=('Helvetica', 10, 'bold'),
            fg='#888888',
            bg='#000000',
            anchor='w',
        )
        self.current_label.pack(anchor=tk.W, fill=tk.X, padx=10, pady=(8, 2))

        self.current_container = tk.Frame(self.current_section, bg='#000000')
        self.current_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Divider line
        self.divider = tk.Frame(self.up_next_frame, bg='#404040', height=1)
        self.divider.pack(fill=tk.X, padx=0, pady=0)

        # Next tracks section
        self.next_section = tk.Frame(self.up_next_frame, bg='#000000')
        self.next_section.pack(fill=tk.BOTH, expand=True)

        self.next_label = tk.Label(
            self.next_section,
            text="Next",
            font=('Helvetica', 10, 'bold'),
            fg='#888888',
            bg='#000000',
            anchor='w',
        )
        self.next_label.pack(anchor=tk.W, fill=tk.X, padx=10, pady=(8, 2))

        # Fixed container for next tracks
        self.next_tracks_container = tk.Frame(self.next_section, bg='#000000')
        self.next_tracks_container.pack(fill=tk.X, anchor=tk.N)

    def switch_tab(self, tab_name: str):
        """Switch between UP NEXT and LYRICS tabs.

        Args:
            tab_name: Either "up_next" or "lyrics"
        """
        # Log tab switch with before/after state
        old_tab = self.active_tab
        self.active_tab = tab_name

        # Log the tab switch action
        log_player_action(
            "tab_switch",
            trigger_source="gui",
            old_state=old_tab.replace("_", " ").title(),
            new_state=tab_name.replace("_", " ").title(),
            description=f"Switched tab from {old_tab.replace('_', ' ').title()} to {tab_name.replace('_', ' ').title()}"
        )

        # Update tab styles
        self._update_tab_styles()

        # Show appropriate content
        if tab_name == "up_next":
            self.lyrics_frame.pack_forget()
            self.up_next_frame.pack(fill=tk.BOTH, expand=True)
        elif tab_name == "lyrics":
            self.up_next_frame.pack_forget()
            self.lyrics_frame.pack(fill=tk.BOTH, expand=True)

    def _update_tab_styles(self):
        """Update tab underline position based on active tab."""
        # Both tabs stay white - only underline moves

        # Force geometry update to get accurate positions
        self.update_idletasks()

        # Calculate absolute positions of tabs
        if self.active_tab == "up_next":
            # Get UP NEXT tab position and width
            tab_x = self.up_next_tab.winfo_x()
            tab_width = self.up_next_tab.winfo_width()

            # Get tabs_container position relative to white_underline_container
            container_x = self.tabs_container.winfo_x()

            # Calculate absolute position
            underline_x = container_x + tab_x

            self.active_underline.place(x=underline_x, y=0, width=tab_width)
        else:
            # Get LYRICS tab position and width
            tab_x = self.lyrics_tab.winfo_x()
            tab_width = self.lyrics_tab.winfo_width()

            # Get tabs_container position relative to white_underline_container
            container_x = self.tabs_container.winfo_x()

            # Calculate absolute position
            underline_x = container_x + tab_x

            self.active_underline.place(x=underline_x, y=0, width=tab_width)

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
        """Rebuild view from queue_manager data, showing only fully visible tracks."""
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

            # Apply rotation logic for shuffle mode
            if current_display_index is not None:
                if self.loop_enabled:
                    # Rotate display so current track is at top
                    display_items = items[current_display_index:] + items[:current_display_index]
                else:
                    # Linear mode: only show current and remaining tracks (no wraparound)
                    display_items = items[current_display_index:]
            else:
                # Fallback if current track not found in shuffled list
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

        # Determine if we have next tracks
        has_next_tracks = len(display_items) > 1

        # Show sections based on what we have
        self.hide_empty_state(show_next=has_next_tracks)

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

        # Create next track widgets - only create what fits in viewport
        if has_next_tracks:
            # Calculate how many tracks fit immediately (before creating widgets)
            # Use a reasonable default since geometry might not be ready yet
            self.update_idletasks()
            parent_height = self.master.winfo_height() if self.master else 0

            if parent_height > 1:
                # Calculate based on actual geometry
                row_height = 71
                current_section_height = 100
                divider_height = 1
                next_label_height = 30  # Approximate
                tab_bar_height = 50  # Height of the tab bar
                # Subtract tab bar height from available space
                available_height = parent_height - tab_bar_height - current_section_height - divider_height - next_label_height
                tracks_to_create = max(1, min(int(available_height / row_height), len(display_items) - 1))
            else:
                # Fallback: create a reasonable number
                tracks_to_create = min(10, len(display_items) - 1)


            # Create only the widgets that will be visible (skip index 0 which is current)
            for display_i in range(1, min(tracks_to_create + 1, len(display_items))):
                filepath, artist, title, album, track_num, date = display_items[display_i]
                actual_index = (
                    self.queue_manager.queue_items.index(filepath) if filepath in self.queue_manager.queue_items else display_i
                )

                row = QueueRowWidget(
                    self.next_tracks_container,
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

    def _calculate_viewport_layout(self, num_tracks_available: int):
        """Calculate how many complete tracks fit in viewport without stretching.

        Calculates based on actual available viewport height:
        - Total window height
        - Minus current section (100px)
        - Minus divider (1px)
        - Minus next label height (~30px)
        = Available height for track rows

        Then divides by row height (71px = 70px + 1px padding) to get max complete rows.

        Args:
            num_tracks_available: Number of next tracks available to show

        Returns:
            tuple: (tracks_to_show, top_padding) - number of complete tracks that fit
        """
        # Force update to get accurate geometry
        self.update_idletasks()

        # Get total height - use parent's height since this frame might not have expanded yet
        # self is packed with expand=True, fill=BOTH, so it should fill the parent
        parent_height = self.master.winfo_height() if self.master else 0
        self_height = self.winfo_height()

        # Use whichever is larger and valid
        total_height = max(parent_height, self_height)


        # If height not yet calculated (widget not yet rendered), use a safe default
        if total_height <= 1:
            # Fallback: assume standard 768px window height
            # Total ~768px - current section 100px - divider 1px - next label 30px = ~637px
            # 637 / 71 = ~8 tracks
            tracks_to_show = min(8, num_tracks_available)
            return tracks_to_show, 0

        # Calculate fixed sections heights
        current_section_height = 100  # Fixed height from setup_ui
        divider_height = 1
        next_label_height = self.next_label.winfo_reqheight()
        tab_bar_height = 50  # Height of the tab bar

        # Calculate available height for track rows
        available_height = total_height - tab_bar_height - current_section_height - divider_height - next_label_height

        # Each row is 70px + 1px padding
        row_height = 71

        # Calculate how many complete rows fit (minimum 1)
        max_complete_rows = max(1, int(available_height / row_height))

        # Don't show more than available
        tracks_to_show = min(max_complete_rows, num_tracks_available)


        return tracks_to_show, 0

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
        self.divider.pack_forget()
        self.next_tracks_container.pack_forget()
        self.next_label.pack_forget()
        self.next_section.pack_forget()

        # Show empty state
        self.empty_label.pack(expand=True, fill=tk.BOTH)
        self.update_idletasks()  # Force UI update  # Force UI update

    def hide_empty_state(self, show_next: bool = True):
        """Hide empty queue message and show sections.

        Args:
            show_next: Whether to show the Next section (default: True)
        """
        self.empty_label.pack_forget()
        self.current_section.pack(fill=tk.X, padx=0, pady=0)
        self.current_section.pack_propagate(False)

        # Only show Next section if requested
        if show_next:
            self.divider.pack(fill=tk.X, padx=0, pady=0)
            self.next_label.pack(anchor=tk.W, fill=tk.X, padx=10, pady=(8, 2))
            self.next_section.pack(fill=tk.BOTH, expand=True)
            # Pack container anchored to top, no expand so it doesn't fill remaining space
            # This prevents the last row from stretching
            self.next_tracks_container.pack(fill=tk.X, anchor=tk.N)
        else:
            # Hide Next section and divider when there are no upcoming tracks
            self.divider.pack_forget()
            self.next_label.pack_forget()
            self.next_section.pack_forget()
            self.next_tracks_container.pack_forget()

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

    def update_lyrics(self, artist: str, title: str, album: str | None = None):
        """Update lyrics display for current track.

        Args:
            artist: Artist name
            title: Song title
            album: Album name (optional)
        """
        if not self.lyrics_manager:
            self.lyrics_panel.show_not_found(title, artist)
            return

        # Show loading state
        self.lyrics_panel.show_loading()

        # Fetch lyrics (async with callback)
        def on_lyrics_loaded(lyrics_data):
            # Thread-safe UI update using after()
            self.after(0, lambda: self._display_lyrics(lyrics_data))

        self.lyrics_manager.get_lyrics(artist, title, album, on_complete=on_lyrics_loaded)

    def _display_lyrics(self, lyrics_data: dict):
        """Display fetched lyrics (called on main thread).

        Args:
            lyrics_data: Dict from LyricsManager
        """
        if lyrics_data.get("found") and lyrics_data.get("lyrics"):
            self.lyrics_panel.show_lyrics(
                lyrics_data.get("title", ""),
                lyrics_data.get("artist", ""),
                lyrics_data.get("lyrics", "")
            )
        else:
            self.lyrics_panel.show_not_found(
                lyrics_data.get("title", ""),
                lyrics_data.get("artist", "")
            )
