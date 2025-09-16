import json
import os
import tkinter as tk
import tkinter.font as tkfont
from config import (
    BUTTON_STYLE,
    BUTTON_SYMBOLS,
    COLORS,
    LISTBOX_CONFIG,
    PROGRESS_BAR,
    THEME_CONFIG,
)
from core.controls import PlayerCore
from core.progress import ProgressControl
from core.theme import setup_theme
from core.volume import VolumeControl
from decouple import config
from pathlib import Path
from tkinter import ttk


class PlayerControls:
    def __init__(self, canvas, command_callbacks, initial_loop_enabled=True):
        self.canvas = canvas
        self.callbacks = command_callbacks
        self.add_button = None
        self.loop_button = None
        self.play_button = None
        self.loop_enabled = initial_loop_enabled
        self.setup_playback_controls()
        self.setup_utility_controls()

        # Bind canvas resize after all buttons are created
        self.canvas.bind('<Configure>', self._on_canvas_resize)

    def setup_playback_controls(self):
        # Create playback controls directly on canvas
        x_position = 10
        y_position = PROGRESS_BAR['controls_y'] - 25

        for action, symbol in [
            ('previous', BUTTON_SYMBOLS['prev']),
            ('play', BUTTON_SYMBOLS['play']),
            ('next', BUTTON_SYMBOLS['next']),
        ]:
            button = tk.Label(
                self.canvas,
                text=symbol,
                font=BUTTON_STYLE['font'],
                fg=THEME_CONFIG['colors']['fg'],
                bg=THEME_CONFIG['colors']['bg'],
            )
            button.place(x=x_position, y=y_position)

            # Bind click and hover events
            button.bind('<Button-1>', lambda e, a=action: self.callbacks[a]())
            button.bind('<Enter>', lambda e, b=button: b.configure(fg=THEME_CONFIG['colors']['primary']))
            button.bind('<Leave>', lambda e, b=button: b.configure(fg=THEME_CONFIG['colors']['fg']))

            if action == 'play':
                self.play_button = button

            x_position += button.winfo_reqwidth() + 5  # Add spacing between buttons

        # Store the width for progress bar calculations
        self.controls_width = x_position + 15

    def setup_utility_controls(self):
        # Create utility controls directly on canvas
        y_position = PROGRESS_BAR['controls_y'] - 25

        # Wait for canvas to be ready
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()

        # Add button (rightmost)
        self.add_button = tk.Label(
            self.canvas,
            text=BUTTON_SYMBOLS['add'],
            font=BUTTON_STYLE['font'],
            fg=THEME_CONFIG['colors']['fg'],
            bg=THEME_CONFIG['colors']['bg'],
        )
        self.add_button.place(x=canvas_width - 60, y=y_position)
        self.add_button.bind('<Button-1>', lambda e: self.callbacks['add']())
        self.add_button.bind('<Enter>', lambda e: self.add_button.configure(fg=THEME_CONFIG['colors']['primary']))
        self.add_button.bind('<Leave>', lambda e: self.add_button.configure(fg=THEME_CONFIG['colors']['fg']))

        # Loop button (to the left of add button)
        self.loop_button = tk.Label(
            self.canvas,
            text=BUTTON_SYMBOLS['loop'],
            font=BUTTON_STYLE['font'],
            fg=THEME_CONFIG['colors']['fg'],  # Start with default color
            bg=THEME_CONFIG['colors']['bg'],
        )
        self.loop_button.place(x=canvas_width - 120, y=y_position)
        self.loop_button.bind('<Button-1>', lambda e: self.callbacks['loop']())
        self.loop_button.bind('<Enter>', lambda e: self.loop_button.configure(fg=THEME_CONFIG['colors']['primary']))
        self.loop_button.bind(
            '<Leave>',
            lambda e: self.loop_button.configure(fg=COLORS['loop_enabled'] if self.loop_enabled else COLORS['loop_disabled']),
        )

        # Force update loop button color after creation
        self.update_loop_button_color(self.loop_enabled)

        # Store the width for progress bar calculations
        self.utility_width = 120

    def _on_canvas_resize(self, event):
        """Recenter the buttons vertically and reposition all controls when canvas is resized."""
        if not all([self.add_button, self.loop_button, self.play_button]):
            return

        # Calculate new y position (centered vertically)
        new_y = (event.height - 25) // 2  # 25 is approximate button height

        # Calculate positions relative to canvas width
        canvas_width = event.width

        # Utility controls are positioned from the right
        # Add button at right edge minus padding
        add_x = canvas_width - 60
        self.add_button.place(x=add_x, y=new_y)

        # Loop button to the left of add button
        loop_x = canvas_width - 120
        self.loop_button.place(x=loop_x, y=new_y)

        # Playback controls are positioned from the left, maintaining relative spacing
        # Find playback control buttons (they are tk.Label widgets that are not add_button or loop_button)
        playback_buttons = []
        for child in self.canvas.winfo_children():
            if isinstance(child, tk.Label) and child not in [self.add_button, self.loop_button]:
                playback_buttons.append(child)

        # Position playback controls with the same spacing as initial setup
        x_position = 10  # Same as initial setup
        for button in playback_buttons:
            button.place(x=x_position, y=new_y)
            # Use the same spacing calculation as setup_playback_controls
            x_position += button.winfo_reqwidth() + 5

        # Update controls width for progress bar calculations
        self.controls_width = x_position + 15  # Same as initial setup

    def update_loop_button_color(self, loop_enabled):
        """Update loop button color based on loop state."""
        self.loop_enabled = loop_enabled  # Update the internal state
        self.loop_button.configure(fg=COLORS['loop_enabled'] if loop_enabled else COLORS['loop_disabled'])


class ProgressBar:
    def __init__(self, window, progress_frame, callbacks, initial_loop_enabled=True):
        self.window = window
        self.progress_frame = progress_frame
        self.callbacks = callbacks
        self.initial_loop_enabled = initial_loop_enabled
        self.setup_progress_bar()
        self.setup_volume_control()

    def setup_progress_bar(self):
        # Create canvas for custom progress bar
        self.canvas = tk.Canvas(
            self.progress_frame,
            height=PROGRESS_BAR['canvas_height'],
            background=THEME_CONFIG['colors']['bg'],
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.X)

        # Create controls with initial loop state
        self.controls = PlayerControls(self.canvas, self.callbacks, initial_loop_enabled=self.initial_loop_enabled)
        self.controls_width = self.controls.controls_width

        # Create progress bar control
        self.progress_control = ProgressControl(
            self.canvas,
            {
                'bar_y': PROGRESS_BAR['bar_y'],
                'circle_radius': PROGRESS_BAR['circle_radius'],
                'line_width': PROGRESS_BAR['line_width'],
                'colors': THEME_CONFIG['colors'],
                'progress_bg': PROGRESS_BAR['progress_bg'],
                'time_label_y': PROGRESS_BAR['time_label_y'],
                'track_info_y': PROGRESS_BAR['track_info_y'],
            },
            {
                'start_drag': self.callbacks['start_drag'],
                'drag': self.callbacks['drag'],
                'end_drag': self.callbacks['end_drag'],
                'click_progress': self.callbacks['click_progress'],
            },
        )
        self.progress_control.set_controls_width(self.controls_width)

        # Define properties for backwards compatibility
        self.bar_y = PROGRESS_BAR['bar_y']
        self.circle_radius = PROGRESS_BAR['circle_radius']
        self.line = self.progress_control.line
        self.progress_line = self.progress_control.progress_line
        self.progress_circle = self.progress_control.progress_circle
        self.time_text = self.progress_control.time_text
        self.track_info = self.progress_control.track_info
        self.dragging = False
        self.last_drag_time = 0

        # For compatibility with existing code
        self.progress_hitbox = self.progress_control.progress_hitbox

        # Bind window resize
        self.canvas.bind('<Configure>', self.on_resize)

    def setup_volume_control(self):
        """Create and setup custom volume control slider."""
        # Calculate positions with proper spacing
        progress_end_x = self.canvas.coords(self.line)[2]  # End of progress line

        # Calculate volume position accounting for utility controls width
        canvas_width = self.canvas.winfo_width()
        utility_controls_width = self.controls.utility_width  # Width reserved for loop and add buttons
        available_space = canvas_width - utility_controls_width - progress_end_x - 40  # 40 for padding

        # Position volume control with proper spacing, ensuring it doesn't overlap with utility controls
        volume_x_start = progress_end_x + 40  # Add padding after progress line

        # Create volume control
        self.volume_control = VolumeControl(
            self.canvas,
            self.bar_y,
            self.circle_radius,
            BUTTON_SYMBOLS,
            THEME_CONFIG,
            {'volume_change': self.callbacks['volume_change']},
        )
        self.volume_control.setup_volume_control(volume_x_start, PROGRESS_BAR['volume_slider_length'])

        # Add properties for backwards compatibility
        self.volume_circle = self.volume_control.volume_circle
        self.volume_dragging = False
        self.volume_value = 80
        self.volume_x_start = volume_x_start
        self.volume_line_bg = self.volume_control.volume_line_bg
        self.volume_line_fg = self.volume_control.volume_line_fg
        self.volume_slider_width = self.volume_control.volume_slider_width
        self.volume_circle_radius = self.volume_control.volume_circle_radius
        self.volume_hitbox = self.volume_control.volume_hitbox
        self.volume_icon = self.volume_control.volume_icon

    def on_resize(self, event):
        """Handle window resize."""
        # Update control button positions first
        if hasattr(self, 'controls'):
            # The controls _on_canvas_resize method will update controls_width
            self.controls._on_canvas_resize(event)
            # Update progress control with new controls width
            self.progress_control.set_controls_width(self.controls.controls_width)

        # Update progress bar positions
        self.progress_control.update_positions()

        # Calculate positions for volume control, accounting for utility controls
        progress_end_x = self.canvas.coords(self.line)[2]
        canvas_width = event.width
        utility_controls_width = self.controls.utility_width  # Width reserved for loop and add buttons

        # Ensure volume control doesn't overlap with utility controls
        max_volume_x = canvas_width - utility_controls_width - PROGRESS_BAR['volume_control_width'] - 20  # 20 for padding
        volume_x_start = min(progress_end_x + 40, max_volume_x)  # Add padding but don't exceed max position

        # Update volume control positions
        if hasattr(self, 'volume_control'):
            self.volume_control.update_positions(volume_x_start)

    def update_track_info(self, title=None, artist=None):
        """Update the track info display."""
        self.progress_control.update_track_info(title, artist)

    def clear_track_info(self):
        """Clear the track info display."""
        self.progress_control.clear_track_info()


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
            'Recently Added',
            'Recently Played',
            'Top 25 Most Played',
        ]

        style = ttk.Style()
        font_str = style.lookup('Treeview', 'font')
        if not font_str:
            font_str = 'TkDefaultFont'
        font = tkfont.nametofont(font_str)

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


class QueueView:
    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks
        self.setup_queue_view()

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

        self.queue.column('track', width=50, anchor='center')
        self.queue.column('title', width=300)
        self.queue.column('artist', width=200)
        self.queue.column('album', width=200)
        self.queue.column('year', width=100, anchor='center')

        self.queue.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.scrollbar.config(command=self.queue.yview)

        # Add bindings
        self.queue.bind('<Double-Button-1>', self.callbacks['play_selected'])
        self.queue.bind('<Delete>', self.callbacks['handle_delete'])
        self.queue.bind('<BackSpace>', self.callbacks['handle_delete'])
        self.queue.bind('<<TreeviewSelect>>', self.callbacks['on_song_select'])
        # Add select all keyboard shortcuts
        self.queue.bind('<Command-a>', self.select_all)  # macOS
        self.queue.bind('<Control-a>', self.select_all)  # Windows/Linux

        # Setup drag and drop
        self.queue.drop_target_register('DND_Files')
        self.queue.dnd_bind('<<Drop>>', self.callbacks['handle_drop'])

    def select_all(self, event=None):
        """Select all items in the queue."""
        self.queue.selection_set(self.queue.get_children())
        return "break"  # Prevent default handling


class MusicPlayer:
    def __init__(self, window: tk.Tk, theme_manager):
        self.window = window
        self.theme_manager = theme_manager
        self.setup_components()

    def setup_components(self):
        # Create player core first
        self.player_core = PlayerCore(self.db, self.queue_manager, self.queue_view)
        self.player_core.window = self.window  # Set window reference for thread-safe callbacks
