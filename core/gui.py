import json
import tkinter as tk
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
