"""Queue row widget for Now Playing view."""

import tkinter as tk
from tkinter import ttk


class QueueRowWidget(ttk.Frame):
    """Individual row widget for queue display with drag-and-drop support.

    Attributes:
        title_text: Track title
        artist_text: Artist name
        filepath: Path to audio file
        index: Position in queue
        is_current: Whether this is the currently playing track
        callbacks: Dictionary of callback functions
    """

    def __init__(
        self, parent, title: str, artist: str, filepath: str, index: int, is_current: bool = False, callbacks: dict = None
    ):
        """Initialize the queue row widget.

        Args:
            parent: Parent widget
            title: Track title
            artist: Artist name
            filepath: Path to audio file
            index: Position in queue
            is_current: Whether this is the currently playing track
            callbacks: Dict of callbacks:
                - on_drag_start(widget, event)
                - on_drag_motion(widget, event)
                - on_drag_release(widget, event)
                - on_context_menu(widget, event)
                - on_double_click(widget, event)
        """
        super().__init__(parent, height=70)
        self.pack_propagate(False)  # Maintain fixed height

        self.title_text = title
        self.artist_text = artist
        self.filepath = filepath
        self.index = index
        self.is_current = is_current
        self.is_playing = is_current
        self.callbacks = callbacks or {}

        # State tracking for drag
        self._drag_start_y = 0
        self._is_dragging = False

        # Setup UI
        self.setup_ui()

        # Apply initial style
        if self.is_current:
            self._apply_playing_style()
        else:
            self._apply_normal_style()

        # Bind events
        self.bind_events()

    def setup_ui(self):
        """Setup the UI components."""
        # Main container
        self.container = tk.Frame(self, bg='#202020')
        self.container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Drag handle on left
        self.drag_handle = tk.Label(
            self.container,
            text="☰",  # Three horizontal lines (hamburger menu icon)
            font=('Helvetica', 14),
            fg='#666666',
            bg='#202020',
            width=2,
        )
        self.drag_handle.pack(side=tk.LEFT, padx=(10, 5), pady=16)

        # Track info container
        self.info_frame = tk.Frame(self.container, bg='#202020')
        self.info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=16)

        # Title label
        self.title_label = tk.Label(
            self.info_frame, text=self.title_text, font=('Helvetica', 15, 'bold'), fg='#ffffff', bg='#202020', anchor='w'
        )
        self.title_label.pack(anchor=tk.W, fill=tk.X)

        # Artist label
        self.artist_label = tk.Label(
            self.info_frame, text=self.artist_text, font=('Helvetica', 12), fg='#888888', bg='#202020', anchor='w'
        )
        self.artist_label.pack(anchor=tk.W, fill=tk.X, pady=(2, 0))

    def bind_events(self):
        """Bind mouse events for drag-and-drop and context menu."""
        # Drag-and-drop on drag handle
        self.drag_handle.bind('<ButtonPress-1>', self.on_drag_start)
        self.drag_handle.bind('<B1-Motion>', self.on_drag_motion)
        self.drag_handle.bind('<ButtonRelease-1>', self.on_drag_release)

        # Right-click context menu (on entire row)
        for widget in [self, self.container, self.info_frame, self.title_label, self.artist_label]:
            widget.bind('<Button-2>', self.on_right_click)  # macOS/Linux right-click
            widget.bind('<Control-Button-1>', self.on_right_click)  # macOS Ctrl+click

        # Double-click to play
        for widget in [self.container, self.info_frame, self.title_label, self.artist_label]:
            widget.bind('<Double-Button-1>', self.on_double_click)

        # Hover effects
        for widget in [self.container, self.info_frame, self.title_label, self.artist_label]:
            widget.bind('<Enter>', lambda e: self._on_hover() if not self.is_current else None)
            widget.bind('<Leave>', lambda e: self._on_leave() if not self.is_current else None)

    def on_drag_start(self, event):
        """Handle drag start event.

        Args:
            event: Mouse button press event
        """
        self._drag_start_y = event.y_root
        self._is_dragging = True

        if 'on_drag_start' in self.callbacks:
            self.callbacks['on_drag_start'](self, event)

    def on_drag_motion(self, event):
        """Handle drag motion event.

        Args:
            event: Mouse motion event
        """
        if not self._is_dragging:
            return

        if 'on_drag_motion' in self.callbacks:
            self.callbacks['on_drag_motion'](self, event)

    def on_drag_release(self, event):
        """Handle drag release event.

        Args:
            event: Mouse button release event
        """
        if not self._is_dragging:
            return

        self._is_dragging = False

        if 'on_drag_release' in self.callbacks:
            self.callbacks['on_drag_release'](self, event)

    def on_right_click(self, event):
        """Handle right-click for context menu.

        Args:
            event: Mouse button event
        """
        if 'on_context_menu' in self.callbacks:
            self.callbacks['on_context_menu'](self, event)

    def on_double_click(self, event):
        """Handle double-click to play track.

        Args:
            event: Mouse button event
        """
        if 'on_double_click' in self.callbacks:
            self.callbacks['on_double_click'](self, event)

    def _on_hover(self):
        """Apply hover style."""
        if not self.is_current:
            self.container.config(bg='#2a2a2a')
            self.info_frame.config(bg='#2a2a2a')
            self.title_label.config(bg='#2a2a2a')
            self.artist_label.config(bg='#2a2a2a')
            self.drag_handle.config(bg='#2a2a2a', fg='#999999')

    def _on_leave(self):
        """Remove hover style."""
        if not self.is_current:
            self._apply_normal_style()

    def _apply_normal_style(self):
        """Apply normal (not playing) style."""
        bg = '#202020'
        self.container.config(bg=bg)
        self.info_frame.config(bg=bg)
        self.title_label.config(bg=bg, fg='#ffffff')
        self.artist_label.config(bg=bg, fg='#888888')
        self.drag_handle.config(bg=bg, fg='#666666')

    def _apply_playing_style(self):
        """Apply playing track style (teal highlight)."""
        bg = '#00343a'  # Dark teal background
        fg = '#33eeff'  # Bright teal foreground
        self.container.config(bg=bg)
        self.info_frame.config(bg=bg)
        self.title_label.config(bg=bg, fg=fg)
        self.artist_label.config(bg=bg, fg=fg)
        self.drag_handle.config(bg=bg, fg=fg)

    def _apply_hover_style(self):
        """Apply hover style during drag operations."""
        bg = '#2a2a2a'
        self.container.config(bg=bg)
        self.info_frame.config(bg=bg)
        self.title_label.config(bg=bg, fg='#ffffff')
        self.artist_label.config(bg=bg, fg='#888888')
        self.drag_handle.config(bg=bg, fg='#999999')

    def set_playing(self, is_playing: bool, is_paused: bool = False):
        """Mark this row as playing or not.

        Args:
            is_playing: Whether this track is playing
            is_paused: Whether playback is paused
        """
        self.is_playing = is_playing
        self.is_current = is_playing

        if is_playing:
            self._apply_playing_style()
            # Could add pause indicator here if needed
        else:
            self._apply_normal_style()

    def update_index(self, index: int):
        """Update the row's index position.

        Args:
            index: New index position
        """
        self.index = index
