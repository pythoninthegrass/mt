import json
import tkinter as tk
import tkinter.font as tkfont
import ttkbootstrap as ttk
from decouple import config

# Theme Configuration
THEME_CONFIG_FILE = 'themes.json'
DEFAULT_THEME = 'spotify'
ACTIVE_THEME = config('MT_THEME', default=DEFAULT_THEME)

# Load theme data
with open(THEME_CONFIG_FILE) as f:
    THEMES_DATA = json.load(f)
    THEME_CONFIG = next(theme for theme in THEMES_DATA['themes'] if ACTIVE_THEME in theme)[ACTIVE_THEME]

# Window Configuration
WINDOW_SIZE = "1280x720"
WINDOW_TITLE = "mt"

# Button Configuration
BUTTON_STYLE = {
    'width': 6,
    'padding': 1.0,
    'font': ('TkDefaultFont', 25),
}

# Button Symbols
BUTTON_SYMBOLS = {
    'play': '⏯',
    'pause': '⏸',
    'prev': '⏮',
    'next': '⏭',
    'add': '+',
    'loop': '⟳',
}

# Progress Bar Configuration
PROGRESS_BAR = {
    'frame_height': 80,
    'canvas_height': 70,
    'bar_y': 40,
    'circle_radius': 6,
    'line_color': THEME_CONFIG['colors']['secondary'],
    'line_width': 2,
    'circle_fill': THEME_CONFIG['colors']['primary'],
    'circle_active_fill': THEME_CONFIG['colors']['active'],
    'time_label_y': 15,
    'frame_padding': (0, 20),
    'frame_side_padding': 10,
    'controls_y': 40,
    'button_spacing': 2,
}

# Listbox Configuration
LISTBOX_CONFIG = {
    'width': 50,
    'selectmode': 'extended',
    'selectbackground': THEME_CONFIG['colors']['selectbg'],
    'selectforeground': THEME_CONFIG['colors']['selectfg'],
    'activestyle': 'none',
    'padding': (0, 15),  # (top, bottom)
    'background': THEME_CONFIG['colors']['bg'],
    'foreground': THEME_CONFIG['colors']['fg'],
}

# Color Configuration
COLORS = {
    'loop_enabled': THEME_CONFIG['colors']['primary'],
    'loop_disabled': THEME_CONFIG['colors']['secondary'],
    'alternate_row_colors': [
        THEME_CONFIG['colors']['bg'],
        THEME_CONFIG['colors']['selectbg']
    ],
}

def setup_theme(root):
    """Configure the application theme and styles"""
    style = ttk.Style(theme='darkly')  # Start with darkly as base

    # Apply theme colors from config
    style.configure('TButton',
                   background=THEME_CONFIG['colors']['bg'],
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
                   font=BUTTON_STYLE['font'],
                   padding=BUTTON_STYLE['padding'])

    style.configure('Loop.Controls.TButton',
                   background=THEME_CONFIG['colors']['bg'],
                   foreground=THEME_CONFIG['colors']['fg'],
                   borderwidth=0,
                   relief='flat',
                   focuscolor='',           # Remove focus border
                   highlightthickness=0,    # Remove highlight border
                   font=BUTTON_STYLE['font'],
                   padding=BUTTON_STYLE['padding'])

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
    def __init__(self, canvas, command_callbacks):
        self.canvas = canvas
        self.callbacks = command_callbacks
        self.setup_playback_controls()
        self.setup_utility_controls()

    def setup_playback_controls(self):
        # Create buttons frame within canvas for playback controls (prev, play, next)
        self.button_frame = ttk.Frame(self.canvas)
        self.button_frame.place(x=10, y=PROGRESS_BAR['controls_y'] - 15)

        for action, symbol in [
            ('previous', BUTTON_SYMBOLS['prev']),
            ('play', BUTTON_SYMBOLS['play']),
            ('next', BUTTON_SYMBOLS['next']),
        ]:
            button = ttk.Button(
                self.button_frame,
                text=symbol,
                style='Controls.TButton',
                command=self.callbacks[action],
                width=3,
            )
            button.pack(side=tk.LEFT, padx=2)

            if action == 'play':
                self.play_button = button

        # Update the button frame after all buttons are packed to get its true width
        self.button_frame.update()
        # Store the width for progress bar calculations
        self.controls_width = self.button_frame.winfo_width() + 20

    def setup_utility_controls(self):
        # Create buttons frame within canvas for utility controls (loop, add)
        self.utility_frame = ttk.Frame(self.canvas)
        self.utility_frame.place(
            x=self.canvas.winfo_width() - 150, y=PROGRESS_BAR['controls_y'] - 15
        )

        for action, symbol in [
            ('loop', BUTTON_SYMBOLS['loop']),
            ('add', BUTTON_SYMBOLS['add']),
        ]:
            button = ttk.Button(
                self.utility_frame,
                text=symbol,
                style='Loop.Controls.TButton'
                if action == 'loop'
                else 'Controls.TButton',
                command=self.callbacks[action],
                width=3,
            )
            button.pack(side=tk.LEFT, padx=2)

            if action == 'loop':
                self.loop_button = button

class ProgressBar:
    def __init__(self, window, progress_frame, callbacks):
        self.window = window
        self.progress_frame = progress_frame
        self.callbacks = callbacks
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

        # Create controls
        self.controls = PlayerControls(self.canvas, self.callbacks)
        self.controls_width = self.controls.controls_width

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
        self.canvas.bind('<Configure>', self.callbacks['on_resize'])

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
