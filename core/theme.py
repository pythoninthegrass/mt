import tkinter as tk
import tkinter.font as tkfont
from config import (
    BUTTON_STYLE,
    COLORS,
    LISTBOX_CONFIG,
    PROGRESS_BAR,
    THEME_CONFIG,
)
from tkinter import ttk


def setup_theme(root):
    """Configure the application theme and styles"""
    # Use standard ttk.Style without ttkbootstrap
    style = ttk.Style()

    # Configure root window and base theme
    root.configure(background=THEME_CONFIG['colors']['bg'])
    root.option_add('*Background', THEME_CONFIG['colors']['bg'])
    root.option_add('*Foreground', THEME_CONFIG['colors']['fg'])

    # Apply theme colors from config
    style.configure('.',
                   background=THEME_CONFIG['colors']['bg'],
                   foreground=THEME_CONFIG['colors']['fg'])

    # Configure all ttk widgets to use the same background
    for widget in ['TFrame', 'TPanedwindow', 'Treeview', 'TButton', 'TLabel']:
        style.configure(widget,
                      background=THEME_CONFIG['colors']['bg'],
                      fieldbackground=THEME_CONFIG['colors']['bg'])

    style.configure('TButton',
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
                   font=BUTTON_STYLE['font'])

    style.configure('Loop.Controls.TButton',
                   background=THEME_CONFIG['colors']['bg'],
                   foreground=THEME_CONFIG['colors']['fg'],
                   borderwidth=0,
                   relief='flat',
                   focuscolor='',           # Remove focus border
                   highlightthickness=0,    # Remove highlight border
                   font=BUTTON_STYLE['font'])

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

    # Configure treeview with alternating row colors
    row_alt = THEME_CONFIG['colors'].get('row_alt', '#242424')
    style.map('Treeview',
             background=[
                 ('selected', THEME_CONFIG['colors']['selectbg']),
                 ('alternate', row_alt)  # Use alternate for odd rows
             ],
             foreground=[('selected', THEME_CONFIG['colors']['selectfg'])])

    # Configure Treeview Heading style
    style.configure('Treeview.Heading',
                   background=THEME_CONFIG['colors']['bg'],
                   foreground=THEME_CONFIG['colors']['fg'],
                   relief='flat',
                   borderwidth=0)

    style.map('Treeview.Heading',
             background=[('active', THEME_CONFIG['colors']['bg'])],
             foreground=[('active', THEME_CONFIG['colors']['primary'])])

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
        'alternate_row_colors': [
            THEME_CONFIG['colors']['bg'],
            THEME_CONFIG['colors'].get('row_alt', '#242424')
        ]
    })
