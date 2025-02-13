import os
from pathlib import Path

# Audio Configuration
AUDIO_EXTENSIONS = {
    '.m4a', '.mp3', '.wav', '.ogg', '.wma', '.flac', '.aac',
    '.ac3', '.dts', '.mpc', '.ape', '.ra', '.mid', '.midi',
    '.mod', '.3gp', '.aif', '.aiff', '.wv', '.tta', '.m4b',
    '.m4r', '.mp1', '.mp2'
}

# UI Configuration
WINDOW_SIZE = "640x720"
WINDOW_TITLE = "mt"
BUTTON_STYLE = {
    'width': 5,
    'height': 2,
    'font': ('TkDefaultFont', 18, 'bold'),
    'padx': 8,
    'pady': 5,
}

# Progress Bar Configuration
PROGRESS_BAR = {
    'frame_height': 60,
    'canvas_height': 50,
    'bar_y': 20,  # Vertical center of the canvas
    'circle_radius': 6,
    'line_color': 'gray',
    'line_width': 2,
    'circle_fill': 'blue',
    'circle_active_fill': 'lightblue',
    'time_label_y': 45,
    'frame_padding': (0, 20),  # (top, bottom)
    'frame_side_padding': 10,  # left/right padding
}

# Listbox Configuration
LISTBOX_CONFIG = {
    'width': 50,
    'selectmode': 'extended',
    'selectbackground': 'lightblue',
    'activestyle': 'none',
    'padding': (0, 15),  # (top, bottom)
}

# Color Configuration
COLORS = {
    'loop_enabled': 'green',
    'loop_disabled': 'black',
    'alternate_row_colors': ['white', '#f0f0f0'],
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

# Database Configuration
DB_NAME = 'mt.db'
DB_TABLES = {
    'queue': '''
        CREATE TABLE IF NOT EXISTS queue
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         filepath TEXT NOT NULL)
    ''',
    'settings': '''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    '''
}

# File System
MAX_SCAN_DEPTH = 5

# Player Configuration
PROGRESS_UPDATE_INTERVAL = 100  # milliseconds
DEFAULT_LOOP_ENABLED = True
