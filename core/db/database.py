"""Main database facade class."""
import sqlite3
from core.db.favorites import FavoritesManager
from core.db.library import LibraryManager
from core.db.preferences import PreferencesManager
from core.db.queue import QueueManager


class MusicDatabase:
    """Facade class providing unified interface to all database operations.

    This class delegates to specialized manager classes for different domains:
    - PreferencesManager: User settings, preferences, UI state
    - LibraryManager: Music library, tracks, metadata
    - QueueManager: Playback queue operations
    - FavoritesManager: Favorite tracks and special views
    """

    def __init__(self, db_name: str, db_tables: dict[str, str]):
        """Initialize database connection and create tables if they don't exist."""
        self.db_name = db_name
        self.db_conn = sqlite3.connect(db_name)
        self.db_cursor = self.db_conn.cursor()

        # Create tables
        for _, create_sql in db_tables.items():
            self.db_cursor.execute(create_sql)

        # Initialize sub-managers
        self._preferences = PreferencesManager(self.db_conn, self.db_cursor)
        self._library = LibraryManager(self.db_conn, self.db_cursor)
        self._queue = QueueManager(self.db_conn, self.db_cursor)
        self._favorites = FavoritesManager(self.db_conn, self.db_cursor)

        # Initialize settings with default values if they don't exist
        self.db_cursor.execute("SELECT COUNT(*) FROM settings WHERE key = 'loop_enabled'")
        if self.db_cursor.fetchone()[0] == 0:
            self.set_loop_enabled(True)  # Set default loop state

        self.db_cursor.execute("SELECT COUNT(*) FROM settings WHERE key = 'shuffle_enabled'")
        if self.db_cursor.fetchone()[0] == 0:
            self.set_shuffle_enabled(False)  # Set default shuffle state

        self.db_cursor.execute("SELECT COUNT(*) FROM settings WHERE key = 'volume'")
        if self.db_cursor.fetchone()[0] == 0:
            self.set_volume(100)  # Set default volume to 100%

        self.db_conn.commit()

    def close(self):
        """Close the database connection."""
        if hasattr(self, 'db_conn'):
            self.db_conn.close()

    # Preferences delegation methods
    def get_loop_enabled(self) -> bool:
        return self._preferences.get_loop_enabled()

    def set_loop_enabled(self, enabled: bool):
        self._preferences.set_loop_enabled(enabled)

    def get_shuffle_enabled(self) -> bool:
        return self._preferences.get_shuffle_enabled()

    def set_shuffle_enabled(self, enabled: bool):
        self._preferences.set_shuffle_enabled(enabled)

    def get_volume(self) -> int:
        return self._preferences.get_volume()

    def set_volume(self, volume: int):
        self._preferences.set_volume(volume)

    def get_ui_preference(self, key: str, default: str = '') -> str:
        return self._preferences.get_ui_preference(key, default)

    def set_ui_preference(self, key: str, value: str):
        self._preferences.set_ui_preference(key, value)

    def get_window_size(self) -> tuple[int, int] | None:
        return self._preferences.get_window_size()

    def set_window_size(self, width: int, height: int):
        self._preferences.set_window_size(width, height)

    def get_window_position(self) -> str | None:
        return self._preferences.get_window_position()

    def set_window_position(self, position: str):
        self._preferences.set_window_position(position)

    def get_left_panel_width(self) -> int | None:
        return self._preferences.get_left_panel_width()

    def set_left_panel_width(self, width: int):
        self._preferences.set_left_panel_width(width)

    def get_queue_column_widths(self, view: str = 'default') -> dict[str, int]:
        return self._preferences.get_queue_column_widths(view)

    def set_queue_column_width(self, column: str, width: int, view: str = 'default'):
        self._preferences.set_queue_column_width(column, width, view)

    # Library delegation methods
    def get_existing_files(self) -> set:
        return self._library.get_existing_files()

    def add_to_library(self, filepath: str, metadata: dict):
        self._library.add_to_library(filepath, metadata)

    def update_track_metadata(
        self,
        filepath: str,
        title: str | None,
        artist: str | None,
        album: str | None,
        album_artist: str | None,
        year: str | None,
        genre: str | None,
        track_number: str | None,
    ) -> bool:
        return self._library.update_track_metadata(filepath, title, artist, album, album_artist, year, genre, track_number)

    def get_library_items(self) -> list[tuple]:
        return self._library.get_library_items()

    def find_file_by_metadata(
        self, title: str, artist: str | None = None, album: str | None = None, track_num: str | None = None
    ) -> str | None:
        return self._library.find_file_by_metadata(title, artist, album, track_num)

    def find_file_by_metadata_strict(
        self, title: str, artist: str | None = None, album: str | None = None, track_num: str | None = None
    ) -> str | None:
        return self._library.find_file_by_metadata_strict(title, artist, album, track_num)

    def search_library(self, search_text):
        return self._library.search_library(search_text)

    def get_library_statistics(self) -> dict:
        return self._library.get_library_statistics()

    def delete_from_library(self, filepath: str) -> bool:
        return self._library.delete_from_library(filepath)

    def update_play_count(self, filepath: str):
        self._library.update_play_count(filepath)

    def get_metadata_by_filepath(self, filepath: str) -> dict:
        return self._library.get_metadata_by_filepath(filepath)

    def get_track_by_filepath(self, filepath: str) -> tuple | None:
        return self._library.get_track_by_filepath(filepath)

    def find_song_by_title_artist(self, title: str, artist: str | None = None) -> tuple[str, str, str, str, str] | None:
        return self._library.find_song_by_title_artist(title, artist)

    def is_duplicate(self, metadata: dict, filepath: str | None = None) -> bool:
        return self._library.is_duplicate(metadata, filepath)

    # Queue delegation methods
    def add_to_queue(self, filepath: str):
        self._queue.add_to_queue(filepath)

    def get_queue_items(self) -> list[tuple]:
        return self._queue.get_queue_items()

    def find_file_in_queue(self, title: str, artist: str | None = None) -> str | None:
        return self._queue.find_file_in_queue(title, artist)

    def search_queue(self, search_text):
        return self._queue.search_queue(search_text)

    def remove_from_queue(self, title: str, artist: str | None = None, album: str | None = None, track_num: str | None = None):
        self._queue.remove_from_queue(title, artist, album, track_num)

    def clear_queue(self):
        self._queue.clear_queue()

    # Favorites delegation methods
    def add_favorite(self, filepath: str) -> bool:
        return self._favorites.add_favorite(filepath)

    def remove_favorite(self, filepath: str) -> bool:
        return self._favorites.remove_favorite(filepath)

    def is_favorite(self, filepath: str) -> bool:
        return self._favorites.is_favorite(filepath)

    def get_liked_songs(self) -> list[tuple]:
        return self._favorites.get_liked_songs()

    def get_top_25_most_played(self) -> list[tuple]:
        return self._favorites.get_top_25_most_played()

    def get_recently_added(self) -> list[tuple]:
        return self._favorites.get_recently_added()

    def get_recently_played(self) -> list[tuple]:
        return self._favorites.get_recently_played()
