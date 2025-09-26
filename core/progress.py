import tkinter as tk


class ProgressControl:
    def __init__(self, canvas, config, command_callbacks):
        self.canvas = canvas
        self.config = config
        self.callbacks = command_callbacks
        self.bar_y = config['bar_y']
        self.circle_radius = config['circle_radius']
        self.controls_width = 0
        self.line = None
        self.progress_line = None
        self.progress_circle = None
        self.progress_hitbox = None
        self.track_info = None
        self.time_text = None
        self.dragging = False
        self.last_drag_time = 0
        self.playback_active = False  # Flag to track if playback is active

        self.setup_progress_bar()

    def setup_progress_bar(self):
        # Create track info text - positioned above progress line
        self.track_info = self.canvas.create_text(
            self.controls_width,  # Align with start of progress line
            self.config['track_info_y'],
            text="",  # Initialize with empty text
            fill=self.config['colors']['fg'],
            anchor=tk.W,
        )

        # Create time labels - moved to the left to make room for volume control
        self.time_text = self.canvas.create_text(
            self.canvas.winfo_width() - 380,  # Position before volume control and utility buttons
            self.config['time_label_y'],
            text="00:00 / 00:00",
            fill=self.config['colors']['fg'],
            anchor=tk.E,
        )

        # Create progress bar background (dark line) - always visible
        self.line = self.canvas.create_line(
            self.controls_width,
            self.bar_y,
            self.canvas.winfo_width() - 380,  # Make shorter to accommodate volume control and utility buttons
            self.bar_y,
            fill=self.config['progress_bg'],  # Use dark background color
            width=self.config['line_width'] + 2,  # Slightly wider for the background
        )

        # Create progress bar foreground (teal line) - initially hidden
        self.progress_line = self.canvas.create_line(
            self.controls_width,
            self.bar_y,
            self.controls_width,  # Initially same as start
            self.bar_y,
            fill=self.config['colors']['primary'],  # Teal color
            width=self.config['line_width'],
            state=tk.HIDDEN,  # Initially hidden
        )

        # Create progress circle with teal fill - initially hidden
        self.progress_circle = self.canvas.create_oval(
            self.controls_width - self.circle_radius,
            self.bar_y - self.circle_radius,
            self.controls_width + self.circle_radius,
            self.bar_y + self.circle_radius,
            fill=self.config['colors']['primary'],  # Teal fill
            outline=self.config['colors']['playhead_border'],  # Border to make it more visible
            state=tk.HIDDEN,  # Initially hidden
        )

        # Create invisible hitbox for the progress bar to handle clicks
        progress_end_x = self.canvas.coords(self.line)[2]
        self.progress_hitbox = self.canvas.create_rectangle(
            self.controls_width - 5,
            self.bar_y - 10,
            progress_end_x + 5,
            self.bar_y + 10,
            fill='',  # Transparent fill
            outline='',  # No outline
            tags=('progress_hitbox',),
        )

        # Bind click to the hitbox
        self.canvas.tag_bind('progress_hitbox', '<Button-1>', self.callbacks['click_progress'])

        # For progress circle, bind events but they won't work until it's visible
        self.canvas.tag_bind(self.progress_circle, '<Button-1>', self.callbacks['start_drag'])
        self.canvas.tag_bind(self.progress_circle, '<B1-Motion>', self.callbacks['drag'])
        self.canvas.tag_bind(self.progress_circle, '<ButtonRelease-1>', self.callbacks['end_drag'])

    def set_controls_width(self, width):
        """Set the width reserved for player controls"""
        self.controls_width = width
        self.update_positions()

    def update_positions(self):
        """Update the positions of progress elements after resize or settings change"""
        width = self.canvas.winfo_width()

        # Update progress line background (always visible)
        self.canvas.coords(
            self.line,
            self.controls_width,
            self.bar_y,
            width - 380,  # Make shorter to accommodate volume control and utility buttons
            self.bar_y,
        )

        # Update progress hitbox
        progress_end_x = self.canvas.coords(self.line)[2]
        self.canvas.coords(
            self.progress_hitbox,
            self.controls_width - 5,
            self.bar_y - 10,
            progress_end_x + 5,
            self.bar_y + 10,
        )

        # Update track info position
        self.canvas.coords(
            self.track_info,
            self.controls_width,
            self.config['track_info_y'],
        )

        # Update time label position
        self.canvas.coords(
            self.time_text,
            width - 380,
            self.config['time_label_y'],
        )

        # If playback is active, also update foreground elements
        if self.playback_active:
            # Get current position ratio if possible
            current_coords = self.canvas.coords(self.progress_line)
            if len(current_coords) == 4:
                total_width_before = self.canvas.coords(self.line)[2] - self.controls_width
                if total_width_before > 0:
                    current_ratio = (current_coords[2] - self.controls_width) / total_width_before

                    # Apply ratio to new width
                    new_total_width = width - 380 - self.controls_width
                    new_x = self.controls_width + (new_total_width * current_ratio)

                    # Update foreground line
                    self.canvas.coords(
                        self.progress_line,
                        self.controls_width,
                        self.bar_y,
                        new_x,
                        self.bar_y,
                    )

                    # Update circle
                    self.canvas.coords(
                        self.progress_circle,
                        new_x - self.circle_radius,
                        self.bar_y - self.circle_radius,
                        new_x + self.circle_radius,
                        self.bar_y + self.circle_radius,
                    )

    def show_playback_elements(self):
        """Show the playback elements when playback starts"""
        if not self.playback_active:
            self.playback_active = True
            self.canvas.itemconfigure(self.progress_line, state=tk.NORMAL)
            self.canvas.itemconfigure(self.progress_circle, state=tk.NORMAL)

            # Ensure proper z-order
            self.canvas.tag_raise(self.progress_line)  # Progress line above background
            self.canvas.tag_raise(self.progress_circle)  # Playhead circle on top of everything

            # Reset to beginning position
            self.update_progress(0)

    def hide_playback_elements(self):
        """Hide the playback elements when playback stops"""
        self.playback_active = False
        self.canvas.itemconfigure(self.progress_line, state=tk.HIDDEN)
        self.canvas.itemconfigure(self.progress_circle, state=tk.HIDDEN)

    def update_progress(self, ratio):
        """Update the position of the progress bar based on the current playback position"""
        # Show elements if they're hidden
        if not self.playback_active:
            self.show_playback_elements()

        if ratio < 0:
            ratio = 0
        elif ratio > 1:
            ratio = 1

        # Calculate the available width for the progress bar
        # This is the width between controls_width and the time display
        # We need to account for the volume control position
        width = self.canvas.winfo_width()
        max_progress_width = width - self.controls_width - 380  # 380 is space for time display, volume, and utility buttons

        # Calculate the x position based on the ratio
        x = self.controls_width + (max_progress_width * ratio)

        # Update circle position
        self.canvas.coords(
            self.progress_circle,
            x - self.circle_radius,
            self.bar_y - self.circle_radius,
            x + self.circle_radius,
            self.bar_y + self.circle_radius,
        )

        # Update progress line
        self.canvas.coords(
            self.progress_line,
            self.controls_width,
            self.bar_y,
            x,
            self.bar_y,
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

    def update_time_display(self, current_time, total_time):
        """Update the time display with formatted times"""
        self.canvas.itemconfig(self.time_text, text=f"{current_time} / {total_time}")
