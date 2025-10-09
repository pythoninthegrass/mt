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
    '.3gp',
    '.aac',
    '.ac3',
    '.aif',
    '.aiff',
    '.ape',
    '.dts',
    '.flac',
    '.m4a',
    '.m4b',
    '.m4r',
    '.mid',
    '.midi',
    '.mod',
    '.mp1',
    '.mp2',
    '.mp3',
    '.mpc',
    '.ogg',
    '.ra',
    '.tta',
    '.wav',
    '.wma',
    '.wv',
}


# Window Configuration
def _validate_window_size(size_str):
    """Validate and clean window size string to Tkinter geometry format."""
    import re

    # Remove any non-numeric characters except 'x'
    cleaned = re.sub(r'[^0-9x]', '', size_str)
    # Ensure it has exactly one 'x' and valid dimensions
    if 'x' not in cleaned or cleaned.count('x') != 1:
        return "1366x768"  # fallback to default
    width, height = cleaned.split('x')
    # Ensure both parts are numeric and reasonable
    try:
        w, h = int(width), int(height)
        if w < 100 or h < 100 or w > 7680 or h > 4320:  # reasonable bounds
            return "1366x768"
        return f"{w}x{h}"
    except ValueError:
        return "1366x768"


WINDOW_SIZE = _validate_window_size(config('MT_WINDOW_SIZE', default="1366x768"))
WINDOW_TITLE = config('MT_WINDOW_TITLE', default="mt")

# Button Configuration
BUTTON_STYLE = {
    'width': 3,
    'font': ('TkDefaultFont', 30),
}

# Button Icons
BUTTON_SYMBOLS = {
    'play': '▶',
    'pause': '⏸',
    'prev': '⏮',
    'next': '⏭',
    'add': 'static/add.png',
    'loop': 'static/repeat.png',
    'shuffle': 'static/shuffle.png',
    'volume': 'static/volume_up.png',
    'favorite': 'static/favorite.png',
    'favorite_border': 'static/favorite_border.png',
}

# Theme Configuration
THEME_CONFIG_FILE = Path('themes.json')
DEFAULT_THEME = 'metro-teal'
ACTIVE_THEME = config('MT_THEME', default=DEFAULT_THEME)

# Load theme data
with open(THEME_CONFIG_FILE) as f:
    THEMES_DATA = json.load(f)
    THEME_CONFIG = next(theme for theme in THEMES_DATA['themes'] if ACTIVE_THEME in theme)[ACTIVE_THEME]

# Progress Bar Configuration
PROGRESS_BAR = {
    'frame_height': 80,
    'canvas_height': 70,
    'bar_y': 45,  # Moved up slightly to better match MusicBee
    'circle_radius': 6,
    'line_color': THEME_CONFIG['colors']['secondary'],
    'line_width': 2,
    'circle_fill': THEME_CONFIG['colors']['primary'],
    'circle_active_fill': THEME_CONFIG['colors']['active'],
    'time_label_y': 25,  # Moved up to match progress bar adjustment
    'track_info_y': 25,  # Moved up to match progress bar adjustment
    'track_info_x': None,
    'frame_padding': (0, 20),
    'frame_side_padding': 10,
    'controls_y': 45,  # Moved up to match progress bar adjustment
    'button_spacing': 2,
    'progress_bg': THEME_CONFIG['colors'].get('progress_bg', '#404040'),
    'volume_control_width': 110,  # Width of volume control (icon + slider)
    'volume_slider_length': 80,  # Length of the volume slider
    'right_margin': 160,  # Space reserved for time display
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
    'shuffle_enabled': THEME_CONFIG['colors']['primary'],
    'shuffle_disabled': THEME_CONFIG['colors']['secondary'],
    'alternate_row_colors': [
        THEME_CONFIG['colors']['bg'],
        THEME_CONFIG['colors'].get('row_alt', THEME_CONFIG['colors']['selectbg']),
    ],
    'status_bar_bg': '#1f1f1f',  # Status bar background color
}

# File System
MAX_SCAN_DEPTH = 5

# Player Configuration
PROGRESS_UPDATE_INTERVAL = 100  # milliseconds
DEFAULT_LOOP_ENABLED = True
