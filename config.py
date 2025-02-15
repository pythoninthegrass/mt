import json
import os
from decouple import config
from pathlib import Path

# Reload app during development
RELOAD = config('MT_RELOAD', default=False, cast=bool)

# Database Configuration
DB_NAME = 'mt.db'

# Audio Configuration
AUDIO_EXTENSIONS = {
    '.m4a', '.mp3', '.wav', '.ogg', '.wma', '.flac', '.aac',
    '.ac3', '.dts', '.mpc', '.ape', '.ra', '.mid', '.midi',
    '.mod', '.3gp', '.aif', '.aiff', '.wv', '.tta', '.m4b',
    '.m4r', '.mp1', '.mp2'
}

# Window Configuration
WINDOW_SIZE = "1280x720"
WINDOW_TITLE = "mt"

# Button Configuration
BUTTON_STYLE = {
    'width': 3,
    'font': ('TkDefaultFont', 30),
}

# Button Symbols
BUTTON_SYMBOLS = {
    'play': '▶',
    'pause': '⏸',
    'prev': '⏮',
    'next': '⏭',
    'add': '+',
    'loop': '⟳',
}

# Theme Configuration
THEME_CONFIG_FILE = Path('themes.json')
DEFAULT_THEME = 'spotify'
ACTIVE_THEME = config('MT_THEME', default=DEFAULT_THEME)

# Load theme data
with open(THEME_CONFIG_FILE) as f:
    THEMES_DATA = json.load(f)
    THEME_CONFIG = next(
        theme for theme in THEMES_DATA['themes'] if ACTIVE_THEME in theme
    )[ACTIVE_THEME]

# Progress Bar Configuration
PROGRESS_BAR = {
    'frame_height': 80,
    'canvas_height': 70,
    'bar_y': 50,
    'circle_radius': 6,
    'line_color': THEME_CONFIG['colors']['secondary'],
    'line_width': 2,
    'circle_fill': THEME_CONFIG['colors']['primary'],
    'circle_active_fill': THEME_CONFIG['colors']['active'],
    'time_label_y': 30,
    'track_info_y': 30,
    'track_info_x': None,
    'frame_padding': (0, 20),
    'frame_side_padding': 10,
    'controls_y': 50,
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
        THEME_CONFIG['colors']['selectbg'],
    ],
}

# File System
MAX_SCAN_DEPTH = 5

# Player Configuration
PROGRESS_UPDATE_INTERVAL = 100  # milliseconds
DEFAULT_LOOP_ENABLED = True
