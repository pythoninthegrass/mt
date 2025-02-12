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
