import json
import os
import tkinter as tk
import tkinter.font as tkfont
import ttkbootstrap as ttk
from config import (
    BUTTON_STYLE,
    BUTTON_SYMBOLS,
    COLORS,
    LISTBOX_CONFIG,
    PROGRESS_BAR,
    THEME_CONFIG,
)
from core.controls import PlayerCore
from decouple import config
from pathlib import Path


def setup_theme(root):
    """Configure the application theme and styles"""
    style = ttk.Style(theme='darkly')  # Start with darkly as base

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

class PlayerControls:
    def __init__(self, canvas, command_callbacks, initial_loop_enabled=True):
        self.canvas = canvas
        self.callbacks = command_callbacks
        self.add_button = None
        self.loop_button = None
        self.play_button = None
        self.loop_enabled = initial_loop_enabled
        self.setup_playback_controls()
        self.setup_utility_controls()

        # Bind canvas resize after all buttons are created
        self.canvas.bind('<Configure>', self._on_canvas_resize)

    def setup_playback_controls(self):
        # Create playback controls directly on canvas
        x_position = 10
        y_position = PROGRESS_BAR['controls_y'] - 25

        for action, symbol in [
            ('previous', BUTTON_SYMBOLS['prev']),
            ('play', BUTTON_SYMBOLS['play']),
            ('next', BUTTON_SYMBOLS['next']),
        ]:
            button = tk.Label(
                self.canvas,
                text=symbol,
                font=BUTTON_STYLE['font'],
                fg=THEME_CONFIG['colors']['fg'],
                bg=THEME_CONFIG['colors']['bg']
            )
            button.place(x=x_position, y=y_position)

            # Bind click and hover events
            button.bind('<Button-1>', lambda e, a=action: self.callbacks[a]())
            button.bind('<Enter>', lambda e, b=button: b.configure(fg=THEME_CONFIG['colors']['primary']))
            button.bind('<Leave>', lambda e, b=button: b.configure(fg=THEME_CONFIG['colors']['fg']))

            if action == 'play':
                self.play_button = button

            x_position += button.winfo_reqwidth() + 5  # Add spacing between buttons

        # Store the width for progress bar calculations
        self.controls_width = x_position + 15

    def setup_utility_controls(self):
        # Create utility controls directly on canvas
        y_position = PROGRESS_BAR['controls_y'] - 25

        # Wait for canvas to be ready
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()

        # Add button (rightmost)
        self.add_button = tk.Label(
            self.canvas,
            text=BUTTON_SYMBOLS['add'],
            font=BUTTON_STYLE['font'],
            fg=THEME_CONFIG['colors']['fg'],
            bg=THEME_CONFIG['colors']['bg']
        )
        self.add_button.place(x=canvas_width - 60, y=y_position)
        self.add_button.bind('<Button-1>', lambda e: self.callbacks['add']())
        self.add_button.bind('<Enter>', lambda e: self.add_button.configure(fg=THEME_CONFIG['colors']['primary']))
        self.add_button.bind('<Leave>', lambda e: self.add_button.configure(fg=THEME_CONFIG['colors']['fg']))

        # Loop button (to the left of add button)
        self.loop_button = tk.Label(
            self.canvas,
            text=BUTTON_SYMBOLS['loop'],
            font=BUTTON_STYLE['font'],
            fg=THEME_CONFIG['colors']['fg'],  # Start with default color
            bg=THEME_CONFIG['colors']['bg']
        )
        self.loop_button.place(x=canvas_width - 120, y=y_position)
        self.loop_button.bind('<Button-1>', lambda e: self.callbacks['loop']())
        self.loop_button.bind('<Enter>', lambda e: self.loop_button.configure(fg=THEME_CONFIG['colors']['primary']))
        self.loop_button.bind('<Leave>', lambda e: self.loop_button.configure(
            fg=COLORS['loop_enabled'] if self.loop_enabled else COLORS['loop_disabled']
        ))

        # Force update loop button color after creation
        self.update_loop_button_color(self.loop_enabled)

        # Store the width for progress bar calculations
        self.utility_width = 120

    def _on_canvas_resize(self, event):
        """Recenter the buttons vertically and reposition utility controls when canvas is resized."""
        if not all([self.add_button, self.loop_button]):
            return

        # Update all button positions
        for button in self.canvas.winfo_children():
            if isinstance(button, tk.Label):
                # Calculate new y position
                new_y = (event.height - button.winfo_reqheight()) // 2

                # For utility controls, update x position from right
                if button == self.add_button:
                    new_x = event.width - 60
                    button.place(x=new_x, y=new_y)
                elif button == self.loop_button:
                    new_x = event.width - 120
                    button.place(x=new_x, y=new_y)
                else:
                    # For playback controls, keep x position
                    button.place(y=new_y)

    def update_loop_button_color(self, loop_enabled):
        """Update loop button color based on loop state."""
        self.loop_enabled = loop_enabled  # Update the internal state
        self.loop_button.configure(
            fg=COLORS['loop_enabled'] if loop_enabled else COLORS['loop_disabled']
        )

class ProgressBar:
    def __init__(self, window, progress_frame, callbacks, initial_loop_enabled=True):
        self.window = window
        self.progress_frame = progress_frame
        self.callbacks = callbacks
        self.initial_loop_enabled = initial_loop_enabled
        self.setup_progress_bar()
        self.setup_volume_control()

    def setup_progress_bar(self):
        # Create canvas for custom progress bar
        self.canvas = tk.Canvas(
            self.progress_frame,
            height=PROGRESS_BAR['canvas_height'],
            background=THEME_CONFIG['colors']['bg'],
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.X)

        # Create controls with initial loop state
        self.controls = PlayerControls(self.canvas, self.callbacks, initial_loop_enabled=self.initial_loop_enabled)
        self.controls_width = self.controls.controls_width

        # Create track info text - positioned above progress line
        self.track_info = self.canvas.create_text(
            self.controls_width,  # Align with start of progress line
            PROGRESS_BAR['track_info_y'],
            text="",  # Initialize with empty text
            fill=THEME_CONFIG['colors']['fg'],
            anchor=tk.W,
        )

        # Create time labels - moved to the left to make room for volume control
        self.time_text = self.canvas.create_text(
            self.canvas.winfo_width() - 260,  # Position before volume control
            PROGRESS_BAR['time_label_y'],
            text="00:00 / 00:00",
            fill=THEME_CONFIG['colors']['fg'],
            anchor=tk.E,
        )

        # Create progress bar background (dark line)
        self.bar_y = PROGRESS_BAR['bar_y']
        self.line = self.canvas.create_line(
            self.controls_width,
            self.bar_y,
            self.canvas.winfo_width() - 260,  # Make shorter to accommodate volume control
            self.bar_y,
            fill=PROGRESS_BAR['progress_bg'],  # Use dark background color
            width=PROGRESS_BAR['line_width'] + 2,  # Slightly wider for the background
        )

        # Create progress bar foreground (teal line) - initially at start position
        self.progress_line = self.canvas.create_line(
            self.controls_width,
            self.bar_y,
            self.controls_width,  # Initially same as start
            self.bar_y,
            fill=THEME_CONFIG['colors']['primary'],  # Teal color
            width=PROGRESS_BAR['line_width'],
        )

        # Create progress circle with teal fill
        self.circle_radius = PROGRESS_BAR['circle_radius']
        self.progress_circle = self.canvas.create_oval(
            self.controls_width - self.circle_radius,
            self.bar_y - self.circle_radius,
            self.controls_width + self.circle_radius,
            self.bar_y + self.circle_radius,
            fill=THEME_CONFIG['colors']['primary'],  # Teal fill
            outline=THEME_CONFIG['colors']['playhead_border'],  # Border to make it more visible
        )

        # Ensure proper z-order - playhead must be on top
        self.canvas.tag_raise(self.progress_line)  # Progress line above background
        self.canvas.tag_raise(self.progress_circle)  # Playhead circle on top of everything

        # Bind events
        self.dragging = False
        self.last_drag_time = 0
        self.canvas.tag_bind(self.progress_circle, '<Button-1>', self.callbacks['start_drag'])
        self.canvas.tag_bind(self.progress_circle, '<B1-Motion>', self.callbacks['drag'])
        self.canvas.tag_bind(self.progress_circle, '<ButtonRelease-1>', self.callbacks['end_drag'])

        # Create invisible hitbox for the progress bar to handle clicks
        progress_end_x = self.canvas.coords(self.line)[2]
        self.progress_hitbox = self.canvas.create_rectangle(
            self.controls_width - 5,
            self.bar_y - 10,
            progress_end_x + 5,
            self.bar_y + 10,
            fill='',  # Transparent fill
            outline='',  # No outline
            tags=('progress_hitbox',)
        )

        # Bind click to the hitbox instead of the whole canvas
        self.canvas.tag_bind('progress_hitbox', '<Button-1>', self.callbacks['click_progress'])
        self.canvas.bind('<Configure>', self.on_resize)

    def setup_volume_control(self):
        """Create and setup custom volume control slider."""
        # Get the circle radius for consistent styling
        self.volume_circle_radius = self.circle_radius  # Use same radius as progress circle

        # Calculate loop button position (based on the PlayerControls class)
        canvas_width = self.canvas.winfo_width()
        loop_button_x = canvas_width - 120

        # Set the volume slider width
        self.volume_slider_width = PROGRESS_BAR['volume_slider_length']

        # Calculate positions with proper spacing
        progress_end_x = self.canvas.coords(self.line)[2]  # End of progress line

        # Calculate volume position with proper spacing (centered between progress and loop)
        volume_x_start = progress_end_x + 40  # Add padding after progress line

        # Create volume icon
        self.volume_icon = tk.Label(
            self.canvas,
            text=BUTTON_SYMBOLS['volume'],
            font=('TkDefaultFont', 12),
            bg=THEME_CONFIG['colors']['bg'],
            fg=THEME_CONFIG['colors']['primary']
        )
        self.volume_icon.place(x=volume_x_start - 25, y=self.bar_y - 10)  # Position icon to the left of slider

        # Default volume is 80%
        self.volume_value = 80

        # Add padding to ensure circle never goes behind icon (equal to circle radius)
        self.volume_slider_padding = self.volume_circle_radius

        # Store the actual slider bounds (with padding for the circle)
        self.volume_slider_start = volume_x_start + self.volume_slider_padding
        self.volume_slider_end = volume_x_start + self.volume_slider_width

        # Store the visual bounds (where the line is drawn)
        self.volume_line_start = volume_x_start
        self.volume_line_end = volume_x_start + self.volume_slider_width

        # Calculate initial volume position with padding
        volume_position = self.volume_slider_start + ((self.volume_slider_end - self.volume_slider_start) * 0.8)

        # Create volume slider background line
        self.volume_line_bg = self.canvas.create_line(
            self.volume_line_start,
            self.bar_y,
            self.volume_line_end,
            self.bar_y,
            fill=PROGRESS_BAR['progress_bg'],  # Same color as progress bar background
            width=PROGRESS_BAR['line_width'] + 2,  # Same width as progress bar bg
        )

        # Create volume slider foreground line - now white as requested
        self.volume_line_fg = self.canvas.create_line(
            self.volume_line_start,
            self.bar_y,
            volume_position,
            self.bar_y,
            fill='white',  # White color as requested
            width=PROGRESS_BAR['line_width'],  # Same width as progress bar
        )

        # Create volume slider handle (circle with white outline, black fill)
        self.volume_circle = self.canvas.create_oval(
            volume_position - self.volume_circle_radius,
            self.bar_y - self.volume_circle_radius,
            volume_position + self.volume_circle_radius,
            self.bar_y + self.volume_circle_radius,
            fill='black',  # Black fill as requested
            outline='white',  # White outline as requested
            width=1,  # Outline width
            tags=('volume_circle',)  # Add tag for easier reference
        )

        # Set proper z-order
        self.canvas.tag_raise(self.volume_line_fg)  # Foreground above background
        self.canvas.tag_raise(self.volume_circle)    # Circle above lines

        # Store volume control coordinates for later reference
        self.volume_x_start = volume_x_start
        self.volume_x_end = volume_x_start + self.volume_slider_width

        # Bind events for volume slider
        self.canvas.tag_bind('volume_circle', '<Button-1>', self._start_volume_drag)
        self.canvas.tag_bind('volume_circle', '<B1-Motion>', self._drag_volume)
        self.canvas.tag_bind('volume_circle', '<ButtonRelease-1>', self._end_volume_drag)

        # Create invisible hitbox for clicking on volume slider directly
        self.volume_hitbox = self.canvas.create_rectangle(
            volume_x_start - 5,  # Slightly wider than visible slider
            self.bar_y - 10,
            volume_x_start + self.volume_slider_width + 5,
            self.bar_y + 10,
            fill='',  # Transparent fill
            outline='',  # No outline
            tags=('volume_hitbox',)
        )

        # Ensure volume hitbox is above progress hitbox to capture events first
        self.canvas.tag_raise('volume_hitbox')

        # Ensure circle is on top of everything for proper dragging
        self.canvas.tag_raise(self.volume_circle)

        # Bind click on the hitbox
        self.canvas.tag_bind('volume_hitbox', '<Button-1>', self._click_volume)

        # Set initial volume after a short delay
        if self.callbacks and 'volume_change' in self.callbacks:
            self.canvas.after(1000, lambda: self.callbacks['volume_change'](80))

    def _start_volume_drag(self, event):
        """Start dragging the volume slider."""
        self.volume_dragging = True

    def _drag_volume(self, event):
        """Handle volume slider dragging."""
        if not hasattr(self, 'volume_dragging') or not self.volume_dragging:
            return

        # Print debug info
        print(f"Dragging volume: {event.x}")

        # Calculate new volume based on drag position
        x = event.x

        # Constrain x to slider bounds with padding for the circle
        if x < self.volume_slider_start:
            x = self.volume_slider_start
        elif x > self.volume_slider_end:
            x = self.volume_slider_end

        # Update volume value (0-100)
        slider_range = self.volume_slider_end - self.volume_slider_start
        self.volume_value = int(((x - self.volume_slider_start) / slider_range) * 100)

        # Update slider position
        self._update_volume_slider_position()

        # Call volume change callback
        if self.callbacks and 'volume_change' in self.callbacks:
            self.callbacks['volume_change'](self.volume_value)

    def _end_volume_drag(self, event):
        """End volume slider dragging."""
        self.volume_dragging = False

    def _click_volume(self, event):
        """Handle click directly on volume slider."""
        # Calculate new volume based on click position
        x = event.x

        # Constrain x to slider bounds with padding for the circle
        if x < self.volume_slider_start:
            x = self.volume_slider_start
        elif x > self.volume_slider_end:
            x = self.volume_slider_end

        # Update volume value (0-100)
        slider_range = self.volume_slider_end - self.volume_slider_start
        self.volume_value = int(((x - self.volume_slider_start) / slider_range) * 100)

        # Update slider position
        self._update_volume_slider_position()

        # Call volume change callback
        if self.callbacks and 'volume_change' in self.callbacks:
            self.callbacks['volume_change'](self.volume_value)

    def _update_volume_slider_position(self):
        """Update the position of the volume slider based on current volume."""
        # Calculate position based on volume value with padding
        slider_range = self.volume_slider_end - self.volume_slider_start
        x = self.volume_slider_start + (slider_range * (self.volume_value / 100))

        # Update foreground line
        self.canvas.coords(
            self.volume_line_fg,
            self.volume_line_start,  # Line always starts at the visual start
            self.bar_y,
            x,
            self.bar_y,
        )

        # Update circle position
        self.canvas.coords(
            self.volume_circle,
            x - self.volume_circle_radius,
            self.bar_y - self.volume_circle_radius,
            x + self.volume_circle_radius,
            self.bar_y + self.volume_circle_radius,
        )

        # Ensure circle remains on top
        self.canvas.tag_raise(self.volume_circle)

    def on_resize(self, event):
        """Handle window resize."""
        # Update progress line background - shortened to make room for volume control
        self.canvas.coords(
            self.line,
            self.controls_width,
            self.bar_y,
            event.width - 260,  # Shortened to make room for volume control
            self.bar_y,
        )

        # Update progress line foreground
        # Keep the same ratio as before
        if hasattr(self, 'progress_line'):
            current_coords = self.canvas.coords(self.progress_line)
            if len(current_coords) == 4:
                # Calculate current ratio
                total_width_before = self.canvas.coords(self.line)[2] - self.controls_width
                if total_width_before > 0:
                    current_ratio = (current_coords[2] - self.controls_width) / total_width_before

                    # Apply ratio to new width
                    new_total_width = event.width - 260 - self.controls_width  # Updated width
                    new_x = self.controls_width + (new_total_width * current_ratio)

                    self.canvas.coords(
                        self.progress_line,
                        self.controls_width,
                        self.bar_y,
                        new_x,
                        self.bar_y,
                    )

                    # Also move the circle
                    self.canvas.coords(
                        self.progress_circle,
                        new_x - self.circle_radius,
                        self.bar_y - self.circle_radius,
                        new_x + self.circle_radius,
                        self.bar_y + self.circle_radius,
                    )

        # Update time label position - moved to make room for volume
        self.canvas.coords(
            self.time_text,
            event.width - 260,  # Position before volume control
            PROGRESS_BAR['time_label_y'],
        )

        # Update track info position if available
        if self.track_info:
            current_text = self.canvas.itemcget(self.track_info, 'text')
            if current_text:
                # Keep text anchored to the left but update when window changes
                self.canvas.coords(
                    self.track_info,
                    self.controls_width,
                    PROGRESS_BAR['track_info_y'],
                )

        # Reposition volume control on resize
        if hasattr(self, 'volume_line_bg'):
            # Calculate new positions with proper spacing
            progress_end_x = self.canvas.coords(self.line)[2]  # End of progress line
            loop_button_x = event.width - 120  # Loop button position

            # Position volume with proper spacing
            volume_x_start = progress_end_x + 40  # Add padding after progress line

            # Update slider bounds
            self.volume_slider_start = volume_x_start + self.volume_slider_padding
            self.volume_slider_end = volume_x_start + self.volume_slider_width
            self.volume_line_start = volume_x_start
            self.volume_line_end = volume_x_start + self.volume_slider_width

            # Calculate current volume position
            slider_range = self.volume_slider_end - self.volume_slider_start
            volume_position = self.volume_slider_start + (slider_range * (self.volume_value / 100))

            # Update volume slider background
            self.canvas.coords(
                self.volume_line_bg,
                self.volume_line_start,
                self.bar_y,
                self.volume_line_end,
                self.bar_y,
            )

            # Update volume slider foreground
            self.canvas.coords(
                self.volume_line_fg,
                self.volume_line_start,
                self.bar_y,
                volume_position,
                self.bar_y,
            )

            # Update volume slider handle
            self.canvas.coords(
                self.volume_circle,
                volume_position - self.volume_circle_radius,
                self.bar_y - self.volume_circle_radius,
                volume_position + self.volume_circle_radius,
                self.bar_y + self.volume_circle_radius,
            )

            # Ensure circle remains on top after resize
            self.canvas.tag_raise(self.volume_circle)

            # Update hitbox
            self.canvas.coords(
                self.volume_hitbox,
                volume_x_start - 5,
                self.bar_y - 10,
                volume_x_start + self.volume_slider_width + 5,
                self.bar_y + 10,
            )

            # Update volume icon position
            self.volume_icon.place(x=volume_x_start - 25, y=self.bar_y - 10)

            # Store updated coordinates
            self.volume_x_start = volume_x_start
            self.volume_x_end = volume_x_start + self.volume_slider_width

        # Update progress hitbox
        if hasattr(self, 'progress_hitbox'):
            progress_end_x = self.canvas.coords(self.line)[2]
            self.canvas.coords(
                self.progress_hitbox,
                self.controls_width - 5,
                self.bar_y - 10,
                progress_end_x + 5,
                self.bar_y + 10,
            )

    def update_track_info(self, title=None, artist=None):
        """Update the track info display."""
        if title and artist:
            track_info = f"{artist} - {title}"  # Display as "Artist - Title"
        else:
            track_info = ""
        self.canvas.itemconfig(self.track_info, text=track_info)

    def clear_track_info(self):
        """Clear the track info display."""
        self.canvas.itemconfig(self.track_info, text="")

class LibraryView:
    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks
        self.setup_library_view()

    def setup_library_view(self):
        # Create treeview for library/playlists
        self.library_tree = ttk.Treeview(
            self.parent, show='tree', selectmode='browse'
        )
        self.library_tree.pack(expand=True, fill=tk.BOTH)

        # Library section
        library_id = self.library_tree.insert('', 'end', text='Library', open=True)
        music_item = self.library_tree.insert(library_id, 'end', text='Music', tags=('music',))
        self.library_tree.insert(
            library_id, 'end', text='Now Playing', tags=('now_playing',)
        )

        # Playlists section
        playlists_id = self.library_tree.insert('', 'end', text='Playlists', open=True)
        self.library_tree.insert(
            playlists_id, 'end', text='Recently Added', tags=('recent_added',)
        )
        self.library_tree.insert(
            playlists_id, 'end', text='Recently Played', tags=('recent_played',)
        )
        self.library_tree.insert(
            playlists_id, 'end', text='Top 25 Most Played', tags=('top_played',)
        )

        # Select Music by default
        self.library_tree.selection_set(music_item)
        self.library_tree.see(music_item)
        # Trigger the selection event to load the library
        self.library_tree.event_generate('<<TreeviewSelect>>')

        # Calculate optimal width
        items = [
            'Library',
            'Music',
            'Now Playing',
            'Playlists',
            'Recently Added',
            'Recently Played',
            'Top 25 Most Played',
        ]

        style = ttk.Style()
        font_str = style.lookup('Treeview', 'font')
        if not font_str:
            font_str = 'TkDefaultFont'
        font = tkfont.nametofont(font_str)

        text_width = max(font.measure(text) for text in items)
        indent_width = 10
        icon_width = 10
        max_indent_level = 2
        side_padding = 0

        total_width = (
            text_width
            + (indent_width * max_indent_level)
            + icon_width
            + side_padding
        )

        pane_width = total_width + 40

        # Configure width
        self.parent.configure(width=pane_width)
        self.parent.pack_propagate(False)

        # Bind selection event
        self.library_tree.bind('<<TreeviewSelect>>', self.callbacks['on_section_select'])

class QueueView:
    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks
        self.setup_queue_view()

    def setup_queue_view(self):
        # Create queue frame and treeview
        self.queue_frame = ttk.Frame(self.parent)
        self.queue_frame.pack(expand=True, fill=tk.BOTH)

        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(self.queue_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create treeview with columns
        self.queue = ttk.Treeview(
            self.queue_frame,
            columns=('track', 'title', 'artist', 'album', 'year'),
            show='headings',
            selectmode='extended',
            yscrollcommand=self.scrollbar.set,
            style='Treeview'  # Explicit style name
        )

        # Enable alternating row colors
        self.queue.tag_configure('evenrow', background=THEME_CONFIG['colors']['bg'])
        self.queue.tag_configure('oddrow', background=THEME_CONFIG['colors'].get('row_alt', '#242424'))

        # Configure columns
        self.queue.heading('track', text='#')
        self.queue.heading('title', text='Title')
        self.queue.heading('artist', text='Artist')
        self.queue.heading('album', text='Album')
        self.queue.heading('year', text='Year')

        self.queue.column('track', width=50, anchor='center')
        self.queue.column('title', width=300)
        self.queue.column('artist', width=200)
        self.queue.column('album', width=200)
        self.queue.column('year', width=100, anchor='center')

        self.queue.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.scrollbar.config(command=self.queue.yview)

        # Add bindings
        self.queue.bind('<Double-Button-1>', self.callbacks['play_selected'])
        self.queue.bind('<Delete>', self.callbacks['handle_delete'])
        self.queue.bind('<BackSpace>', self.callbacks['handle_delete'])
        self.queue.bind('<<TreeviewSelect>>', self.callbacks['on_song_select'])
        # Add select all keyboard shortcuts
        self.queue.bind('<Command-a>', self.select_all)  # macOS
        self.queue.bind('<Control-a>', self.select_all)  # Windows/Linux

        # Setup drag and drop
        self.queue.drop_target_register('DND_Files')
        self.queue.dnd_bind('<<Drop>>', self.callbacks['handle_drop'])

    def select_all(self, event=None):
        """Select all items in the queue."""
        self.queue.selection_set(self.queue.get_children())
        return "break"  # Prevent default handling

class MusicPlayer:
    def __init__(self, window: tk.Tk, theme_manager):
        self.window = window
        self.theme_manager = theme_manager
        self.setup_components()

    def setup_components(self):
        # Create player core first
        self.player_core = PlayerCore(self.db, self.queue_manager, self.queue_view)
        self.player_core.window = self.window  # Set window reference for thread-safe callbacks

        # ... existing code ...
