import os
import sqlite3
from core.logging import db_logger, log_database_operation, log_error
from pathlib import Path
from typing import Any, Optional

# Database initialization tables
# These tables are created when the database is first initialized
# and form the core schema of the music player
DB_TABLES = {
    'queue': '''
        CREATE TABLE IF NOT EXISTS queue
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         filepath TEXT NOT NULL)
    ''',
    'library': '''
        CREATE TABLE IF NOT EXISTS library
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         filepath TEXT NOT NULL,
         title TEXT,
         artist TEXT,
         album TEXT,
         album_artist TEXT,
         track_number TEXT,
         track_total TEXT,
         date TEXT,
         duration REAL,
         added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         last_played TIMESTAMP,
         play_count INTEGER DEFAULT 0)
    ''',
    'settings': '''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''',
    'favorites': '''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (track_id) REFERENCES library(id),
            UNIQUE(track_id)
        )
    ''',
}


class MusicDatabase:
    def __init__(self, db_name: str, db_tables: dict[str, str]):
        """Initialize database connection and create tables if they don't exist."""
        self.db_name = db_name
        self.db_conn = sqlite3.connect(db_name)
        self.db_cursor = self.db_conn.cursor()

        # Create tables
        for _, create_sql in db_tables.items():
            self.db_cursor.execute(create_sql)

        # Initialize settings with default values if they don't exist
        self.db_cursor.execute("SELECT COUNT(*) FROM settings WHERE key = 'loop_enabled'")
        if self.db_cursor.fetchone()[0] == 0:
            self.set_loop_enabled(True)  # Set default loop state

        self.db_cursor.execute("SELECT COUNT(*) FROM settings WHERE key = 'shuffle_enabled'")
        if self.db_cursor.fetchone()[0] == 0:
            self.set_shuffle_enabled(False)  # Set default shuffle state

        self.db_conn.commit()

    def close(self):
        """Close the database connection."""
        if hasattr(self, 'db_conn'):
            self.db_conn.close()

    def get_loop_enabled(self) -> bool:
        """Get loop state from settings."""
        self.db_cursor.execute("SELECT value FROM settings WHERE key = 'loop_enabled'")
        result = self.db_cursor.fetchone()
        return bool(int(result[0])) if result else True

    def set_loop_enabled(self, enabled: bool):
        """Set loop state in settings."""
        value = '1' if enabled else '0'
        self.db_cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('loop_enabled', ?)", (value,))
        self.db_conn.commit()

    def get_shuffle_enabled(self) -> bool:
        """Get shuffle state from settings."""
        self.db_cursor.execute("SELECT value FROM settings WHERE key = 'shuffle_enabled'")
        result = self.db_cursor.fetchone()
        return bool(int(result[0])) if result else False

    def set_shuffle_enabled(self, enabled: bool):
        """Set shuffle state in settings."""
        value = '1' if enabled else '0'
        self.db_cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('shuffle_enabled', ?)", (value,))
        self.db_conn.commit()

    def get_ui_preference(self, key: str, default: str = '') -> str:
        """Get a UI preference value from settings."""
        self.db_cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = self.db_cursor.fetchone()
        return result[0] if result else default

    def set_ui_preference(self, key: str, value: str):
        """Set a UI preference value in settings."""
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
        """Get saved left panel width."""
        width_str = self.get_ui_preference('left_panel_width')
        return int(width_str) if width_str else None

    def set_left_panel_width(self, width: int):
        """Save left panel width."""
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

    def get_existing_files(self) -> set:
        """Get set of all files currently in library."""
        self.db_cursor.execute('SELECT filepath FROM library')
        return {row[0] for row in self.db_cursor.fetchall()}

    def add_to_library(self, filepath: str, metadata: dict[str, Any]):
        """Add a file to the library with its metadata."""
        try:
            from core.logging import log_database_operation

            log_database_operation("INSERT", "library", filepath=filepath, title=metadata.get('title'))
        except ImportError:
            pass

        self.db_cursor.execute(
            '''
            INSERT INTO library
            (filepath, title, artist, album, album_artist,
            track_number, track_total, date, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
            (
                filepath,
                metadata.get('title'),
                metadata.get('artist'),
                metadata.get('album'),
                metadata.get('album_artist'),
                metadata.get('track_number'),
                metadata.get('track_total'),
                metadata.get('date'),
                metadata.get('duration'),
            ),
        )
        self.db_conn.commit()

        try:
            from core.logging import db_logger
            from eliot import log_message

            log_message(
                message_type="library_add_success", filepath=filepath, title=metadata.get('title'), artist=metadata.get('artist')
            )
        except ImportError:
            pass

    def add_to_queue(self, filepath: str):
        """Add a file to the queue."""
        self.db_cursor.execute('INSERT INTO queue (filepath) VALUES (?)', (filepath,))
        self.db_conn.commit()

    def get_queue_items(self) -> list[tuple]:
        """Get all items in the queue with their metadata."""
        self.db_cursor.execute('''
            SELECT q.filepath, l.artist, l.title, l.album, l.track_number, l.date
            FROM queue q
            LEFT JOIN library l ON q.filepath = l.filepath
            ORDER BY q.id
        ''')
        return self.db_cursor.fetchall()

    def get_library_items(self) -> list[tuple]:
        """Get all items in the library with their metadata."""
        self.db_cursor.execute('''
            WITH RECURSIVE
            -- First, get the track number as an integer for sorting
            parsed_tracks AS (
                SELECT
                    id,
                    filepath,
                    artist,
                    title,
                    album,
                    track_number,
                    date,
                    CASE
                        WHEN track_number IS NULL THEN 999999
                        WHEN track_number LIKE '%/%' THEN CAST(substr(track_number, 1, instr(track_number, '/') - 1) AS INTEGER)
                        ELSE CAST(track_number AS INTEGER)
                    END as track_num_int
                FROM library
            ),
            -- Then, deduplicate based on metadata while keeping the first added version
            deduped AS (
                SELECT
                    filepath,
                    artist,
                    title,
                    album,
                    track_number,
                    date,
                    track_num_int,
                    ROW_NUMBER() OVER (
                        PARTITION BY
                            LOWER(COALESCE(title, '')),
                            LOWER(COALESCE(artist, '')),
                            LOWER(COALESCE(album, '')),
                            COALESCE(track_number, '')
                        ORDER BY id ASC
                    ) as rn
                FROM parsed_tracks
            )
            -- Finally, select and sort the deduplicated results
            SELECT
                filepath,
                artist,
                title,
                album,
                track_number,
                date
            FROM deduped
            WHERE rn = 1
            ORDER BY
                CASE WHEN artist IS NULL THEN 1 ELSE 0 END,
                LOWER(COALESCE(artist, '')),
                CASE WHEN album IS NULL THEN 1 ELSE 0 END,
                LOWER(COALESCE(album, '')),
                track_num_int,
                LOWER(COALESCE(title, ''))
        ''')
        return self.db_cursor.fetchall()

    def find_file_by_metadata(
        self, title: str, artist: str | None = None, album: str | None = None, track_num: str | None = None
    ) -> str | None:
        """Find a file in the library based on its metadata."""
        # First try exact match
        query = '''
            SELECT filepath FROM library
            WHERE (
                (title = ? OR (title IS NULL AND ? = '')) AND
                (artist = ? OR (artist IS NULL AND ? = '')) AND
                (album = ? OR (album IS NULL AND ? = '')) AND
                (CASE
                    WHEN ? != '' THEN
                        CASE
                            WHEN track_number LIKE '%/%'
                            THEN printf('%02d', CAST(substr(track_number, 1, instr(track_number, '/') - 1) AS INTEGER)) = ?
                            ELSE printf('%02d', CAST(track_number AS INTEGER)) = ?
                        END
                    ELSE track_number IS NULL
                END)
            )
        '''
        self.db_cursor.execute(
            query, (title, title, artist, artist, album, album, track_num or '', track_num or '', track_num or '')
        )
        result = self.db_cursor.fetchone()

        # If no exact match, try matching just the title (for playback compatibility)
        if not result:
            query = '''
                SELECT filepath FROM library
                WHERE LOWER(title) = LOWER(?)
                LIMIT 1
            '''
            self.db_cursor.execute(query, (title,))
            result = self.db_cursor.fetchone()

        return result[0] if result else None

    def find_file_by_metadata_strict(
        self, title: str, artist: str | None = None, album: str | None = None, track_num: str | None = None
    ) -> str | None:
        """Find a file in the library based on exact metadata match only (no fallback).
        
        This is used for highlighting currently playing tracks to avoid false matches
        when multiple versions of the same song exist.
        """
        query = '''
            SELECT filepath FROM library
            WHERE (
                (title = ? OR (title IS NULL AND ? = '')) AND
                (artist = ? OR (artist IS NULL AND ? = '')) AND
                (album = ? OR (album IS NULL AND ? = '')) AND
                (CASE
                    WHEN ? != '' THEN
                        CASE
                            WHEN track_number LIKE '%/%'
                            THEN printf('%02d', CAST(substr(track_number, 1, instr(track_number, '/') - 1) AS INTEGER)) = ?
                            ELSE printf('%02d', CAST(track_number AS INTEGER)) = ?
                        END
                    ELSE track_number IS NULL
                END)
            )
        '''
        self.db_cursor.execute(
            query, (title, title, artist, artist, album, album, track_num or '', track_num or '', track_num or '')
        )
        result = self.db_cursor.fetchone()

        return result[0] if result else None

    def find_file_in_queue(self, title: str, artist: str | None = None) -> str | None:
        """Find a file in the queue based on its metadata."""
        query = '''
            SELECT q.filepath, l.title, l.artist, l.album, l.track_number
            FROM queue q
            JOIN library l ON q.filepath = l.filepath
            WHERE LOWER(l.title) = LOWER(?)
            AND (LOWER(l.artist) = LOWER(?) OR l.artist IS NULL OR ? = '')
            ORDER BY q.id
            LIMIT 1
        '''
        self.db_cursor.execute(query, (title, artist or '', artist or ''))
        result = self.db_cursor.fetchone()
        return result[0] if result else None

    def search_library(self, search_text):
        """Search library items by text across artist, title, and album."""
        search_term = f'%{search_text}%'
        query = '''
            SELECT filepath, artist, title, album, track_number, date
            FROM library 
            WHERE artist LIKE ? OR title LIKE ? OR album LIKE ?
            ORDER BY artist, album, CAST(track_number AS INTEGER)
        '''
        self.db_cursor.execute(query, (search_term, search_term, search_term))
        return self.db_cursor.fetchall()

    def search_queue(self, search_text):
        """Search queue items by text across artist, title, and album."""
        search_term = f'%{search_text}%'
        query = '''
            SELECT filepath, artist, title, album, track_number, date
            FROM queue 
            WHERE artist LIKE ? OR title LIKE ? OR album LIKE ?
            ORDER BY id
        '''
        self.db_cursor.execute(query, (search_term, search_term, search_term))
        return self.db_cursor.fetchall()

    def get_library_statistics(self) -> dict[str, Any]:
        """Get comprehensive library statistics including file count, size, and total duration."""
        from typing import Any
        
        stats = {
            'file_count': 0,
            'total_size_bytes': 0,
            'total_duration_seconds': 0
        }
        
        try:
            # Get file count
            count_query = "SELECT COUNT(*) FROM library"
            self.db_cursor.execute(count_query)
            stats['file_count'] = self.db_cursor.fetchone()[0]
            
            # Get all file paths and durations to calculate size and total duration
            files_query = "SELECT filepath, duration FROM library"
            self.db_cursor.execute(files_query)
            files = self.db_cursor.fetchall()
            
            total_size = 0
            total_duration = 0.0
            
            for filepath, duration in files:
                # Calculate file size
                try:
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath)
                        total_size += file_size
                except (OSError, TypeError):
                    # Skip files that can't be accessed or don't exist
                    continue
                
                # Add duration (handle None values)
                if duration and isinstance(duration, (int, float)):
                    total_duration += float(duration)
            
            stats['total_size_bytes'] = total_size
            stats['total_duration_seconds'] = int(total_duration)
            
        except Exception as e:
            print(f"Error calculating library statistics: {e}")
            # Return empty stats on error
            pass
        
        return stats

    def remove_from_queue(self, title: str, artist: str | None = None, album: str | None = None, track_num: str | None = None):
        """Remove a song from the queue based on its metadata."""
        self.db_cursor.execute(
            '''
            DELETE FROM queue
            WHERE filepath IN (
                SELECT filepath FROM library
                WHERE (
                    (title = ? OR (title IS NULL AND ? = '')) AND
                    (artist = ? OR (artist IS NULL AND ? = '')) AND
                    (album = ? OR (album IS NULL AND ? = '')) AND
                    (CASE
                        WHEN ? != '' THEN
                            CASE
                                WHEN track_number LIKE '%/%'
                                THEN printf('%02d', CAST(substr(track_number, 1, instr(track_number, '/') - 1) AS INTEGER)) = ?
                                ELSE printf('%02d', CAST(track_number AS INTEGER)) = ?
                            END
                        ELSE track_number IS NULL
                    END)
                )
            )
        ''',
            (title, title, artist, artist, album, album, track_num or '', track_num or '', track_num or ''),
        )
        self.db_conn.commit()

    def delete_from_library(self, filepath: str) -> bool:
        """Delete a track from the library by its filepath.
        
        Args:
            filepath: The absolute path to the file to remove from library
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            from eliot import log_message
            
            # Delete from library
            self.db_cursor.execute('DELETE FROM library WHERE filepath = ?', (filepath,))
            
            # Also delete from favorites if it exists
            self.db_cursor.execute('''
                DELETE FROM favorites 
                WHERE track_id IN (SELECT id FROM library WHERE filepath = ?)
            ''', (filepath,))
            
            # Commit the changes
            self.db_conn.commit()
            
            log_message(
                message_type="library_delete",
                filepath=filepath,
                message="Track deleted from library"
            )
            
            return True
            
        except Exception as e:
            print(f"Error deleting from library: {e}")
            try:
                from core.logging import library_logger, log_error
                log_error(library_logger, e, filepath=filepath)
            except ImportError:
                pass
            return False

    def update_play_count(self, filepath: str):
        """Increment play count for a song."""
        query = """
            UPDATE library SET
                play_count = play_count + 1,
                last_played = CURRENT_TIMESTAMP
            WHERE filepath = ?
        """
        self.db_cursor.execute(query, (filepath,))
        self.db_conn.commit()

    def get_metadata_by_filepath(self, filepath: str) -> dict:
        """Get metadata for a file by its path."""
        query = """
            SELECT title, artist, album, track_number, date
            FROM library
            WHERE filepath = ?
        """
        self.db_cursor.execute(query, (filepath,))
        result = self.db_cursor.fetchone()

        if result:
            return {'title': result[0], 'artist': result[1], 'album': result[2], 'track_number': result[3], 'date': result[4]}
        return {}

    def find_song_by_title_artist(self, title: str, artist: str | None = None) -> tuple[str, str, str, str, str] | None:
        """Find a song in the library by title and artist.

        Returns:
            Optional[Tuple[str, str, str, str, str]]: (filepath, title, artist, album, track_number) or None if not found
        """
        # First try exact match
        query = '''
            SELECT filepath, title, artist, album, track_number
            FROM library
            WHERE LOWER(title) = LOWER(?)
            AND (LOWER(artist) = LOWER(?) OR artist IS NULL OR ? = '')
            LIMIT 1
        '''
        self.db_cursor.execute(query, (title, artist or '', artist or ''))
        result = self.db_cursor.fetchone()

        # If no exact match, try matching just the title
        if not result:
            query = '''
                SELECT filepath, title, artist, album, track_number
                FROM library
                WHERE LOWER(title) = LOWER(?)
                LIMIT 1
            '''
            self.db_cursor.execute(query, (title,))
            result = self.db_cursor.fetchone()

        # If still no match, try fuzzy match
        if not result:
            query = '''
                SELECT filepath, title, artist, album, track_number
                FROM library
                WHERE LOWER(title) LIKE LOWER(?)
                OR LOWER(filepath) LIKE LOWER(?)
                LIMIT 1
            '''
            self.db_cursor.execute(query, (f"%{title}%", f"%{title}%"))
            result = self.db_cursor.fetchone()

        return result

    def is_duplicate(self, metadata: dict[str, Any], filepath: str | None = None) -> bool:
        """Check if a track with the same metadata already exists in the library.

        Returns:
            bool: True if a duplicate exists, False otherwise
        """
        # First check if the exact filepath exists
        if filepath:
            self.db_cursor.execute('SELECT COUNT(*) FROM library WHERE filepath = ?', (filepath,))
            if self.db_cursor.fetchone()[0] > 0:
                return True

        # Only check for duplicate if we have substantial metadata
        # A track needs at least title AND (artist OR album) to be considered a duplicate
        has_title = bool(metadata.get('title'))
        has_artist = bool(metadata.get('artist'))
        has_album = bool(metadata.get('album'))

        # If we only have a title (likely from filename), don't consider it a duplicate
        if has_title and not has_artist and not has_album:
            return False

        # Build query based on available metadata
        query_parts = []
        params = []

        if has_title:
            query_parts.append('LOWER(title) = LOWER(?)')
            params.append(metadata['title'])

        if has_artist:
            query_parts.append('LOWER(artist) = LOWER(?)')
            params.append(metadata['artist'])

        if has_album:
            query_parts.append('LOWER(album) = LOWER(?)')
            params.append(metadata['album'])

        if metadata.get('track_number'):
            query_parts.append('track_number = ?')
            params.append(metadata['track_number'])

        # Include date to differentiate between different releases/remasters
        if metadata.get('date'):
            query_parts.append('LOWER(COALESCE(date, "")) = LOWER(?)')
            params.append(metadata['date'])

        # Include album_artist to differentiate compilations vs original releases
        if metadata.get('album_artist'):
            query_parts.append('LOWER(COALESCE(album_artist, "")) = LOWER(?)')
            params.append(metadata['album_artist'])

        if metadata.get('duration'):
            # Allow 1 second tolerance for duration comparison
            query_parts.append('ABS(duration - ?) < 1')
            params.append(metadata['duration'])

        if not query_parts:
            return False

        query = f'''
            SELECT COUNT(*) FROM library
            WHERE {' AND '.join(query_parts)}
        '''

        self.db_cursor.execute(query, params)
        count = self.db_cursor.fetchone()[0]
        return count > 0

    def add_favorite(self, filepath: str) -> bool:
        """Add a track to favorites by its filepath.

        Args:
            filepath: Path to the track file

        Returns:
            bool: True if added successfully, False if track not in library or already favorited
        """
        try:
            # Get track_id from library
            self.db_cursor.execute('SELECT id FROM library WHERE filepath = ?', (filepath,))
            result = self.db_cursor.fetchone()

            if not result:
                return False

            track_id = result[0]

            # Insert into favorites (UNIQUE constraint prevents duplicates)
            self.db_cursor.execute(
                'INSERT INTO favorites (track_id) VALUES (?)',
                (track_id,)
            )
            self.db_conn.commit()

            try:
                from eliot import log_message
                log_message(message_type="favorite_added", filepath=filepath, track_id=track_id)
            except ImportError:
                pass

            return True

        except sqlite3.IntegrityError:
            # Already favorited
            return False
        except Exception as e:
            try:
                from core.logging import log_error
                log_error(e, "Failed to add favorite", filepath=filepath)
            except ImportError:
                pass
            return False

    def remove_favorite(self, filepath: str) -> bool:
        """Remove a track from favorites by its filepath.

        Args:
            filepath: Path to the track file

        Returns:
            bool: True if removed successfully, False if not found
        """
        try:
            # Get track_id from library
            self.db_cursor.execute('SELECT id FROM library WHERE filepath = ?', (filepath,))
            result = self.db_cursor.fetchone()

            if not result:
                return False

            track_id = result[0]

            # Remove from favorites
            self.db_cursor.execute('DELETE FROM favorites WHERE track_id = ?', (track_id,))
            affected_rows = self.db_cursor.rowcount
            self.db_conn.commit()

            try:
                from eliot import log_message
                log_message(message_type="favorite_removed", filepath=filepath, track_id=track_id)
            except ImportError:
                pass

            return affected_rows > 0

        except Exception as e:
            try:
                from core.logging import log_error
                log_error(e, "Failed to remove favorite", filepath=filepath)
            except ImportError:
                pass
            return False

    def is_favorite(self, filepath: str) -> bool:
        """Check if a track is in favorites.

        Args:
            filepath: Path to the track file

        Returns:
            bool: True if track is favorited, False otherwise
        """
        try:
            query = '''
                SELECT COUNT(*) FROM favorites f
                JOIN library l ON f.track_id = l.id
                WHERE l.filepath = ?
            '''
            self.db_cursor.execute(query, (filepath,))
            count = self.db_cursor.fetchone()[0]
            return count > 0
        except Exception:
            return False

    def get_liked_songs(self) -> list[tuple]:
        """Get all favorited tracks with their metadata, ordered by favorite timestamp (FIFO).

        Returns:
            list[tuple]: List of (filepath, artist, title, album, track_number, date) tuples
        """
        try:
            query = '''
                SELECT l.filepath, l.artist, l.title, l.album, l.track_number, l.date
                FROM favorites f
                JOIN library l ON f.track_id = l.id
                ORDER BY f.timestamp ASC
            '''
            self.db_cursor.execute(query)
            return self.db_cursor.fetchall()
        except Exception as e:
            try:
                from core.logging import log_error
                log_error(e, "Failed to get liked songs")
            except ImportError:
                pass
            return []

    def get_top_25_most_played(self) -> list[tuple]:
        """Get top 25 most played tracks with their metadata, ordered by play count (descending).

        Returns:
            list[tuple]: List of (filepath, artist, title, album, play_count, date) tuples
        """
        try:
            query = '''
                SELECT filepath, artist, title, album, play_count, date
                FROM library
                WHERE play_count > 0
                ORDER BY play_count DESC, last_played DESC
                LIMIT 25
            '''
            self.db_cursor.execute(query)
            return self.db_cursor.fetchall()
        except Exception as e:
            try:
                from core.logging import log_error
                log_error(e, "Failed to get top 25 most played")
            except ImportError:
                pass
            return []
