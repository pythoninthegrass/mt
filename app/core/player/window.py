"""Window management for the music player - handles geometry, position, and preferences."""

from core.logging import controls_logger, log_player_action
from eliot import start_action
from time import time


class PlayerWindowManager:
    """Manages window state, geometry, position, and UI preferences persistence."""

    def __init__(self, window, db, main_container, queue_view):
        """Initialize the window manager.

        Args:
            window: The main Tkinter window
            db: Database instance
            main_container: Main PanedWindow container
            queue_view: QueueView instance
        """
        self.window = window
        self.db = db
        self.main_container = main_container
        self.queue_view = queue_view
        self._startup_time: float = time()
        self._window_save_timer = None

    def load_window_position(self):
        """Load and apply saved window position."""
        if hasattr(self, 'db') and hasattr(self, 'window'):
            saved_position = self.db.get_window_position()
            if saved_position:
                try:
                    self.window.geometry(saved_position)
                    self.window.update()
                except Exception:
                    # If position is invalid, ignore it
                    pass

    def save_window_size(self, width, height):
        """Save window size to database."""
        # Only save reasonable window sizes
        if hasattr(self, 'db') and width > 100 and height > 100:
            self.db.set_window_size(width, height)

    def save_window_position(self):
        """Save window position to database."""
        if hasattr(self, 'db') and hasattr(self, 'window'):
            # Don't save position if window is maximized, minimized, or iconified
            state = self.window.wm_state()
            if state in ('zoomed', 'iconic', 'withdrawn'):
                return

            # Get current window position
            position = self.window.winfo_geometry()
            if position:
                self.db.set_window_position(position)

    def on_window_configure(self, event):
        """Handle window resize/configure events."""
        # Only save if this is the main window and not during initial setup
        if event.widget == self.window and hasattr(self, 'db'):
            # Skip saving if dimensions are too small (likely during initialization)
            if event.width <= 100 or event.height <= 100:
                return

            # Skip saving during the first few seconds after startup to avoid
            # overriding loaded preferences
            if time() - self._startup_time < 2.0:  # Skip for first 2 seconds
                return

            if self._window_save_timer:
                self.window.after_cancel(self._window_save_timer)

            # Save both size and position after 500ms of no resize events
            self._window_save_timer = self.window.after(
                500, lambda: (self.save_window_size(event.width, event.height), self.save_window_position())
            )

    def on_paned_resize(self, event):
        """Handle paned window resize (left panel width changes)."""
        with start_action(controls_logger, "panel_resize"):
            if hasattr(self, 'db'):
                # Get current sash position
                sash_pos = self.main_container.sashpos(0)
                if sash_pos > 0:
                    # Get existing panel width for comparison
                    existing_width = self.db.get_left_panel_width() or 0
                    window_geometry = self.window.geometry()

                    log_player_action(
                        "panel_resize",
                        trigger_source="user_drag",
                        old_panel_width=existing_width,
                        new_panel_width=sash_pos,
                        width_change=sash_pos - existing_width,
                        window_geometry=window_geometry,
                        panel_type="left_library_panel",
                        description=f"Left panel resized from {existing_width}px to {sash_pos}px",
                    )

                    self.db.set_left_panel_width(sash_pos)

    def save_column_widths(self, widths):
        """Save queue column widths for the current view."""
        with start_action(controls_logger, "save_column_preferences"):
            if hasattr(self, 'db') and hasattr(self, 'queue_view'):
                # Get current view name
                current_view = self.queue_view.current_view

                # Get existing widths for comparison
                existing_widths = self.db.get_queue_column_widths(current_view) or {}

                # Calculate what's actually being persisted
                persisted_changes = {}
                for col_name, width in widths.items():
                    old_width = existing_widths.get(col_name, 0)
                    if width != old_width:
                        persisted_changes[col_name] = {'old_width': old_width, 'new_width': width}
                        self.db.set_queue_column_width(col_name, width, current_view)

                log_player_action(
                    "column_preferences_saved",
                    trigger_source="periodic_check",
                    view=current_view,
                    widths_saved=widths,
                    existing_widths=existing_widths,
                    persisted_changes=persisted_changes,
                    columns_changed=len(persisted_changes),
                    total_columns=len(widths),
                    description=f"Column preferences persisted for {len(persisted_changes)} changed columns in {current_view} view",
                )

    def on_window_close(self, api_server=None):
        """Handle window close event - save final UI state.

        Args:
            api_server: Optional APIServer instance to stop before closing
        """
        # Save current column widths before closing
        if hasattr(self, 'queue_view') and hasattr(self.queue_view, 'queue'):
            columns = ['track', 'title', 'artist', 'album', 'year']
            for col in columns:
                try:
                    width = self.queue_view.queue.column(col, 'width')
                    self.db.set_queue_column_width(col, width)
                except Exception:
                    pass

        # Save final window size and position (only if window is not minimized/iconified)
        # Check if window is iconified (minimized)
        if hasattr(self, 'window') and self.window.wm_state() != 'iconic':
            geometry = self.window.geometry()
            # Parse geometry string like "1400x800+100+100"
            if 'x' in geometry:
                size_part = geometry.split('+')[0]  # Get "1400x800" part
                try:
                    width, height = size_part.split('x')
                    # Only save if dimensions are reasonable (not 1x1)
                    if int(width) > 100 and int(height) > 100:
                        self.db.set_window_size(int(width), int(height))
                except ValueError:
                    pass

            # Save final window position
            self.save_window_position()

        # Stop API server if provided and running
        if api_server:
            api_server.stop()

        # Close the window
        self.window.destroy()
