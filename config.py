import json
import os
from decouple import config
from pathlib import Path

# Theme Configuration
THEME_CONFIG_FILE = 'themes.json'
DEFAULT_THEME = 'spotify'
ACTIVE_THEME = config('MT_THEME', default=DEFAULT_THEME)

# Load theme data
with open(THEME_CONFIG_FILE) as f:
    THEMES_DATA = json.load(f)
    THEME_CONFIG = next(theme for theme in THEMES_DATA['themes'] if ACTIVE_THEME in theme)[ACTIVE_THEME]

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
    'line_color': THEME_CONFIG['colors']['secondary'],
    'line_width': 2,
    'circle_fill': THEME_CONFIG['colors']['primary'],
    'circle_active_fill': THEME_CONFIG['colors']['active'],
    'time_label_y': 45,
    'frame_padding': (0, 20),  # (top, bottom)
    'frame_side_padding': 10,  # left/right padding
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
    'loop_enabled': '#00b7c3',       # Updated to teal
    'loop_disabled': '#686868',      # Updated to theme secondary color
    'alternate_row_colors': [
        THEME_CONFIG['colors']['bg'],
        THEME_CONFIG['colors']['selectbg']
    ],
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
