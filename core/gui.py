import json
import os
import tkinter as tk
import tkinter.font as tkfont
import ttkbootstrap as ttk
from config import (
    BUTTON_STYLE,
    BUTTON_SYMBOLS,
    COLORS,
    LISTBOX_CONFIG,
    PROGRESS_BAR,
    THEME_CONFIG,
)
from core.controls import PlayerCore
from decouple import config
from pathlib import Path


def setup_theme(root):
    """Configure the application theme and styles"""
    style = ttk.Style(theme='darkly')  # Start with darkly as base

    # Configure root window and base theme
    root.configure(background=THEME_CONFIG['colors']['bg'])
    root.option_add('*Background', THEME_CONFIG['colors']['bg'])
    root.option_add('*Foreground', THEME_CONFIG['colors']['fg'])

    # Apply theme colors from config
    style.configure('.',
                   background=THEME_CONFIG['colors']['bg'],
                   foreground=THEME_CONFIG['colors']['fg'])

    # Configure all ttk widgets to use the same background
    for widget in ['TFrame', 'TPanedwindow', 'Treeview', 'TButton', 'TLabel']:
        style.configure(widget,
                      background=THEME_CONFIG['colors']['bg'],
                      fieldbackground=THEME_CONFIG['colors']['bg'])

    style.configure('TButton',
                   foreground=THEME_CONFIG['colors']['fg'],
                   borderwidth=0,
                   relief='flat',
                   focuscolor='',           # Remove focus border
                   highlightthickness=0,    # Remove highlight border
                   font=BUTTON_STYLE['font'])

    # Configure specific styles for control buttons
    style.configure('Controls.TButton',
                   background=THEME_CONFIG['colors']['bg'],
                   foreground=THEME_CONFIG['colors']['fg'],
                   borderwidth=0,
                   relief='flat',
                   focuscolor='',           # Remove focus border
                   highlightthickness=0,    # Remove highlight border
                   font=BUTTON_STYLE['font'])

    style.configure('Loop.Controls.TButton',
                   background=THEME_CONFIG['colors']['bg'],
                   foreground=THEME_CONFIG['colors']['fg'],
                   borderwidth=0,
                   relief='flat',
                   focuscolor='',           # Remove focus border
                   highlightthickness=0,    # Remove highlight border
                   font=BUTTON_STYLE['font'])

    style.map('Controls.TButton',
             background=[('active', THEME_CONFIG['colors']['bg'])],
             foreground=[('active', THEME_CONFIG['colors']['primary'])])

    style.map('Loop.Controls.TButton',
             background=[('active', THEME_CONFIG['colors']['bg'])],
             foreground=[('active', THEME_CONFIG['colors']['primary'])])

    style.configure('TFrame', background=THEME_CONFIG['colors']['bg'])
    style.configure('TLabel', background=THEME_CONFIG['colors']['bg'], foreground=THEME_CONFIG['colors']['fg'])
    style.configure('Vertical.TScrollbar',
                   background=THEME_CONFIG['colors']['bg'],
                   troughcolor=THEME_CONFIG['colors']['dark'],
                   arrowcolor=THEME_CONFIG['colors']['fg'])

    # Configure Treeview style
    style.configure('Treeview',
                   background=THEME_CONFIG['colors']['bg'],
                   foreground=THEME_CONFIG['colors']['fg'],
                   fieldbackground=THEME_CONFIG['colors']['bg'],
                   borderwidth=0,
                   relief='flat')

    style.configure('Treeview.Heading',
                   background=THEME_CONFIG['colors']['bg'],
                   foreground=THEME_CONFIG['colors']['fg'],
                   relief='flat',
                   borderwidth=0)

    style.map('Treeview.Heading',
             background=[('active', THEME_CONFIG['colors']['bg'])],
             foreground=[('active', THEME_CONFIG['colors']['primary'])])

    style.map('Treeview',
             background=[('selected', THEME_CONFIG['colors']['selectbg'])],
             foreground=[('selected', THEME_CONFIG['colors']['selectfg'])])

    # Update progress bar colors
    PROGRESS_BAR.update({
        'line_color': THEME_CONFIG['colors']['secondary'],
        'circle_fill': THEME_CONFIG['colors']['primary'],
        'circle_active_fill': THEME_CONFIG['colors']['active']
    })

    # Update listbox colors
    LISTBOX_CONFIG.update({
        'selectbackground': THEME_CONFIG['colors']['selectbg'],
        'selectforeground': THEME_CONFIG['colors']['selectfg'],
        'background': THEME_CONFIG['colors']['bg'],
        'foreground': THEME_CONFIG['colors']['fg']
    })

    # Update colors
    COLORS.update({
        'loop_enabled': THEME_CONFIG['colors']['primary'],
        'loop_disabled': THEME_CONFIG['colors']['secondary'],
        'alternate_row_colors': [THEME_CONFIG['colors']['bg'], THEME_CONFIG['colors']['selectbg']]
    })

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
                bg=THEME_CONFIG['colors']['bg']
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
            bg=THEME_CONFIG['colors']['bg']
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
            bg=THEME_CONFIG['colors']['bg']
        )
        self.loop_button.place(x=canvas_width - 120, y=y_position)
        self.loop_button.bind('<Button-1>', lambda e: self.callbacks['loop']())
        self.loop_button.bind('<Enter>', lambda e: self.loop_button.configure(fg=THEME_CONFIG['colors']['primary']))
        self.loop_button.bind('<Leave>', lambda e: self.loop_button.configure(
            fg=COLORS['loop_enabled'] if self.loop_enabled else COLORS['loop_disabled']
        ))

        # Force update loop button color after creation
        self.update_loop_button_color(self.loop_enabled)

        # Store the width for progress bar calculations
        self.utility_width = 120

    def _on_canvas_resize(self, event):
        """Recenter the buttons vertically and reposition utility controls when canvas is resized."""
        if not all([self.add_button, self.loop_button]):
            return

        # Update all button positions
        for button in self.canvas.winfo_children():
            if isinstance(button, tk.Label):
                # Calculate new y position
                new_y = (event.height - button.winfo_reqheight()) // 2

                # For utility controls, update x position from right
                if button == self.add_button:
                    new_x = event.width - 60
                    button.place(x=new_x, y=new_y)
                elif button == self.loop_button:
                    new_x = event.width - 120
                    button.place(x=new_x, y=new_y)
                else:
                    # For playback controls, keep x position
                    button.place(y=new_y)

    def update_loop_button_color(self, loop_enabled):
        """Update loop button color based on loop state."""
        self.loop_enabled = loop_enabled  # Update the internal state
        self.loop_button.configure(
            fg=COLORS['loop_enabled'] if loop_enabled else COLORS['loop_disabled']
        )

class ProgressBar:
    def __init__(self, window, progress_frame, callbacks, initial_loop_enabled=True):
        self.window = window
        self.progress_frame = progress_frame
        self.callbacks = callbacks
        self.initial_loop_enabled = initial_loop_enabled
        self.setup_progress_bar()

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

        # Create track info text - positioned above progress line
        self.track_info = self.canvas.create_text(
            self.controls_width,  # Align with start of progress line
            PROGRESS_BAR['track_info_y'],
            text="",  # Initialize with empty text
            fill=THEME_CONFIG['colors']['fg'],
            anchor=tk.W,
        )

        # Create time labels
        self.time_text = self.canvas.create_text(
            self.canvas.winfo_width() - 160,
            PROGRESS_BAR['time_label_y'],
            text="00:00 / 00:00",
            fill=THEME_CONFIG['colors']['fg'],
            anchor=tk.E,
        )

        # Create progress bar line
        self.bar_y = PROGRESS_BAR['bar_y']
        self.line = self.canvas.create_line(
            self.controls_width,
            self.bar_y,
            self.canvas.winfo_width() - 160,
            self.bar_y,
            fill=PROGRESS_BAR['line_color'],
            width=PROGRESS_BAR['line_width'],
        )

        # Create progress circle
        self.circle_radius = PROGRESS_BAR['circle_radius']
        self.progress_circle = self.canvas.create_oval(
            self.controls_width - self.circle_radius,
            self.bar_y - self.circle_radius,
            self.controls_width + self.circle_radius,
            self.bar_y + self.circle_radius,
            fill=PROGRESS_BAR['circle_fill'],
            outline="",
        )

        # Bind events
        self.dragging = False
        self.last_drag_time = 0
        self.canvas.tag_bind(self.progress_circle, '<Button-1>', self.callbacks['start_drag'])
        self.canvas.tag_bind(self.progress_circle, '<B1-Motion>', self.callbacks['drag'])
        self.canvas.tag_bind(self.progress_circle, '<ButtonRelease-1>', self.callbacks['end_drag'])
        self.canvas.bind('<Button-1>', self.callbacks['click_progress'])
        self.canvas.bind('<Configure>', self.on_resize)

    def on_resize(self, event):
        """Handle window resize."""
        # Update progress line
        self.canvas.coords(
            self.line,
            self.controls_width,
            self.bar_y,
            event.width - 160,
            self.bar_y,
        )

        # Update time text position
        self.canvas.coords(
            self.time_text,
            event.width - 160,
            PROGRESS_BAR['time_label_y'],
        )

        # Update track info position
        self.canvas.coords(
            self.track_info,
            self.controls_width,
            PROGRESS_BAR['track_info_y'],
        )

    def update_track_info(self, title=None, artist=None):
        """Update the track info display."""
        if title and artist:
            track_info = f"{artist} - {title}"  # Display as "Artist - Title"
        else:
            track_info = ""
        self.canvas.itemconfig(self.track_info, text=track_info)

    def clear_track_info(self):
        """Clear the track info display."""
        self.canvas.itemconfig(self.track_info, text="")

class LibraryView:
    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks
        self.setup_library_view()

    def setup_library_view(self):
        # Create treeview for library/playlists
        self.library_tree = ttk.Treeview(
            self.parent, show='tree', selectmode='browse'
        )
        self.library_tree.pack(expand=True, fill=tk.BOTH)

        # Library section
        library_id = self.library_tree.insert('', 'end', text='Library', open=True)
        music_item = self.library_tree.insert(library_id, 'end', text='Music', tags=('music',))
        self.library_tree.insert(
            library_id, 'end', text='Now Playing', tags=('now_playing',)
        )

        # Playlists section
        playlists_id = self.library_tree.insert('', 'end', text='Playlists', open=True)
        self.library_tree.insert(
            playlists_id, 'end', text='Recently Added', tags=('recent_added',)
        )
        self.library_tree.insert(
            playlists_id, 'end', text='Recently Played', tags=('recent_played',)
        )
        self.library_tree.insert(
            playlists_id, 'end', text='Top 25 Most Played', tags=('top_played',)
        )

        # Select Music by default
        self.library_tree.selection_set(music_item)
        self.library_tree.see(music_item)
        # Trigger the selection event to load the library
        self.library_tree.event_generate('<<TreeviewSelect>>')

        # Calculate optimal width
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

        total_width = (
            text_width
            + (indent_width * max_indent_level)
            + icon_width
            + side_padding
        )

        pane_width = total_width + 40

        # Configure width
        self.parent.configure(width=pane_width)
        self.parent.pack_propagate(False)

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
        )

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

        # Setup drag and drop
        self.queue.drop_target_register('DND_Files')
        self.queue.dnd_bind('<<Drop>>', self.callbacks['handle_drop'])

class MusicPlayer:
    def __init__(self, window: tk.Tk, theme_manager):
        self.window = window
        self.theme_manager = theme_manager
        self.setup_components()

    def setup_components(self):
        # Create player core first
        self.player_core = PlayerCore(self.db, self.queue_manager, self.queue_view)
        self.player_core.window = self.window  # Set window reference for thread-safe callbacks

        # ... existing code ...
