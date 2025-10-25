import tkinter as tk
from config import BUTTON_SYMBOLS, COLORS, THEME_CONFIG
from utils.icons import load_icon


class PlayerControls:
    def __init__(self, canvas, command_callbacks, initial_loop_enabled=True, initial_shuffle_enabled=False):
        self.canvas = canvas
        self.callbacks = command_callbacks
        self.add_button = None
        self.loop_button = None
        self.shuffle_button = None
        self.favorite_button = None
        self.play_button = None
        self.loop_enabled = initial_loop_enabled
        self.shuffle_enabled = initial_shuffle_enabled
        self.favorite_enabled = False

        # Icon sizes - playback controls are larger than utility controls
        self.playback_icon_size = (35, 35)
        self.utility_icon_size = (23, 23)

        # Store icon references to prevent garbage collection
        self.icon_images = {}

        self.setup_playback_controls()
        self.setup_utility_controls()

        # Bind canvas resize after all buttons are created
        self.canvas.bind('<Configure>', self._on_canvas_resize)

    def setup_playback_controls(self):
        # Create playback controls directly on canvas
        x_position = 25
        # Calculate vertical center of canvas (accounting for button height)
        self.canvas.update_idletasks()
        canvas_height = self.canvas.winfo_height()
        y_position = (canvas_height - self.playback_icon_size[1]) // 2

        # Store initial Y position for playback controls
        self.initial_playback_y = y_position

        for action, symbol in [
            ('previous', BUTTON_SYMBOLS['prev']),
            ('play', BUTTON_SYMBOLS['play']),
            ('next', BUTTON_SYMBOLS['next']),
        ]:
            button = tk.Label(
                self.canvas,
                text=symbol,
                fg='#CCCCCC',  # Light gray for normal state
                bg="#000000",  # Pure black background
                font=('TkDefaultFont', 28),
            )
            button.place(x=x_position, y=y_position)

            # Bind click and hover events
            button.bind('<Button-1>', lambda e, a=action: self.callbacks[a]())
            button.bind('<Enter>', lambda e, b=button: b.configure(fg=THEME_CONFIG['colors']['primary']))
            button.bind('<Leave>', lambda e, b=button: b.configure(fg='#CCCCCC'))

            if action == 'play':
                self.play_button = button

            x_position += self.playback_icon_size[0] + 10  # Add spacing between buttons

        # Store the width for progress bar calculations
        self.controls_width = x_position + 15

    def setup_utility_controls(self):
        # Create utility controls directly on canvas
        # Wait for canvas to be ready
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Calculate vertical center of canvas (accounting for icon height)
        # Then shift down by 1%
        y_center = (canvas_height - self.utility_icon_size[1]) // 2
        y_position = int(y_center + (canvas_height * 0.01))

        # Store initial Y position for utility controls
        self.initial_utility_y = y_position

        try:
            # Load icons for utility controls
            # Add button (rightmost)
            add_normal = load_icon(BUTTON_SYMBOLS['add'], size=self.utility_icon_size, opacity=0.7)
            add_hover = load_icon(
                BUTTON_SYMBOLS['add'], size=self.utility_icon_size, opacity=1.0, tint_color=THEME_CONFIG['colors']['primary']
            )
            self.icon_images['add_normal'] = add_normal
            self.icon_images['add_hover'] = add_hover
        except Exception as e:
            print(f"Error loading add button icons: {e}")
            import traceback

            traceback.print_exc()
            raise

        self.add_button = tk.Label(
            self.canvas,
            image=add_normal,
            bg="#000000",  # Pure black background like MusicBee
        )
        self.add_button.place(x=canvas_width - 60, y=y_position)
        self.add_button.bind('<Button-1>', lambda e: self.callbacks['add']())
        self.add_button.bind('<Enter>', lambda e: self.add_button.configure(image=self.icon_images['add_hover']))
        self.add_button.bind('<Leave>', lambda e: self.add_button.configure(image=self.icon_images['add_normal']))

        # Loop button (to the left of add button) - 54px spacing (reduced by 10% from 60px)
        loop_normal = load_icon(BUTTON_SYMBOLS['loop'], size=self.utility_icon_size, opacity=0.7)
        loop_enabled_icon = load_icon(
            BUTTON_SYMBOLS['loop'], size=self.utility_icon_size, opacity=1.0, tint_color=COLORS['loop_enabled']
        )
        loop_disabled_icon = load_icon(BUTTON_SYMBOLS['loop'], size=self.utility_icon_size, opacity=0.5)
        loop_hover = load_icon(
            BUTTON_SYMBOLS['loop'], size=self.utility_icon_size, opacity=1.0, tint_color=THEME_CONFIG['colors']['primary']
        )
        self.icon_images['loop_normal'] = loop_normal
        self.icon_images['loop_enabled'] = loop_enabled_icon
        self.icon_images['loop_disabled'] = loop_disabled_icon
        self.icon_images['loop_hover'] = loop_hover

        self.loop_button = tk.Label(
            self.canvas,
            image=loop_enabled_icon if self.loop_enabled else loop_disabled_icon,
            bg="#000000",  # Pure black background like MusicBee
        )
        self.loop_button.place(x=canvas_width - 114, y=y_position)
        self.loop_button.bind('<Button-1>', lambda e: self.callbacks['loop']())
        self.loop_button.bind('<Enter>', lambda e: self.loop_button.configure(image=self.icon_images['loop_hover']))
        self.loop_button.bind(
            '<Leave>',
            lambda e: self.loop_button.configure(
                image=self.icon_images['loop_enabled'] if self.loop_enabled else self.icon_images['loop_disabled']
            ),
        )

        # Shuffle button (to the left of loop button) - 54px spacing
        shuffle_normal = load_icon(BUTTON_SYMBOLS['shuffle'], size=self.utility_icon_size, opacity=0.7)
        shuffle_enabled_icon = load_icon(
            BUTTON_SYMBOLS['shuffle'], size=self.utility_icon_size, opacity=1.0, tint_color=COLORS['shuffle_enabled']
        )
        shuffle_disabled_icon = load_icon(BUTTON_SYMBOLS['shuffle'], size=self.utility_icon_size, opacity=0.5)
        shuffle_hover = load_icon(
            BUTTON_SYMBOLS['shuffle'], size=self.utility_icon_size, opacity=1.0, tint_color=THEME_CONFIG['colors']['primary']
        )
        self.icon_images['shuffle_normal'] = shuffle_normal
        self.icon_images['shuffle_enabled'] = shuffle_enabled_icon
        self.icon_images['shuffle_disabled'] = shuffle_disabled_icon
        self.icon_images['shuffle_hover'] = shuffle_hover

        self.shuffle_button = tk.Label(
            self.canvas,
            image=shuffle_enabled_icon if self.shuffle_enabled else shuffle_disabled_icon,
            bg="#000000",  # Pure black background like MusicBee
        )
        self.shuffle_button.place(x=canvas_width - 168, y=y_position)
        self.shuffle_button.bind('<Button-1>', lambda e: self.callbacks['shuffle']())
        self.shuffle_button.bind('<Enter>', lambda e: self.shuffle_button.configure(image=self.icon_images['shuffle_hover']))
        self.shuffle_button.bind(
            '<Leave>',
            lambda e: self.shuffle_button.configure(
                image=self.icon_images['shuffle_enabled'] if self.shuffle_enabled else self.icon_images['shuffle_disabled']
            ),
        )

        # Favorite button (to the left of shuffle button) - 54px spacing
        favorite_normal = load_icon(BUTTON_SYMBOLS['favorite_border'], size=self.utility_icon_size, opacity=0.7)
        favorite_filled = load_icon(
            BUTTON_SYMBOLS['favorite'], size=self.utility_icon_size, opacity=1.0, tint_color=COLORS['loop_enabled']
        )
        favorite_hover = load_icon(
            BUTTON_SYMBOLS['favorite_border'],
            size=self.utility_icon_size,
            opacity=1.0,
            tint_color=THEME_CONFIG['colors']['primary'],
        )
        favorite_filled_hover = load_icon(
            BUTTON_SYMBOLS['favorite'], size=self.utility_icon_size, opacity=1.0, tint_color=THEME_CONFIG['colors']['primary']
        )
        self.icon_images['favorite_normal'] = favorite_normal
        self.icon_images['favorite_filled'] = favorite_filled
        self.icon_images['favorite_hover'] = favorite_hover
        self.icon_images['favorite_filled_hover'] = favorite_filled_hover

        self.favorite_button = tk.Label(
            self.canvas,
            image=favorite_normal,
            bg="#000000",  # Pure black background like MusicBee
        )
        self.favorite_button.place(x=canvas_width - 222, y=y_position)
        self.favorite_button.bind('<Button-1>', lambda e: self.callbacks.get('favorite', lambda: None)())
        self.favorite_button.bind(
            '<Enter>',
            lambda e: self.favorite_button.configure(
                image=self.icon_images['favorite_filled_hover'] if self.favorite_enabled else self.icon_images['favorite_hover']
            ),
        )
        self.favorite_button.bind(
            '<Leave>',
            lambda e: self.favorite_button.configure(
                image=self.icon_images['favorite_filled'] if self.favorite_enabled else self.icon_images['favorite_normal']
            ),
        )

        # Ensure buttons are on top of canvas elements
        self.favorite_button.lift()
        self.shuffle_button.lift()
        self.loop_button.lift()
        self.add_button.lift()

        # Store the width for progress bar calculations
        self.utility_width = 222

    def _on_canvas_resize(self, event):
        """Reposition controls horizontally when canvas is resized, keeping Y positions fixed."""
        if not all([self.add_button, self.loop_button, self.shuffle_button, self.favorite_button, self.play_button]):
            return

        # Use stored initial Y positions - do NOT recalculate to prevent vertical movement
        playback_y = self.initial_playback_y
        utility_y = self.initial_utility_y

        # Calculate positions relative to canvas width
        canvas_width = event.width

        # Utility controls are positioned from the right with 54px spacing
        # Add button at right edge minus padding
        add_x = canvas_width - 60
        self.add_button.place(x=add_x, y=utility_y)

        # Loop button to the left of add button - 54px spacing
        loop_x = canvas_width - 114
        self.loop_button.place(x=loop_x, y=utility_y)

        # Shuffle button to the left of loop button - 54px spacing
        shuffle_x = canvas_width - 168
        self.shuffle_button.place(x=shuffle_x, y=utility_y)

        # Favorite button to the left of shuffle button - 54px spacing
        favorite_x = canvas_width - 222
        self.favorite_button.place(x=favorite_x, y=utility_y)

        # Playback controls are positioned from the left, maintaining fixed X positions
        # Start at x=25 to match initial setup
        x_position = 25

        # Find playback control buttons (they are tk.Label widgets that are not utility buttons)
        playback_buttons = []
        for child in self.canvas.winfo_children():
            if isinstance(child, tk.Label) and child not in [
                self.add_button,
                self.loop_button,
                self.shuffle_button,
                self.favorite_button,
            ]:
                playback_buttons.append(child)

        # Position playback controls with the same spacing as initial setup
        for button in playback_buttons:
            button.place(x=x_position, y=playback_y)
            # Use the same spacing as setup_playback_controls: icon width + 10px
            x_position += self.playback_icon_size[0] + 10

        # Update controls width for progress bar calculations
        self.controls_width = (
            x_position + 15
        )  # Same as initial setup  # Same as initial setup  # Same as initial setup  # Same as initial setup  # Same as initial setup  # Same as initial setup  # Same as initial setup  # Same as initial setup  # Same as initial setup  # Same as initial setup

    def update_loop_button_color(self, loop_enabled):
        """Update loop button icon based on loop state."""
        self.loop_enabled = loop_enabled  # Update the internal state
        self.loop_button.configure(image=self.icon_images['loop_enabled'] if loop_enabled else self.icon_images['loop_disabled'])

    def update_shuffle_button_color(self, shuffle_enabled):
        """Update shuffle button icon based on shuffle state."""
        self.shuffle_enabled = shuffle_enabled  # Update the internal state
        self.shuffle_button.configure(
            image=self.icon_images['shuffle_enabled'] if shuffle_enabled else self.icon_images['shuffle_disabled']
        )

    def update_favorite_button(self, is_favorite):
        """Update favorite button icon based on favorite state."""
        self.favorite_enabled = is_favorite
        if is_favorite:
            self.favorite_button.configure(image=self.icon_images['favorite_filled'])
        else:
            self.favorite_button.configure(image=self.icon_images['favorite_normal'])

    def update_play_button(self, is_playing):
        """Update play button to show play or pause state."""
        indicator = ('▶' if is_playing else '⏸')
        if is_playing:
            # When playing, show pause symbol
            self.play_button.configure(
                text=BUTTON_SYMBOLS['pause'],
                fg='#FFFFFF',  # Bright white when active/playing
            )
        else:
            # When paused/stopped, show play symbol
            self.play_button.configure(
                text=BUTTON_SYMBOLS['play'],
                fg='#CCCCCC',  # Light gray when paused
            )
