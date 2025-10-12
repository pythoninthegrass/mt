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

def get_version():
    """Get version from pyproject.toml"""
    import tomllib

    toml_load = tomllib.load
    open_mode = 'rb'

    pyproject_path = Path(__file__).parent / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, open_mode) as f:
            data = toml_load(f)
            return data.get("project", {}).get("version", "unknown")
    return "unknown"


__version__ = get_version()


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

# App Configuration
APP_NAME = config('MT_APP_NAME', default="mt")


def configure_macos(root=None):
    """Configure macOS-specific app properties.

    Call once before window creation (root=None) to set process name,
    then again after window creation (with root) to configure window properties.

    Args:
        root: Optional Tk root window instance. If None, only sets process name.
    """
    import datetime
    import platform
    import sys

    if platform.system() != "Darwin":
        return

    try:
        # Phase 1: Pre-window setup (when root=None)
        if root is None:
            from Foundation import NSProcessInfo

            # Set the process name - this affects both menu bar and dock
            process_info = NSProcessInfo.processInfo()
            process_info.setProcessName_(APP_NAME)

            # Also modify sys.argv[0] to change what the system reports as the executable
            sys.argv[0] = APP_NAME
            return

        # Phase 2: Post-window setup (when root is provided)
        # Set the window class for macOS
        root.tk.call('::tk::unsupported::MacWindowStyle', 'style', root._w, 'document')

        # Update NSApplication after Tk init
        from AppKit import NSApplication, NSBundle

        app = NSApplication.sharedApplication()

        # Update bundle info dictionary
        bundle = NSBundle.mainBundle()
        if bundle:
            info = bundle.infoDictionary()
            if info is not None:
                info['CFBundleName'] = APP_NAME
                info['CFBundleDisplayName'] = APP_NAME
                info['CFBundleExecutable'] = APP_NAME
                info['CFBundleIdentifier'] = f'com.mt.{APP_NAME}'
                info['CFBundleVersion'] = __version__
                info['CFBundleShortVersionString'] = __version__
                info['NSHumanReadableCopyright'] = f"© {datetime.datetime.now().year} pythoninthegrass"

        # Set activation policy to make it a proper app
        app.setActivationPolicy_(0)  # NSApplicationActivationPolicyRegular

        # Force app to activate
        app.activateIgnoringOtherApps_(True)

    except Exception as e:
        print(f"macOS configuration error: {e}")


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
    'status_bar_bg': '#272931',  # Status bar background color
}

# File System
MAX_SCAN_DEPTH = 5

# Player Configuration
PROGRESS_UPDATE_INTERVAL = 100  # milliseconds
DEFAULT_LOOP_ENABLED = True

# API Server Configuration
API_SERVER_ENABLED = config('MT_API_SERVER_ENABLED', default=False, cast=bool)
API_SERVER_PORT = config('MT_API_SERVER_PORT', default=5555, cast=int)
