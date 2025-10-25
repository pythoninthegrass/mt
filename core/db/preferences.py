import sqlite3
from core.logging import db_logger, log_database_operation


class PreferencesManager:
    """Manages user preferences, settings, and UI state."""

    def __init__(self, db_conn: sqlite3.Connection, db_cursor: sqlite3.Cursor):
        self.db_conn = db_conn
        self.db_cursor = db_cursor

    def get_loop_enabled(self) -> bool:
        """Get loop state from settings."""
        self.db_cursor.execute("SELECT value FROM settings WHERE key = 'loop_enabled'")
        result = self.db_cursor.fetchone()
        return bool(int(result[0])) if result else True

    def set_loop_enabled(self, enabled: bool):
        """Set loop state in settings."""
        self.db_cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('loop_enabled', ?)", (int(enabled),))
        self.db_conn.commit()

    def get_shuffle_enabled(self) -> bool:
        """Get shuffle state from settings."""
        self.db_cursor.execute("SELECT value FROM settings WHERE key = 'shuffle_enabled'")
        result = self.db_cursor.fetchone()
        return bool(int(result[0])) if result else False

    def set_shuffle_enabled(self, enabled: bool):
        """Set shuffle state in settings."""
        self.db_cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('shuffle_enabled', ?)", (int(enabled),))
        self.db_conn.commit()

    def get_volume(self) -> int:
        """Get volume from settings."""
        self.db_cursor.execute("SELECT value FROM settings WHERE key = 'volume'")
        result = self.db_cursor.fetchone()
        return int(result[0]) if result else 100

    def set_volume(self, volume: int):
        """Set volume in settings."""
        if 0 <= volume <= 100:
            self.db_cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('volume', ?)", (volume,))
            self.db_conn.commit()

    def get_ui_preference(self, key: str, default: str = '') -> str:
        """Get a UI preference value from settings."""
        self.db_cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = self.db_cursor.fetchone()
        return result[0] if result else default

    def set_ui_preference(self, key: str, value: str):
        """Set a UI preference value."""
        self.db_cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        self.db_conn.commit()

    def get_window_size(self) -> tuple[int, int] | None:
        """Get saved window size."""
        size_str = self.get_ui_preference('window_size')
        if size_str:
            try:
                width, height = size_str.split('x')
                return (int(width), int(height))
            except ValueError:
                pass
        return None

    def set_window_size(self, width: int, height: int):
        """Save window size."""
        self.set_ui_preference('window_size', f'{width}x{height}')

    def get_window_position(self) -> str | None:
        """Get saved window position."""
        return self.get_ui_preference('window_position')

    def set_window_position(self, position: str):
        """Save window position."""
        self.set_ui_preference('window_position', position)

    def get_left_panel_width(self) -> int | None:
        """Get left panel width from settings."""
        result = self.get_ui_preference('left_panel_width')
        return int(result) if result else None

    def set_left_panel_width(self, width: int):
        """Set left panel width in settings."""
        self.set_ui_preference('left_panel_width', str(width))

    def get_queue_column_widths(self, view: str = 'default') -> dict[str, int]:
        """Get saved queue column widths for a specific view."""
        widths = {}
        prefix = f'queue_col_{view}_'
        self.db_cursor.execute("SELECT key, value FROM settings WHERE key LIKE ?", (f'{prefix}%',))
        for key, value in self.db_cursor.fetchall():
            col_name = key.replace(prefix, '')
            try:
                widths[col_name] = int(value)
            except ValueError:
                pass
        return widths

    def set_queue_column_width(self, column: str, width: int, view: str = 'default'):
        """Save queue column width for a specific view."""
        self.set_ui_preference(f'queue_col_{view}_{column}', str(width))
