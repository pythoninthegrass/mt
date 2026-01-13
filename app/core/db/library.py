import contextlib
import os
import sqlite3
from core.logging import db_logger, log_database_operation, log_error
from typing import Any


class LibraryManager:
    """Manages music library operations including tracks, metadata, and search."""

    def __init__(self, db_conn: sqlite3.Connection, db_cursor: sqlite3.Cursor):
        self.db_conn = db_conn
        self.db_cursor = db_cursor

    def get_existing_files(self) -> set:
        """Get set of all files currently in library."""
        self.db_cursor.execute('SELECT filepath FROM library')
        return {row[0] for row in self.db_cursor.fetchall()}

    def add_to_library(self, filepath: str, metadata: dict[str, Any]):
        """Add a file to the library with its metadata."""
        try:
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
            from eliot import log_message

            log_message(
                message_type="library_add_success", filepath=filepath, title=metadata.get('title'), artist=metadata.get('artist')
            )
        except ImportError:
            pass

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
        """Update track metadata in library.

        Args:
            filepath: Path to the track file
            title: Track title
            artist: Artist name
            album: Album name
            album_artist: Album artist name
            year: Release year
            genre: Genre
            track_number: Track number

        Returns:
            bool: True if updated successfully
        """
        with contextlib.suppress(Exception):
            self.db_cursor.execute(
                '''
                UPDATE library
                SET title = ?, artist = ?, album = ?, album_artist = ?,
                    date = ?, track_number = ?
                WHERE filepath = ?
            ''',
                (title, artist, album, album_artist, year, track_number, filepath),
            )
            self.db_conn.commit()
            return True
        return False

    def get_library_items(self) -> list[tuple]:
        """Get all items in the library with their metadata."""
        self.db_cursor.execute('''
            WITH parsed_tracks AS (
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
            )
            SELECT
                filepath,
                artist,
                title,
                album,
                track_number,
                date
            FROM parsed_tracks
            ORDER BY
                CASE WHEN artist IS NULL THEN 1 ELSE 0 END,
                LOWER(COALESCE(artist, '')),
                CASE WHEN album IS NULL THEN 1 ELSE 0 END,
                LOWER(COALESCE(album, '')),
                track_num_int,
                LOWER(COALESCE(title, '')),
                filepath
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

    def get_library_statistics(self) -> dict[str, Any]:
        """Get comprehensive library statistics including file count, size, and total duration."""
        stats = {'file_count': 0, 'total_size_bytes': 0, 'total_duration_seconds': 0}

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

    def delete_from_library(self, filepath: str) -> bool:
        """Delete a track from the library by its filepath.

        Args:
            filepath: The absolute path to the file to remove from library

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            from eliot import log_message

            # Get track_id before deleting from library
            self.db_cursor.execute('SELECT id FROM library WHERE filepath = ?', (filepath,))
            result = self.db_cursor.fetchone()

            if result:
                track_id = result[0]

                # Delete from favorites first
                self.db_cursor.execute('DELETE FROM favorites WHERE track_id = ?', (track_id,))

            # Delete from library
            self.db_cursor.execute('DELETE FROM library WHERE filepath = ?', (filepath,))

            # Commit the changes
            self.db_conn.commit()

            log_message(message_type="library_delete", filepath=filepath, message="Track deleted from library")

            return True

        except Exception as e:
            print(f"Error deleting from library: {e}")
            try:
                from core.logging import library_logger

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

    def get_track_by_filepath(self, filepath: str) -> tuple | None:
        """Get track metadata as tuple by filepath.

        Returns:
            Tuple of (artist, title, album, track_number, date) or None if not found
        """
        query = """
            SELECT artist, title, album, track_number, date
            FROM library
            WHERE filepath = ?
        """
        self.db_cursor.execute(query, (filepath,))
        result = self.db_cursor.fetchone()
        return result if result else None

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
