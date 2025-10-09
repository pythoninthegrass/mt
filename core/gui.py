import contextlib
import customtkinter as ctk
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
from utils.icons import load_icon


class PlayerControls:
    def __init__(self, canvas, command_callbacks, initial_loop_enabled=True, initial_shuffle_enabled=False):
        self.canvas = canvas
        self.callbacks = command_callbacks
        self.add_button = None
        self.loop_button = None
        self.shuffle_button = None
        self.favorite_button = None
        self.play_button = None
        self.loop_enabled = initial_loop_enabled
        self.shuffle_enabled = initial_shuffle_enabled
        self.favorite_enabled = False

        # Icon sizes - playback controls are larger than utility controls
        self.playback_icon_size = (35, 35)
        self.utility_icon_size = (23, 23)

        # Store icon references to prevent garbage collection
        self.icon_images = {}

        self.setup_playback_controls()
        self.setup_utility_controls()

        # Bind canvas resize after all buttons are created
        self.canvas.bind('<Configure>', self._on_canvas_resize)

    def setup_playback_controls(self):
        # Create playback controls directly on canvas
        x_position = 25
        # Calculate vertical center of canvas (accounting for button height)
        self.canvas.update_idletasks()
        canvas_height = self.canvas.winfo_height()
        y_position = (canvas_height - self.playback_icon_size[1]) // 2

        for action, symbol in [
            ('previous', BUTTON_SYMBOLS['prev']),
            ('play', BUTTON_SYMBOLS['play']),
            ('next', BUTTON_SYMBOLS['next']),
        ]:
            button = tk.Label(
                self.canvas,
                text=symbol,
                fg='#CCCCCC',  # Light gray for normal state
                bg="#000000",  # Pure black background
                font=('TkDefaultFont', 28)
            )
            button.place(x=x_position, y=y_position)

            # Bind click and hover events
            button.bind('<Button-1>', lambda e, a=action: self.callbacks[a]())
            button.bind('<Enter>', lambda e, b=button: b.configure(fg=THEME_CONFIG['colors']['primary']))
            button.bind('<Leave>', lambda e, b=button: b.configure(fg='#CCCCCC'))

            if action == 'play':
                self.play_button = button

            x_position += self.playback_icon_size[0] + 10  # Add spacing between buttons

        # Store the width for progress bar calculations
        self.controls_width = x_position + 15

    def setup_utility_controls(self):
        # Create utility controls directly on canvas
        # Wait for canvas to be ready
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Calculate vertical center of canvas (accounting for icon height)
        y_position = (canvas_height - self.utility_icon_size[1]) // 2

        try:
            # Load icons for utility controls
            # Add button (rightmost)
            add_normal = load_icon(BUTTON_SYMBOLS['add'], size=self.utility_icon_size, opacity=0.7)
            add_hover = load_icon(BUTTON_SYMBOLS['add'], size=self.utility_icon_size, opacity=1.0, tint_color=THEME_CONFIG['colors']['primary'])
            self.icon_images['add_normal'] = add_normal
            self.icon_images['add_hover'] = add_hover
        except Exception as e:
            print(f"Error loading add button icons: {e}")
            import traceback
            traceback.print_exc()
            raise

        self.add_button = tk.Label(
            self.canvas,
            image=add_normal,
            bg="#000000",  # Pure black background like MusicBee
        )
        self.add_button.place(x=canvas_width - 60, y=y_position)
        self.add_button.bind('<Button-1>', lambda e: self.callbacks['add']())
        self.add_button.bind('<Enter>', lambda e: self.add_button.configure(image=self.icon_images['add_hover']))
        self.add_button.bind('<Leave>', lambda e: self.add_button.configure(image=self.icon_images['add_normal']))

        # Loop button (to the left of add button) - 54px spacing (reduced by 10% from 60px)
        loop_normal = load_icon(BUTTON_SYMBOLS['loop'], size=self.utility_icon_size, opacity=0.7)
        loop_enabled_icon = load_icon(BUTTON_SYMBOLS['loop'], size=self.utility_icon_size, opacity=1.0, tint_color=COLORS['loop_enabled'])
        loop_disabled_icon = load_icon(BUTTON_SYMBOLS['loop'], size=self.utility_icon_size, opacity=0.5)
        loop_hover = load_icon(BUTTON_SYMBOLS['loop'], size=self.utility_icon_size, opacity=1.0, tint_color=THEME_CONFIG['colors']['primary'])
        self.icon_images['loop_normal'] = loop_normal
        self.icon_images['loop_enabled'] = loop_enabled_icon
        self.icon_images['loop_disabled'] = loop_disabled_icon
        self.icon_images['loop_hover'] = loop_hover

        self.loop_button = tk.Label(
            self.canvas,
            image=loop_enabled_icon if self.loop_enabled else loop_disabled_icon,
            bg="#000000",  # Pure black background like MusicBee
        )
        self.loop_button.place(x=canvas_width - 114, y=y_position)
        self.loop_button.bind('<Button-1>', lambda e: self.callbacks['loop']())
        self.loop_button.bind('<Enter>', lambda e: self.loop_button.configure(image=self.icon_images['loop_hover']))
        self.loop_button.bind(
            '<Leave>',
            lambda e: self.loop_button.configure(image=self.icon_images['loop_enabled'] if self.loop_enabled else self.icon_images['loop_disabled']),
        )

        # Shuffle button (to the left of loop button) - 54px spacing
        shuffle_normal = load_icon(BUTTON_SYMBOLS['shuffle'], size=self.utility_icon_size, opacity=0.7)
        shuffle_enabled_icon = load_icon(BUTTON_SYMBOLS['shuffle'], size=self.utility_icon_size, opacity=1.0, tint_color=COLORS['shuffle_enabled'])
        shuffle_disabled_icon = load_icon(BUTTON_SYMBOLS['shuffle'], size=self.utility_icon_size, opacity=0.5)
        shuffle_hover = load_icon(BUTTON_SYMBOLS['shuffle'], size=self.utility_icon_size, opacity=1.0, tint_color=THEME_CONFIG['colors']['primary'])
        self.icon_images['shuffle_normal'] = shuffle_normal
        self.icon_images['shuffle_enabled'] = shuffle_enabled_icon
        self.icon_images['shuffle_disabled'] = shuffle_disabled_icon
        self.icon_images['shuffle_hover'] = shuffle_hover

        self.shuffle_button = tk.Label(
            self.canvas,
            image=shuffle_enabled_icon if self.shuffle_enabled else shuffle_disabled_icon,
            bg="#000000",  # Pure black background like MusicBee
        )
        self.shuffle_button.place(x=canvas_width - 168, y=y_position)
        self.shuffle_button.bind('<Button-1>', lambda e: self.callbacks['shuffle']())
        self.shuffle_button.bind('<Enter>', lambda e: self.shuffle_button.configure(image=self.icon_images['shuffle_hover']))
        self.shuffle_button.bind(
            '<Leave>',
            lambda e: self.shuffle_button.configure(
                image=self.icon_images['shuffle_enabled'] if self.shuffle_enabled else self.icon_images['shuffle_disabled']
            ),
        )

        # Favorite button (to the left of shuffle button) - 54px spacing
        favorite_normal = load_icon(BUTTON_SYMBOLS['favorite_border'], size=self.utility_icon_size, opacity=0.7)
        favorite_filled = load_icon(BUTTON_SYMBOLS['favorite'], size=self.utility_icon_size, opacity=1.0, tint_color=COLORS['loop_enabled'])
        favorite_hover = load_icon(BUTTON_SYMBOLS['favorite_border'], size=self.utility_icon_size, opacity=1.0, tint_color=THEME_CONFIG['colors']['primary'])
        favorite_filled_hover = load_icon(BUTTON_SYMBOLS['favorite'], size=self.utility_icon_size, opacity=1.0, tint_color=THEME_CONFIG['colors']['primary'])
        self.icon_images['favorite_normal'] = favorite_normal
        self.icon_images['favorite_filled'] = favorite_filled
        self.icon_images['favorite_hover'] = favorite_hover
        self.icon_images['favorite_filled_hover'] = favorite_filled_hover

        self.favorite_button = tk.Label(
            self.canvas,
            image=favorite_normal,
            bg="#000000",  # Pure black background like MusicBee
        )
        self.favorite_button.place(x=canvas_width - 222, y=y_position)
        self.favorite_button.bind('<Button-1>', lambda e: self.callbacks.get('favorite', lambda: None)())
        self.favorite_button.bind('<Enter>', lambda e: self.favorite_button.configure(
            image=self.icon_images['favorite_filled_hover'] if self.favorite_enabled else self.icon_images['favorite_hover']
        ))
        self.favorite_button.bind('<Leave>', lambda e: self.favorite_button.configure(
            image=self.icon_images['favorite_filled'] if self.favorite_enabled else self.icon_images['favorite_normal']
        ))

        # Ensure buttons are on top of canvas elements
        self.favorite_button.lift()
        self.shuffle_button.lift()
        self.loop_button.lift()
        self.add_button.lift()

        # Store the width for progress bar calculations
        self.utility_width = 222

    def _on_canvas_resize(self, event):
        """Recenter the buttons vertically and reposition all controls when canvas is resized."""
        if not all([self.add_button, self.loop_button, self.shuffle_button, self.favorite_button, self.play_button]):
            return

        # Calculate new y position (centered vertically - use larger playback icon size for consistency)
        new_y = (event.height - self.playback_icon_size[1]) // 2

        # Calculate positions relative to canvas width
        canvas_width = event.width

        # Utility controls are positioned from the right with 54px spacing (reduced by 10%)
        # Add button at right edge minus padding (unchanged)
        add_x = canvas_width - 60
        self.add_button.place(x=add_x, y=new_y)

        # Loop button to the left of add button - 54px spacing
        loop_x = canvas_width - 114
        self.loop_button.place(x=loop_x, y=new_y)

        # Shuffle button to the left of loop button - 54px spacing
        shuffle_x = canvas_width - 168
        self.shuffle_button.place(x=shuffle_x, y=new_y)

        # Favorite button to the left of shuffle button - 54px spacing
        favorite_x = canvas_width - 222
        self.favorite_button.place(x=favorite_x, y=new_y)

        # Playback controls are positioned from the left, maintaining relative spacing
        # Find playback control buttons (they are tk.Label widgets that are not utility buttons)
        playback_buttons = []
        for child in self.canvas.winfo_children():
            if isinstance(child, tk.Label) and child not in [self.add_button, self.loop_button, self.shuffle_button, self.favorite_button]:
                playback_buttons.append(child)

        # Position playback controls with the same spacing as initial setup
        x_position = 10  # Same as initial setup
        for button in playback_buttons:
            button.place(x=x_position, y=new_y)
            # Use the same spacing calculation as setup_playback_controls
            x_position += button.winfo_reqwidth() + 5

        # Update controls width for progress bar calculations
        self.controls_width = x_position + 15  # Same as initial setup  # Same as initial setup

    def update_loop_button_color(self, loop_enabled):
        """Update loop button icon based on loop state."""
        self.loop_enabled = loop_enabled  # Update the internal state
        self.loop_button.configure(image=self.icon_images['loop_enabled'] if loop_enabled else self.icon_images['loop_disabled'])

    def update_shuffle_button_color(self, shuffle_enabled):
        """Update shuffle button icon based on shuffle state."""
        self.shuffle_enabled = shuffle_enabled  # Update the internal state
        self.shuffle_button.configure(image=self.icon_images['shuffle_enabled'] if shuffle_enabled else self.icon_images['shuffle_disabled'])

    def update_favorite_button(self, is_favorite):
        """Update favorite button icon based on favorite state."""
        self.favorite_enabled = is_favorite
        if is_favorite:
            self.favorite_button.configure(image=self.icon_images['favorite_filled'])
        else:
            self.favorite_button.configure(image=self.icon_images['favorite_normal'])

    def update_play_button(self, is_playing):
        """Update play button to show play or pause state."""
        if is_playing:
            # When playing, show pause symbol
            self.play_button.configure(
                text=BUTTON_SYMBOLS['pause'],
                fg='#FFFFFF'  # Bright white when active/playing
            )
        else:
            # When paused/stopped, show play symbol
            self.play_button.configure(
                text=BUTTON_SYMBOLS['play'],
                fg='#CCCCCC'  # Light gray when paused
            )


class ProgressBar:
    def __init__(self, window, progress_frame, callbacks, initial_loop_enabled=True, initial_shuffle_enabled=False):
        self.window = window
        self.progress_frame = progress_frame
        self.callbacks = callbacks
        self.initial_loop_enabled = initial_loop_enabled
        self.initial_shuffle_enabled = initial_shuffle_enabled
        self.setup_progress_bar()
        self.setup_volume_control()

    def setup_progress_bar(self):
        # Create canvas for custom progress bar
        self.canvas = tk.Canvas(
            self.progress_frame,
            height=PROGRESS_BAR['canvas_height'],
            background="#000000",  # Pure black like search bar
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.X)

        # Create controls with initial loop and shuffle state
        self.controls = PlayerControls(
            self.canvas,
            self.callbacks,
            initial_loop_enabled=self.initial_loop_enabled,
            initial_shuffle_enabled=self.initial_shuffle_enabled,
        )
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
        # Wait for canvas to be ready and get current dimensions
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Calculate positions with proper spacing
        progress_end_x = self.canvas.coords(self.line)[2]       # End of progress line
        utility_controls_width = self.controls.utility_width    # Width reserved for loop and add buttons

        # Position volume control relative to shuffle button position (leftmost utility control)
        shuffle_button_x = canvas_width - 180  # Same positioning as utility controls
        volume_end_x = shuffle_button_x - 60  # Fixed spacing before shuffle button

        # Calculate volume start position
        volume_x_start = progress_end_x + 45  # Fixed spacing after progress bar

        # Calculate available space for volume slider
        available_space = volume_end_x - volume_x_start
        volume_slider_length = max(80, min(120, available_space - 30))  # 30 for volume icon, constrain between 80-120px

        # Calculate centered y position to match utility controls, lowered by 15%
        # Utility controls are centered at (canvas_height - utility_icon_size[1]) // 2 + utility_icon_size[1] // 2
        volume_bar_y = int(canvas_height // 2 * 1.10)  # Center of canvas, lowered by 10%

        # Create volume control
        self.volume_control = VolumeControl(
            self.canvas,
            volume_bar_y,
            self.circle_radius,
            BUTTON_SYMBOLS,
            THEME_CONFIG,
            {'volume_change': self.callbacks['volume_change']},
        )
        self.volume_control.setup_volume_control(volume_x_start, volume_slider_length)

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
        canvas_height = event.height
        utility_controls_width = self.controls.utility_width  # Width reserved for loop and add buttons

        # Position volume control relative to shuffle button position (leftmost utility control)
        shuffle_button_x = canvas_width - 180  # Same positioning as utility controls
        volume_end_x = shuffle_button_x - 60  # Fixed spacing before shuffle button

        # Calculate volume start position
        volume_x_start = progress_end_x + 45  # Fixed spacing after progress bar

        # Calculate available space for volume slider
        available_space = volume_end_x - volume_x_start
        volume_slider_length = max(80, min(120, available_space - 30))  # 30 for volume icon, constrain between 80-120px

        # Update volume control positions with centered y position
        if hasattr(self, 'volume_control'):
            # Update the bar_y to keep it centered
            volume_bar_y = canvas_height // 2
            self.volume_control.bar_y = volume_bar_y
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
        self.queue.bind('<Double-Button-1>', self.callbacks['play_selected'])
        self.queue.bind('<Delete>', self.callbacks['handle_delete'])
        self.queue.bind('<BackSpace>', self.callbacks['handle_delete'])
        self.queue.bind('<<TreeviewSelect>>', self.callbacks['on_song_select'])
        # Add select all keyboard shortcuts
        self.queue.bind('<Command-a>', self.select_all)  # macOS
        self.queue.bind('<Control-a>', self.select_all)  # Windows/Linux

        # Add column resize handling with periodic check
        self._last_column_widths = self.get_column_widths()
        self._column_check_timer = None
        # Don't start periodic check yet - will be started after preferences are loaded

        # Bind to Map event to apply saved preferences when widget becomes visible
        self.queue.bind('<Map>', self._on_treeview_mapped)

    def set_track_column_header(self, text: str):
        """Update the track column header text."""
        self.queue.heading('track', text=text)

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
        from core.logging import library_logger, log_player_action
        from eliot import start_action

        # Ignore modifier keys and special keys - let them use default behavior
        if event.keysym in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R',
                            'Alt_L', 'Alt_R', 'Meta_L', 'Meta_R', 'Super_L', 'Super_R',
                            'Up', 'Down', 'Left', 'Right', 'Return', 'Escape',
                            'Tab', 'BackSpace', 'Delete', 'Home', 'End',
                            'Page_Up', 'Page_Down'):
            return None  # Let default behavior handle these keys

        # Ignore if modifiers are pressed (Ctrl, Alt, Command)
        if event.state & 0x4:   # Control
            return None
        if event.state & 0x8:   # Alt
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
            self._type_timer = self.queue.after(
                self._type_timeout,
                self._reset_type_buffer
            )

        return "break"  # Prevent default handling

    def _jump_to_artist(self, search_text: str):
        """Jump to first artist matching the typed text."""
        from core.logging import library_logger, log_player_action

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

            if artist.startswith(search_text):
                # Select and scroll to the item
                self.queue.selection_set(item_id)
                self.queue.see(item_id)
                self.queue.focus(item_id)

                log_player_action(
                    "type_to_jump",
                    trigger_source="keyboard",
                    search_text=search_text,
                    matched_artist=artist,
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
            self.stoplight_buttons = StoplightButtons(window, self.search_frame, integrated=True)

        # Create inner frame right-justified but expanded left to Album column
        self.inner_frame = ctk.CTkFrame(self.search_frame, fg_color="transparent")
        self.inner_frame.pack(side=tk.RIGHT, padx=10, pady=5)

        # Search icon label - using Unicode magnifying glass instead of emoji
        self.search_icon = ctk.CTkLabel(
            self.inner_frame,
            text="⌕",  # Unicode magnifying glass (U+2315)
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


class StatusBar:
    def __init__(self, parent, library_manager):
        self.parent = parent
        self.library_manager = library_manager
        self.setup_status_bar()

    def setup_status_bar(self):
        """Create status bar spanning entire bottom pane."""
        from config import COLORS

        # Create status bar container - continuous bar across full width
        self.status_bar = ctk.CTkFrame(
            self.parent,
            height=20,
            corner_radius=0,
            fg_color=COLORS['status_bar_bg'],  # #272931
            border_width=0,
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)
        self.status_bar.pack_propagate(False)

        # Status label with library statistics - right-justified
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Loading library statistics...",
            font=("SF Pro Display", 12),
            text_color="#CCCCCC",  # Light gray text
            anchor="e",  # Right-aligned text
        )
        self.status_label.pack(side=tk.RIGHT, padx=10, pady=5)

        # Initial statistics load
        self.update_statistics()

    def format_file_size(self, size_bytes):
        """Convert bytes to human readable format (GB)."""
        if size_bytes == 0:
            return "0.0 GB"

        gb_size = size_bytes / (1024**3)
        return f"{gb_size:.1f} GB"

    def format_duration(self, total_seconds):
        """Convert total seconds to NNd hh:mm format."""
        if total_seconds <= 0:
            return "0d 00:00"

        days = int(total_seconds // 86400)  # 86400 seconds in a day
        remaining_seconds = total_seconds % 86400
        hours = int(remaining_seconds // 3600)
        minutes = int((remaining_seconds % 3600) // 60)

        return f"{days}d {hours:02d}:{minutes:02d}"

    def format_file_count(self, count):
        """Format file count with commas for readability."""
        return f"{count:,}"

    def get_library_statistics(self):
        """Get comprehensive library statistics."""
        stats = self.library_manager.get_library_statistics()
        return {
            'file_count': stats.get('file_count', 0),
            'total_size_bytes': stats.get('total_size_bytes', 0),
            'total_duration_seconds': stats.get('total_duration_seconds', 0),
        }

    def update_statistics(self):
        """Update the status bar with current library statistics."""
        try:
            stats = self.get_library_statistics()

            file_count_str = self.format_file_count(stats['file_count'])
            size_str = self.format_file_size(stats['total_size_bytes'])
            duration_str = self.format_duration(stats['total_duration_seconds'])

            status_text = f"{file_count_str} files{'':<5}{size_str}{'':<5}{duration_str}"
            self.status_label.configure(text=status_text)

        except Exception as e:
            self.status_label.configure(text="Unable to load library statistics")

    def refresh_statistics(self):
        """Manually refresh the statistics (useful after library scan)."""
        self.update_statistics()


class MusicPlayer:
    def __init__(self, window: tk.Tk, theme_manager):
        self.window = window
        self.theme_manager = theme_manager
        self.setup_components()

    def setup_components(self):
        # Create player core first
        self.player_core = PlayerCore(self.db, self.queue_manager, self.queue_view)
        self.player_core.window = self.window  # Set window reference for thread-safe callbacks
