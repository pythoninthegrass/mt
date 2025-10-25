import contextlib
import customtkinter as ctk
import tkinter as tk
import tkinter.font as tkfont
from config import (
    BUTTON_SYMBOLS,
    COLORS,
    PROGRESS_BAR,
    THEME_CONFIG,
)
from core.controls import PlayerCore
from core.gui.player_controls import PlayerControls
from core.progress import ProgressControl
from core.volume import VolumeControl
from tkinter import ttk
from utils.icons import load_icon

class ProgressBar:
    def __init__(self, window, progress_frame, callbacks, initial_loop_enabled=True, initial_shuffle_enabled=False, initial_volume=100):
        self.window = window
        self.progress_frame = progress_frame
        self.callbacks = callbacks
        self.initial_loop_enabled = initial_loop_enabled
        self.initial_shuffle_enabled = initial_shuffle_enabled
        self.initial_volume = initial_volume
        self.setup_progress_bar()
        self.setup_volume_control()

    def setup_progress_bar(self):
        # Create canvas for custom progress bar
        self.canvas = tk.Canvas(
            self.progress_frame,
            height=PROGRESS_BAR['canvas_height'],
            background="#000000",  # Pure black like search bar
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.X)

        # Create controls with initial loop and shuffle state
        self.controls = PlayerControls(
            self.canvas,
            self.callbacks,
            initial_loop_enabled=self.initial_loop_enabled,
            initial_shuffle_enabled=self.initial_shuffle_enabled,
        )
        self.controls_width = self.controls.controls_width

        # Create progress bar control
        self.progress_control = ProgressControl(
            self.canvas,
            {
                'bar_y': PROGRESS_BAR['bar_y'],
                'circle_radius': PROGRESS_BAR['circle_radius'],
                'line_width': PROGRESS_BAR['line_width'],
                'colors': THEME_CONFIG['colors'],
                'progress_bg': PROGRESS_BAR['progress_bg'],
                'time_label_y': PROGRESS_BAR['time_label_y'],
                'track_info_y': PROGRESS_BAR['track_info_y'],
            },
            {
                'start_drag': self.callbacks['start_drag'],
                'drag': self.callbacks['drag'],
                'end_drag': self.callbacks['end_drag'],
                'click_progress': self.callbacks['click_progress'],
            },
        )
        self.progress_control.set_controls_width(self.controls_width)

        # Define properties for backwards compatibility
        self.bar_y = PROGRESS_BAR['bar_y']
        self.circle_radius = PROGRESS_BAR['circle_radius']
        self.line = self.progress_control.line
        self.progress_line = self.progress_control.progress_line
        self.progress_circle = self.progress_control.progress_circle
        self.time_text = self.progress_control.time_text
        self.track_info = self.progress_control.track_info
        self.dragging = False
        self.last_drag_time = 0

        # For compatibility with existing code
        self.progress_hitbox = self.progress_control.progress_hitbox

        # Bind window resize
        self.canvas.bind('<Configure>', self.on_resize)

    def setup_volume_control(self):
        """Create and setup custom volume control slider."""
        # Wait for canvas to be ready and get current dimensions
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Calculate positions with proper spacing
        progress_end_x = self.canvas.coords(self.line)[2]  # End of progress line
        utility_controls_width = self.controls.utility_width  # Width reserved for loop and add buttons

        # Position volume control relative to shuffle button position (leftmost utility control)
        shuffle_button_x = canvas_width - 180  # Same positioning as utility controls
        volume_end_x = shuffle_button_x - 60  # Fixed spacing before shuffle button

        # Calculate volume start position
        volume_x_start = progress_end_x + 45  # Fixed spacing after progress bar

        # Calculate available space for volume slider
        available_space = volume_end_x - volume_x_start
        volume_slider_length = max(80, min(120, available_space - 30))  # 30 for volume icon, constrain between 80-120px

        # Calculate centered y position to match utility controls, lowered by 15%
        # Utility controls are centered at (canvas_height - utility_icon_size[1]) // 2 + utility_icon_size[1] // 2
        volume_bar_y = int(canvas_height // 2 * 1.10)  # Center of canvas, lowered by 10%

        # Create volume control with initial volume from database
        self.volume_control = VolumeControl(
            self.canvas,
            volume_bar_y,
            self.circle_radius,
            BUTTON_SYMBOLS,
            THEME_CONFIG,
            {'volume_change': self.callbacks['volume_change']},
        )
        self.volume_control.setup_volume_control(volume_x_start, volume_slider_length, initial_volume=self.initial_volume)

        # Add properties for backwards compatibility
        self.volume_circle = self.volume_control.volume_circle
        self.volume_dragging = False
        self.volume_value = self.initial_volume
        self.volume_x_start = volume_x_start
        self.volume_line_bg = self.volume_control.volume_line_bg
        self.volume_line_fg = self.volume_control.volume_line_fg
        self.volume_slider_width = self.volume_control.volume_slider_width
        self.volume_circle_radius = self.volume_control.volume_circle_radius
        self.volume_hitbox = self.volume_control.volume_hitbox
        self.volume_icon = self.volume_control.volume_icon

    def on_resize(self, event):
        """Handle window resize."""
        # Update control button positions first
        if hasattr(self, 'controls'):
            # The controls _on_canvas_resize method will update controls_width
            self.controls._on_canvas_resize(event)
            # Update progress control with new controls width
            self.progress_control.set_controls_width(self.controls.controls_width)

        # Update progress bar positions
        self.progress_control.update_positions()

        # Calculate positions for volume control, accounting for utility controls
        progress_end_x = self.canvas.coords(self.line)[2]
        canvas_width = event.width
        canvas_height = event.height
        utility_controls_width = self.controls.utility_width  # Width reserved for loop and add buttons

        # Position volume control relative to shuffle button position (leftmost utility control)
        shuffle_button_x = canvas_width - 180  # Same positioning as utility controls
        volume_end_x = shuffle_button_x - 60  # Fixed spacing before shuffle button

        # Calculate volume start position
        volume_x_start = progress_end_x + 45  # Fixed spacing after progress bar

        # Calculate available space for volume slider
        available_space = volume_end_x - volume_x_start
        volume_slider_length = max(80, min(120, available_space - 30))  # 30 for volume icon, constrain between 80-120px

        # Update volume control positions with centered y position
        if hasattr(self, 'volume_control'):
            # Update the bar_y to keep it centered
            volume_bar_y = canvas_height // 2
            self.volume_control.bar_y = volume_bar_y
            self.volume_control.update_positions(volume_x_start)

    def update_track_info(self, title=None, artist=None):
        """Update the track info display."""
        self.progress_control.update_track_info(title, artist)

    def clear_track_info(self):
        """Clear the track info display."""
        self.progress_control.clear_track_info()




class StatusBar:
    def __init__(self, parent, library_manager):
        self.parent = parent
        self.library_manager = library_manager

        # Use monospace font for statistics display to prevent horizontal movement
        # SF Mono is available on macOS, CustomTkinter will handle font fallback
        self.stats_font = ("SF Mono", 12)

        self.setup_status_bar()

    def setup_status_bar(self):
        """Create status bar spanning entire bottom pane."""
        from config import COLORS

        # Create status bar container - continuous bar across full width
        self.status_bar = ctk.CTkFrame(
            self.parent,
            height=20,
            corner_radius=0,
            fg_color=COLORS['status_bar_bg'],  # #272931
            border_width=0,
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)
        self.status_bar.pack_propagate(False)

        # Status label with library statistics - right-justified
        # Use monospace font to prevent horizontal shifting when numbers change
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Loading library statistics...",
            font=self.stats_font,
            text_color="#CCCCCC",  # Light gray text
            anchor="e",  # Right-aligned text
        )
        self.status_label.pack(side=tk.RIGHT, padx=10, pady=5)

        # Initial statistics load
        self.update_statistics()

    def format_file_size(self, size_bytes):
        """Convert bytes to human readable format (GB)."""
        if size_bytes == 0:
            return "0.0 GB"

        gb_size = size_bytes / (1024**3)
        return f"{gb_size:.1f} GB"

    def format_duration(self, total_seconds):
        """Convert total seconds to d h m format."""
        if total_seconds <= 0:
            return "0d 0h 0m"

        days = int(total_seconds // 86400)  # 86400 seconds in a day
        remaining_seconds = total_seconds % 86400
        hours = int(remaining_seconds // 3600)
        minutes = int((remaining_seconds % 3600) // 60)

        return f"{days}d {hours}h {minutes}m"

    def format_file_count(self, count):
        """Format file count with commas for readability."""
        return f"{count:,}"

    def get_library_statistics(self):
        """Get comprehensive library statistics."""
        stats = self.library_manager.get_library_statistics()
        return {
            'file_count': stats.get('file_count', 0),
            'total_size_bytes': stats.get('total_size_bytes', 0),
            'total_duration_seconds': stats.get('total_duration_seconds', 0),
        }

    def update_statistics(self):
        """Update the status bar with current library statistics."""
        try:
            stats = self.get_library_statistics()

            file_count_str = self.format_file_count(stats['file_count'])
            size_str = self.format_file_size(stats['total_size_bytes'])
            duration_str = self.format_duration(stats['total_duration_seconds'])

            status_text = f"{file_count_str} files{'':<2}{size_str}{'':<2}{duration_str}"
            self.status_label.configure(text=status_text)

        except Exception:
            self.status_label.configure(text="Unable to load library statistics")

    def refresh_statistics(self):
        """Manually refresh the statistics (useful after library scan)."""
        self.update_statistics()




