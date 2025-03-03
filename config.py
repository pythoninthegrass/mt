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
WINDOW_SIZE = "1366x768"
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
    'volume': '🔊',
}

# Theme Configuration
THEME_CONFIG_FILE = Path('themes.json')
DEFAULT_THEME = "metro-teal"
ACTIVE_THEME = config('MT_THEME', default=DEFAULT_THEME)

# Load theme data
with open(THEME_CONFIG_FILE) as f:
    THEMES_DATA = json.load(f)
    # Find the theme dictionary containing our desired theme
    theme_dict = None
    for theme_data in THEMES_DATA['themes']:
        if ACTIVE_THEME in theme_data:
            theme_dict = theme_data[ACTIVE_THEME]
            break

    # If theme not found, fallback to the first available theme
    if theme_dict is None and THEMES_DATA['themes']:
        first_theme_name = list(THEMES_DATA['themes'][0].keys())[0]
        theme_dict = THEMES_DATA['themes'][0][first_theme_name]
        print(f"Theme '{ACTIVE_THEME}' not found, falling back to '{first_theme_name}'")

    THEME_CONFIG = theme_dict

# Progress Bar Configuration
PROGRESS_BAR = {
    'frame_height': 80,
    'canvas_height': 80,
    'bar_y': 50,
    'circle_radius': 3,
    'line_color': THEME_CONFIG['colors']['secondary'],
    'line_width': 2,
    'circle_fill': THEME_CONFIG['colors']['primary'],
    'circle_active_fill': THEME_CONFIG['colors']['active'],
    'time_label_y': 30,
    'track_info_y': 30,
    'track_info_x': None,
    'frame_padding': (0, 25),
    'frame_side_padding': 10,
    'controls_y': 50,
    'button_spacing': 2,
    'progress_bg': THEME_CONFIG['colors'].get('progress_bg', '#404040'),
    'volume_control_width': 120,  # Width of volume control (icon + slider)
    'volume_slider_length': 90,   # Length of the volume slider
    'right_margin': 160,          # Space reserved for time display
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
        THEME_CONFIG['colors'].get('row_alt', THEME_CONFIG['colors']['selectbg']),
    ],
}

# File System
MAX_SCAN_DEPTH = 5

# Player Configuration
PROGRESS_UPDATE_INTERVAL = 100  # milliseconds
DEFAULT_LOOP_ENABLED = True

# Application settings
APP_NAME = "mt"
VERSION = "0.1.0"

# File extensions recognized as music files
MUSIC_EXTENSIONS = [
    ".mp3",
    ".flac",
    ".wav",
    ".ogg",
    ".m4a",
    ".aac"
]

# UI Colors - Using colors from the active theme
COLORS = {
    "background": THEME_CONFIG['colors'].get('bg', "#1E1E1E"),
    "sidebar_bg": THEME_CONFIG['colors'].get('dark', "#252526"),
    "text_primary": THEME_CONFIG['colors'].get('fg', "#FFFFFF"),
    "text_secondary": THEME_CONFIG['colors'].get('light', "#BBBBBB"),
    "accent": THEME_CONFIG['colors'].get('primary', "#0078D7"),
    "selection": THEME_CONFIG['colors'].get('selectbg', "#3A3D41"),
    "divider": THEME_CONFIG['colors'].get('border', "#333333"),
    "player_bg": THEME_CONFIG['colors'].get('inputbg', "#2D2D30"),
}

# UI Settings
UI_SETTINGS = {
    "font_family": "Segoe UI",
    "default_font_size": 14,
    "small_font_size": 12,
    "large_font_size": 16,
    "row_height": 32,
    "sidebar_width": 220,
}

# Default paths
DEFAULT_PATHS = {
    "music_dir": "~/Music",
    "downloads_dir": "~/Downloads",
    "playlists_dir": "~/Music/Playlists",
}

# Player settings
PLAYER_SETTINGS = {
    "volume": 0.7,
    "crossfade": 5,  # seconds
    "output_device": "default",
    "equalizer_enabled": False,
    "replay_gain": True,
    "visualizer_enabled": True,
}

# Column configuration
COLUMNS = [
    {"id": "number", "name": "#", "width": 40, "visible": True},
    {"id": "title", "name": "Title", "width": 400, "visible": True},
    {"id": "artist", "name": "Artist", "width": 300, "visible": True},
    {"id": "album", "name": "Album", "width": 350, "visible": True},
    {"id": "genre", "name": "Genre", "width": 120, "visible": True},
    {"id": "year", "name": "Year", "width": 100, "visible": True},
    {"id": "duration", "name": "Duration", "width": 90, "visible": True},
]

# Alphabet Row Configuration
ALPHABET_ROW = {
    'min_breakpoint': 850,        # Minimum width breakpoint before scaling
    'fixed_width': 1150,           # Fixed width when above breakpoint
    'height': 40,                 # Height of the alphabet row
    'initial_x': None,            # None means centered, or specify a pixel value
    'button_width': 25,           # Width for each letter button
    'button_height': 30,          # Height for each letter button
    'button_spacing': -5,         # Spacing between buttons (negative to bring closer)
    'padding_top': 5,             # Top padding for the container
    'padding_bottom': 5,          # Bottom padding for the container
    'use_wrap': False,            # Whether to allow wrapping to multiple rows
    'scale_factor': 0.9,          # Scaling factor when below breakpoint (90% of window width)
}
