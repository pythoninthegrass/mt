import tkinter as tk


class VolumeControl:
    def __init__(self, canvas, bar_y, volume_circle_radius, button_symbols, theme_config, callbacks):
        self.canvas = canvas
        self.bar_y = bar_y
        self.volume_circle_radius = volume_circle_radius
        self.button_symbols = button_symbols
        self.theme_config = theme_config
        self.callbacks = callbacks

        # Default volume is 80%
        self.volume_value = 80
        self.volume_dragging = False

        # Will be calculated during setup
        self.volume_slider_width = 80
        self.volume_slider_padding = self.volume_circle_radius
        self.volume_slider_start = 0  # Will be set during setup
        self.volume_slider_end = 0    # Will be set during setup
        self.volume_line_start = 0    # Will be set during setup
        self.volume_line_end = 0      # Will be set during setup

        # UI elements - will be created during setup
        self.volume_icon = None
        self.volume_line_bg = None
        self.volume_line_fg = None
        self.volume_circle = None
        self.volume_hitbox = None

    def setup_volume_control(self, volume_x_start, volume_slider_length=80):
        """Create and setup custom volume control slider."""
        self.volume_slider_width = volume_slider_length

        # Store the actual slider bounds (with padding for the circle)
        self.volume_slider_padding = self.volume_circle_radius
        self.volume_slider_start = volume_x_start + self.volume_slider_padding
        self.volume_slider_end = volume_x_start + self.volume_slider_width

        # Store the visual bounds (where the line is drawn)
        self.volume_line_start = volume_x_start
        self.volume_line_end = volume_x_start + self.volume_slider_width

        # Calculate initial volume position with padding
        volume_position = self.volume_slider_start + ((self.volume_slider_end - self.volume_slider_start) * 0.8)

        # Create volume icon
        self.volume_icon = tk.Label(
            self.canvas,
            text=self.button_symbols['volume'],
            font=('TkDefaultFont', 12),
            bg=self.theme_config['colors']['bg'],
            fg=self.theme_config['colors']['primary']
        )
        self.volume_icon.place(x=volume_x_start - 25, y=self.bar_y - 10)  # Position icon to the left of slider

        # Create volume slider background line
        self.volume_line_bg = self.canvas.create_line(
            self.volume_line_start,
            self.bar_y,
            self.volume_line_end,
            self.bar_y,
            fill='#404040',  # Same color as progress bar background
            width=2 + 2,  # Same width as progress bar bg
        )

        # Create volume slider foreground line - white as requested
        self.volume_line_fg = self.canvas.create_line(
            self.volume_line_start,
            self.bar_y,
            volume_position,
            self.bar_y,
            fill='white',  # White color as requested
            width=2,  # Same width as progress bar
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
        if not self.volume_dragging:
            return

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

    def set_volume(self, volume):
        """Set the volume value and update the slider position."""
        self.volume_value = max(0, min(volume, 100))
        self._update_volume_slider_position()

    def get_volume(self):
        """Get the current volume value."""
        return self.volume_value

    def update_positions(self, volume_x_start):
        """Update the positions of volume control elements on resize."""
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
