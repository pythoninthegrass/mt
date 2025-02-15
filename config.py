import os
from core.gui import (
    BUTTON_STYLE,
    BUTTON_SYMBOLS,
    COLORS,
    LISTBOX_CONFIG,
    PROGRESS_BAR,
    THEME_CONFIG,
    WINDOW_SIZE,
    WINDOW_TITLE,
)
from decouple import config

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

# File System
MAX_SCAN_DEPTH = 5

# Player Configuration
PROGRESS_UPDATE_INTERVAL = 100  # milliseconds
DEFAULT_LOOP_ENABLED = True
