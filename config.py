import json
import os
from decouple import config
from pathlib import Path

# Reload app during development
RELOAD = config('MT_RELOAD', default=False, cast=bool)

# Database Configuration
DB_NAME = config('DB_NAME', default='mt.db')

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


def _normalize_keybinding(binding: str) -> str:
    """Normalize keybinding string to tkinter format with case-insensitive modifiers.

    Supports:
    - Case-insensitive modifiers: cmd/CMD/Command → Command
    - Shorthand: cmd → Command, ctrl → Control
    - Compound modifiers: cmd-shift-d → Command-D (uppercase when Shift present)

    Args:
        binding: User keybinding string (e.g., "cmd-d", "cmd-shift-d", "ctrl-D")

    Returns:
        Normalized keybinding string (e.g., "Command-d", "Command-D", "Control-D")

    Examples:
        >>> _normalize_keybinding("cmd-d")
        'Command-d'
        >>> _normalize_keybinding("cmd-shift-d")
        'Command-D'
        >>> _normalize_keybinding("ctrl-shift-a")
        'Control-A'
        >>> _normalize_keybinding("command-D")
        'Command-D'
    """
    # Split on hyphen
    parts = [p.strip() for p in binding.split('-')]

    # Map for case-insensitive modifier normalization
    modifier_map = {
        'cmd': 'Command',
        'command': 'Command',
        'ctrl': 'Control',
        'control': 'Control',
        'alt': 'Alt',
        'shift': 'Shift',
    }

    modifiers = []
    key = None
    has_shift = False

    for part in parts:
        part_lower = part.lower()
        if part_lower in modifier_map:
            normalized = modifier_map[part_lower]
            if normalized == 'Shift':
                has_shift = True
            modifiers.append(normalized)
        else:
            # This is the key (last part)
            key = part

    # If Shift modifier present, uppercase the key
    # In tkinter, <Command-D> (uppercase) automatically implies Shift
    if has_shift and key:
        key = key.upper()
        # Remove explicit Shift from modifiers (uppercase key implies it)
        modifiers = [m for m in modifiers if m != 'Shift']

    # Rebuild normalized binding
    if key:
        return '-'.join(modifiers + [key])
    return binding  # Return original if parsing failed


def load_keybindings():
    """Load keybindings from settings.toml with fallback defaults.

    Returns:
        dict: Keybindings with both Command and Control variants for cross-platform support
    """
    import tomllib

    # Default keybindings
    defaults = {
        'queue_next': 'Command-d',
        'stop_after_current': 'Command-s',
    }

    settings_path = Path(__file__).parent / "settings.toml"

    # Load from settings.toml if it exists
    if settings_path.exists():
        try:
            with open(settings_path, 'rb') as f:
                settings = tomllib.load(f)
                if 'keybindings' in settings:
                    # Merge with defaults (user settings take precedence)
                    defaults.update(settings['keybindings'])
        except Exception:
            pass  # Fall back to defaults if file is invalid

    # Normalize all keybindings (case-insensitive, shorthand support, compound modifiers)
    normalized = {}
    for action, binding in defaults.items():
        # Apply normalization to support various input formats
        normalized_binding = _normalize_keybinding(binding)
        normalized[action] = normalized_binding

        # Create cross-platform variants if Command is used
        if 'Command' in normalized_binding:
            # Create Control variant for Windows/Linux
            control_binding = normalized_binding.replace('Command-', 'Control-')
            normalized[f"{action}_alt"] = control_binding

    return normalized


# Load keybindings at module import
KEYBINDINGS = load_keybindings()


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
    'repeat_one': 'static/repeat_one.png',
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

# Test Configuration
TEST_TIMEOUT = config('TEST_TIMEOUT', default=0.5, cast=float)
