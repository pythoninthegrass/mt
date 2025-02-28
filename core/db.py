import os
import sqlite3
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
    '''
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
        self.db_cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('loop_enabled', ?)",
            (value,)
        )
        self.db_conn.commit()

    def get_existing_files(self) -> set:
        """Get set of all files currently in library."""
        self.db_cursor.execute('SELECT filepath FROM library')
        return {row[0] for row in self.db_cursor.fetchall()}

    def add_to_library(self, filepath: str, metadata: dict[str, Any]):
        """Add a file to the library with its metadata."""
        self.db_cursor.execute('''
            INSERT INTO library
            (filepath, title, artist, album, album_artist,
            track_number, track_total, date, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            filepath,
            metadata.get('title'),
            metadata.get('artist'),
            metadata.get('album'),
            metadata.get('album_artist'),
            metadata.get('track_number'),
            metadata.get('track_total'),
            metadata.get('date'),
            metadata.get('duration')
        ))
        self.db_conn.commit()

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

    def find_file_by_metadata(self, title: str, artist: str = None, album: str = None, track_num: str = None) -> str | None:
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
        self.db_cursor.execute(query, (title, title, artist, artist, album, album, track_num or '', track_num or '', track_num or ''))
        result = self.db_cursor.fetchone()

        # If no exact match, try matching just the title
        if not result:
            query = '''
                SELECT filepath FROM library
                WHERE LOWER(title) = LOWER(?)
                LIMIT 1
            '''
            self.db_cursor.execute(query, (title,))
            result = self.db_cursor.fetchone()

        return result[0] if result else None

    def find_file_in_queue(self, title: str, artist: str = None) -> str | None:
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

    def remove_from_queue(self, title: str, artist: str = None, album: str = None, track_num: str = None):
        """Remove a song from the queue based on its metadata."""
        self.db_cursor.execute('''
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
        ''', (title, title, artist, artist, album, album, track_num or '', track_num or '', track_num or ''))
        self.db_conn.commit()

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
            return {
                'title': result[0],
                'artist': result[1],
                'album': result[2],
                'track_number': result[3],
                'date': result[4]
            }
        return {}

    def find_song_by_title_artist(self, title: str, artist: str = None) -> tuple[str, str, str, str, str] | None:
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

    def is_duplicate(self, metadata: dict[str, Any]) -> bool:
        """Check if a track with the same metadata already exists in the library.

        Returns:
            bool: True if a duplicate exists, False otherwise
        """
        # Build query based on available metadata
        query_parts = []
        params = []

        if metadata.get('title'):
            query_parts.append('LOWER(title) = LOWER(?)')
            params.append(metadata['title'])

        if metadata.get('artist'):
            query_parts.append('LOWER(artist) = LOWER(?)')
            params.append(metadata['artist'])

        if metadata.get('album'):
            query_parts.append('LOWER(album) = LOWER(?)')
            params.append(metadata['album'])

        if metadata.get('track_number'):
            query_parts.append('track_number = ?')
            params.append(metadata['track_number'])

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
