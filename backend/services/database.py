"""Database service for the mt music player backend.

This is a clean-room implementation that uses the same SQLite schema
as the original Tkinter application but without any Tkinter dependencies.
"""

import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

# Database schema - same as app/core/db/__init__.py
DB_TABLES = {
    "queue": """
        CREATE TABLE IF NOT EXISTS queue
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         filepath TEXT NOT NULL)
    """,
    "library": """
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
         file_size INTEGER DEFAULT 0,
         added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         last_played TIMESTAMP,
         play_count INTEGER DEFAULT 0)
    """,
    "settings": """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """,
    "favorites": """
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (track_id) REFERENCES library(id),
            UNIQUE(track_id)
        )
    """,
    "lyrics_cache": """
        CREATE TABLE IF NOT EXISTS lyrics_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artist TEXT NOT NULL,
            title TEXT NOT NULL,
            album TEXT,
            lyrics TEXT,
            source_url TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(artist, title)
        )
    """,
    "playlists": """
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            position INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "playlist_items": """
        CREATE TABLE IF NOT EXISTS playlist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            track_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(playlist_id, track_id),
            FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
            FOREIGN KEY (track_id) REFERENCES library(id) ON DELETE CASCADE
        )
    """,
}


class DatabaseService:
    """Async-compatible database service for FastAPI.

    Uses connection pooling and context managers for thread safety.
    """

    def __init__(self, db_path: str | Path):
        """Initialize the database service.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            for table_sql in DB_TABLES.values():
                cursor.execute(table_sql)
            conn.commit()
            self._run_migrations(conn)

    def _run_migrations(self, conn: sqlite3.Connection) -> None:
        """Run database migrations for schema updates."""
        cursor = conn.cursor()

        # Migration: Add file_size column to library table
        cursor.execute("PRAGMA table_info(library)")
        library_columns = {row[1] for row in cursor.fetchall()}
        if "file_size" not in library_columns:
            cursor.execute("ALTER TABLE library ADD COLUMN file_size INTEGER DEFAULT 0")
            conn.commit()

        # Migration: Add position column to playlists table
        cursor.execute("PRAGMA table_info(playlists)")
        playlist_columns = {row[1] for row in cursor.fetchall()}
        if "position" not in playlist_columns:
            cursor.execute("ALTER TABLE playlists ADD COLUMN position INTEGER DEFAULT 0")
            # Initialize positions based on creation order
            cursor.execute("SELECT id FROM playlists ORDER BY created_at ASC")
            for pos, row in enumerate(cursor.fetchall()):
                cursor.execute("UPDATE playlists SET position = ? WHERE id = ?", (pos, row[0]))
            conn.commit()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection with automatic cleanup.

        Yields:
            SQLite connection that will be automatically closed
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        # Enable foreign key constraints for CASCADE behavior
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    # ==================== Library Operations ====================

    def get_all_tracks(
        self,
        search: str | None = None,
        artist: str | None = None,
        album: str | None = None,
        sort_by: str = "added_date",
        sort_order: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get tracks from the library with filtering and pagination.

        Returns:
            Tuple of (tracks list, total count)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build WHERE clause
            conditions = []
            params: list[Any] = []

            if search:
                conditions.append("(title LIKE ? OR artist LIKE ? OR album LIKE ?)")
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])

            if artist:
                conditions.append("artist = ?")
                params.append(artist)

            if album:
                conditions.append("album = ?")
                params.append(album)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            # Validate sort column
            valid_sort_columns = {"title", "artist", "album", "added_date", "play_count", "duration", "last_played"}
            if sort_by not in valid_sort_columns:
                sort_by = "added_date"

            sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"

            # Get total count
            count_query = f"SELECT COUNT(*) FROM library {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            # Get tracks
            query = f"""
                SELECT id, filepath, title, artist, album, album_artist,
                       track_number, track_total, date, duration, file_size,
                       play_count, last_played, added_date
                FROM library
                {where_clause}
                ORDER BY {sort_by} {sort_direction}
                LIMIT ? OFFSET ?
            """
            cursor.execute(query, params + [limit, offset])

            tracks = [dict(row) for row in cursor.fetchall()]
            return tracks, total

    def get_track_by_id(self, track_id: int) -> dict[str, Any] | None:
        """Get a single track by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, filepath, title, artist, album, album_artist,
                       track_number, track_total, date, duration, file_size,
                       play_count, last_played, added_date
                FROM library WHERE id = ?
            """,
                (track_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_track_by_filepath(self, filepath: str) -> dict[str, Any] | None:
        """Get a track by filepath."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, filepath, title, artist, album, album_artist,
                       track_number, track_total, date, duration, file_size,
                       play_count, last_played, added_date
                FROM library WHERE filepath = ?
            """,
                (filepath,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_track(self, filepath: str, metadata: dict[str, Any]) -> int:
        """Add a track to the library.

        Returns:
            The ID of the newly added track
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO library
                (filepath, title, artist, album, album_artist,
                 track_number, track_total, date, duration, file_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    filepath,
                    metadata.get("title"),
                    metadata.get("artist"),
                    metadata.get("album"),
                    metadata.get("album_artist"),
                    metadata.get("track_number"),
                    metadata.get("track_total"),
                    metadata.get("date"),
                    metadata.get("duration"),
                    metadata.get("file_size", 0),
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def delete_track(self, track_id: int) -> bool:
        """Delete a track from the library and all related metadata."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM favorites WHERE track_id = ?", (track_id,))
            cursor.execute("DELETE FROM playlist_items WHERE track_id = ?", (track_id,))
            cursor.execute("DELETE FROM library WHERE id = ?", (track_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_track_metadata(self, track_id: int, metadata: dict[str, Any]) -> bool:
        """Update track metadata in the library."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE library SET
                    title = ?,
                    artist = ?,
                    album = ?,
                    album_artist = ?,
                    track_number = ?,
                    track_total = ?,
                    date = ?,
                    duration = ?,
                    file_size = ?
                WHERE id = ?
            """,
                (
                    metadata.get("title"),
                    metadata.get("artist"),
                    metadata.get("album"),
                    metadata.get("album_artist"),
                    metadata.get("track_number"),
                    metadata.get("track_total"),
                    metadata.get("date"),
                    metadata.get("duration"),
                    metadata.get("file_size", 0),
                    track_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_play_count(self, track_id: int) -> dict[str, Any] | None:
        """Increment play count for a track."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE library SET
                    play_count = play_count + 1,
                    last_played = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (track_id,),
            )
            conn.commit()

            # Return updated values
            cursor.execute("SELECT id, play_count, last_played FROM library WHERE id = ?", (track_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_library_stats(self) -> dict[str, int]:
        """Get library statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM library")
            total_tracks = cursor.fetchone()[0]

            cursor.execute("SELECT COALESCE(SUM(duration), 0) FROM library")
            total_duration = int(cursor.fetchone()[0] or 0)

            cursor.execute("SELECT COALESCE(SUM(file_size), 0) FROM library")
            total_size = int(cursor.fetchone()[0] or 0)

            cursor.execute("SELECT COUNT(DISTINCT artist) FROM library WHERE artist IS NOT NULL")
            total_artists = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT album) FROM library WHERE album IS NOT NULL")
            total_albums = cursor.fetchone()[0]

            return {
                "total_tracks": total_tracks,
                "total_duration": total_duration,
                "total_size": total_size,
                "total_artists": total_artists,
                "total_albums": total_albums,
            }

    def update_file_sizes(self) -> int:
        """Update file sizes for tracks that have file_size = 0."""
        import os

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, filepath FROM library WHERE file_size = 0 OR file_size IS NULL")
            tracks = cursor.fetchall()

            updated = 0
            for row in tracks:
                filepath = row["filepath"]
                try:
                    if os.path.exists(filepath):
                        size = os.path.getsize(filepath)
                        cursor.execute("UPDATE library SET file_size = ? WHERE id = ?", (size, row["id"]))
                        updated += 1
                except Exception:
                    pass

            conn.commit()
            return updated

    # ==================== Queue Operations ====================

    def get_queue(self) -> list[dict[str, Any]]:
        """Get all items in the queue with track metadata."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT q.id as queue_id, q.filepath,
                       l.id, l.title, l.artist, l.album, l.album_artist,
                       l.track_number, l.track_total, l.date, l.duration, l.file_size,
                       l.play_count, l.last_played, l.added_date
                FROM queue q
                LEFT JOIN library l ON q.filepath = l.filepath
                ORDER BY q.id
            """
            )

            items = []
            for i, row in enumerate(cursor.fetchall()):
                row_dict = dict(row)
                items.append(
                    {
                        "position": i,
                        "track": {
                            "id": row_dict.get("id"),
                            "filepath": row_dict["filepath"],
                            "title": row_dict.get("title"),
                            "artist": row_dict.get("artist"),
                            "album": row_dict.get("album"),
                            "album_artist": row_dict.get("album_artist"),
                            "track_number": row_dict.get("track_number"),
                            "track_total": row_dict.get("track_total"),
                            "date": row_dict.get("date"),
                            "duration": row_dict.get("duration"),
                            "file_size": row_dict.get("file_size", 0),
                            "play_count": row_dict.get("play_count", 0),
                            "last_played": row_dict.get("last_played"),
                            "added_date": row_dict.get("added_date"),
                        },
                    }
                )
            return items

    def add_to_queue(self, track_ids: list[int], position: int | None = None) -> int:
        """Add tracks to the queue.

        Returns:
            Number of tracks added
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get filepaths for track IDs
            placeholders = ",".join("?" * len(track_ids))
            cursor.execute(f"SELECT id, filepath FROM library WHERE id IN ({placeholders})", track_ids)
            tracks = {row["id"]: row["filepath"] for row in cursor.fetchall()}

            if position is not None:
                # Get current queue to insert at position
                cursor.execute("SELECT id, filepath FROM queue ORDER BY id")
                current_queue = list(cursor.fetchall())

                # Clear and rebuild queue
                cursor.execute("DELETE FROM queue")

                # Insert items before position
                for i, item in enumerate(current_queue[:position]):
                    cursor.execute("INSERT INTO queue (filepath) VALUES (?)", (item["filepath"],))

                # Insert new items
                for track_id in track_ids:
                    if track_id in tracks:
                        cursor.execute("INSERT INTO queue (filepath) VALUES (?)", (tracks[track_id],))

                # Insert items after position
                for item in current_queue[position:]:
                    cursor.execute("INSERT INTO queue (filepath) VALUES (?)", (item["filepath"],))
            else:
                # Append to end
                for track_id in track_ids:
                    if track_id in tracks:
                        cursor.execute("INSERT INTO queue (filepath) VALUES (?)", (tracks[track_id],))

            conn.commit()
            return len([tid for tid in track_ids if tid in tracks])

    def add_files_to_queue(self, filepaths: list[str], position: int | None = None) -> tuple[int, list[dict[str, Any]]]:
        """Add files directly to the queue.

        Returns:
            Tuple of (count added, list of track info)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            added_tracks = []

            for filepath in filepaths:
                # Check if file exists in library
                cursor.execute("SELECT * FROM library WHERE filepath = ?", (filepath,))
                row = cursor.fetchone()

                if row:
                    added_tracks.append(dict(row))
                else:
                    # Add to library with minimal metadata
                    filename = os.path.basename(filepath)
                    title = os.path.splitext(filename)[0]
                    cursor.execute(
                        "INSERT INTO library (filepath, title) VALUES (?, ?)",
                        (filepath, title),
                    )
                    conn.commit()
                    cursor.execute("SELECT * FROM library WHERE filepath = ?", (filepath,))
                    row = cursor.fetchone()
                    if row:
                        added_tracks.append(dict(row))

            # Add to queue
            if position is not None:
                cursor.execute("SELECT id, filepath FROM queue ORDER BY id")
                current_queue = list(cursor.fetchall())
                cursor.execute("DELETE FROM queue")

                for i, item in enumerate(current_queue[:position]):
                    cursor.execute("INSERT INTO queue (filepath) VALUES (?)", (item["filepath"],))

                for track in added_tracks:
                    cursor.execute("INSERT INTO queue (filepath) VALUES (?)", (track["filepath"],))

                for item in current_queue[position:]:
                    cursor.execute("INSERT INTO queue (filepath) VALUES (?)", (item["filepath"],))
            else:
                for track in added_tracks:
                    cursor.execute("INSERT INTO queue (filepath) VALUES (?)", (track["filepath"],))

            conn.commit()
            return len(added_tracks), added_tracks

    def remove_from_queue(self, position: int) -> bool:
        """Remove a track from the queue by position."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get queue items
            cursor.execute("SELECT id FROM queue ORDER BY id")
            items = list(cursor.fetchall())

            if position < 0 or position >= len(items):
                return False

            queue_id = items[position]["id"]
            cursor.execute("DELETE FROM queue WHERE id = ?", (queue_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_queue(self) -> None:
        """Clear the entire queue."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM queue")
            conn.commit()

    def reorder_queue(self, from_position: int, to_position: int) -> bool:
        """Reorder tracks in the queue."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get current queue
            cursor.execute("SELECT id, filepath FROM queue ORDER BY id")
            items = list(cursor.fetchall())

            if from_position < 0 or from_position >= len(items):
                return False
            if to_position < 0 or to_position >= len(items):
                return False

            # Reorder in memory
            filepaths = [item["filepath"] for item in items]
            item = filepaths.pop(from_position)
            filepaths.insert(to_position, item)

            # Rebuild queue
            cursor.execute("DELETE FROM queue")
            for filepath in filepaths:
                cursor.execute("INSERT INTO queue (filepath) VALUES (?)", (filepath,))

            conn.commit()
            return True

    def get_queue_length(self) -> int:
        """Get the number of items in the queue."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM queue")
            return cursor.fetchone()[0]

    # ==================== Favorites Operations ====================

    def get_favorites(self, limit: int = 100, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
        """Get favorited tracks."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM favorites")
            total = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT l.*, f.timestamp as favorited_date
                FROM favorites f
                JOIN library l ON f.track_id = l.id
                ORDER BY f.timestamp ASC
                LIMIT ? OFFSET ?
            """,
                (limit, offset),
            )

            tracks = [dict(row) for row in cursor.fetchall()]
            return tracks, total

    def get_top_25(self) -> list[dict[str, Any]]:
        """Get top 25 most played tracks."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM library
                WHERE play_count > 0
                ORDER BY play_count DESC, last_played DESC
                LIMIT 25
            """
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_recently_played(self, days: int = 14, limit: int = 100) -> list[dict[str, Any]]:
        """Get tracks played within the last N days.

        Args:
            days: Number of days to look back (default 14)
            limit: Maximum number of tracks to return (default 100)

        Returns:
            List of tracks ordered by last_played descending
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM library
                WHERE last_played IS NOT NULL
                  AND last_played >= datetime('now', ?)
                ORDER BY last_played DESC
                LIMIT ?
            """,
                (f"-{days} days", limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_recently_added(self, days: int = 14, limit: int = 100) -> list[dict[str, Any]]:
        """Get tracks added within the last N days.

        Args:
            days: Number of days to look back (default 14)
            limit: Maximum number of tracks to return (default 100)

        Returns:
            List of tracks ordered by added_date descending
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM library
                WHERE added_date IS NOT NULL
                  AND added_date >= datetime('now', ?)
                ORDER BY added_date DESC
                LIMIT ?
            """,
                (f"-{days} days", limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def is_favorite(self, track_id: int) -> tuple[bool, datetime | None]:
        """Check if a track is favorited."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp FROM favorites WHERE track_id = ?", (track_id,))
            row = cursor.fetchone()
            if row:
                return True, row["timestamp"]
            return False, None

    def add_favorite(self, track_id: int) -> datetime | None:
        """Add a track to favorites."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO favorites (track_id) VALUES (?)", (track_id,))
                conn.commit()
                cursor.execute("SELECT timestamp FROM favorites WHERE track_id = ?", (track_id,))
                row = cursor.fetchone()
                return row["timestamp"] if row else None
            except sqlite3.IntegrityError:
                return None  # Already favorited

    def remove_favorite(self, track_id: int) -> bool:
        """Remove a track from favorites."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM favorites WHERE track_id = ?", (track_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ==================== Playlist Operations ====================

    def get_playlists(self) -> list[dict[str, Any]]:
        """Get all playlists with track counts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.id, p.name, p.position, p.created_at,
                       COUNT(pi.id) as track_count
                FROM playlists p
                LEFT JOIN playlist_items pi ON p.id = pi.playlist_id
                GROUP BY p.id
                ORDER BY p.position ASC, p.created_at ASC
            """
            )
            return [dict(row) for row in cursor.fetchall()]

    def create_playlist(self, name: str, description: str | None = None) -> dict[str, Any] | None:
        """Create a new playlist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO playlists (name) VALUES (?)", (name,))
                conn.commit()
                playlist_id = cursor.lastrowid

                cursor.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    result["track_count"] = 0
                    return result
                return None
            except sqlite3.IntegrityError:
                return None  # Name already exists

    def get_playlist(self, playlist_id: int) -> dict[str, Any] | None:
        """Get a playlist with its tracks."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
            playlist_row = cursor.fetchone()
            if not playlist_row:
                return None

            playlist = dict(playlist_row)

            cursor.execute(
                """
                SELECT l.*, pi.position, pi.added_at
                FROM playlist_items pi
                JOIN library l ON pi.track_id = l.id
                WHERE pi.playlist_id = ?
                ORDER BY pi.position ASC
            """,
                (playlist_id,),
            )

            tracks = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                tracks.append(
                    {
                        "position": row_dict["position"],
                        "added_date": row_dict["added_at"],
                        "track": {k: v for k, v in row_dict.items() if k not in ("position", "added_at")},
                    }
                )

            playlist["tracks"] = tracks
            playlist["track_count"] = len(tracks)
            return playlist

    def update_playlist(self, playlist_id: int, name: str | None = None) -> dict[str, Any] | None:
        """Update playlist metadata."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if name:
                try:
                    cursor.execute("UPDATE playlists SET name = ? WHERE id = ?", (name, playlist_id))
                    conn.commit()
                except sqlite3.IntegrityError:
                    return None  # Name conflict

            cursor.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                cursor.execute("SELECT COUNT(*) FROM playlist_items WHERE playlist_id = ?", (playlist_id,))
                result["track_count"] = cursor.fetchone()[0]
                return result
            return None

    def delete_playlist(self, playlist_id: int) -> bool:
        """Delete a playlist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
            conn.commit()
            return cursor.rowcount > 0

    def add_tracks_to_playlist(self, playlist_id: int, track_ids: list[int], position: int | None = None) -> int:
        """Add tracks to a playlist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get current max position
            cursor.execute("SELECT COALESCE(MAX(position), -1) FROM playlist_items WHERE playlist_id = ?", (playlist_id,))
            max_position = cursor.fetchone()[0]

            added = 0
            for track_id in track_ids:
                try:
                    max_position += 1
                    cursor.execute(
                        "INSERT INTO playlist_items (playlist_id, track_id, position) VALUES (?, ?, ?)",
                        (playlist_id, track_id, max_position),
                    )
                    added += 1
                except sqlite3.IntegrityError:
                    max_position -= 1  # Duplicate, skip

            conn.commit()
            return added

    def remove_track_from_playlist(self, playlist_id: int, position: int) -> bool:
        """Remove a track from a playlist by position."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get item at position
            cursor.execute(
                "SELECT id FROM playlist_items WHERE playlist_id = ? AND position = ?",
                (playlist_id, position),
            )
            row = cursor.fetchone()
            if not row:
                return False

            cursor.execute("DELETE FROM playlist_items WHERE id = ?", (row["id"],))

            # Reindex positions
            cursor.execute(
                "SELECT id FROM playlist_items WHERE playlist_id = ? ORDER BY position",
                (playlist_id,),
            )
            for new_pos, item in enumerate(cursor.fetchall()):
                cursor.execute("UPDATE playlist_items SET position = ? WHERE id = ?", (new_pos, item["id"]))

            conn.commit()
            return True

    def reorder_playlist(self, playlist_id: int, from_position: int, to_position: int) -> bool:
        """Reorder tracks within a playlist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, track_id FROM playlist_items WHERE playlist_id = ? ORDER BY position",
                (playlist_id,),
            )
            items = list(cursor.fetchall())

            if from_position < 0 or from_position >= len(items):
                return False
            if to_position < 0 or to_position >= len(items):
                return False

            # Reorder
            item_ids = [item["id"] for item in items]
            moved = item_ids.pop(from_position)
            item_ids.insert(to_position, moved)

            # Update positions
            for pos, item_id in enumerate(item_ids):
                cursor.execute("UPDATE playlist_items SET position = ? WHERE id = ?", (pos, item_id))

            conn.commit()
            return True

    def get_playlist_track_count(self, playlist_id: int) -> int:
        """Get the number of tracks in a playlist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM playlist_items WHERE playlist_id = ?", (playlist_id,))
            return cursor.fetchone()[0]

    def reorder_playlists(self, from_position: int, to_position: int) -> bool:
        """Reorder playlists in the sidebar."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM playlists ORDER BY position ASC, created_at ASC")
            items = list(cursor.fetchall())

            if from_position < 0 or from_position >= len(items):
                return False
            if to_position < 0 or to_position >= len(items):
                return False

            playlist_ids = [item["id"] for item in items]
            moved = playlist_ids.pop(from_position)
            playlist_ids.insert(to_position, moved)

            for pos, playlist_id in enumerate(playlist_ids):
                cursor.execute("UPDATE playlists SET position = ? WHERE id = ?", (pos, playlist_id))

            conn.commit()
            return True

    def generate_unique_playlist_name(self, base: str = "New playlist") -> str:
        """Generate a unique playlist name by appending a number if needed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM playlists WHERE name = ?", (base,))
            if not cursor.fetchone():
                return base

            suffix = 2
            while True:
                candidate = f"{base} ({suffix})"
                cursor.execute("SELECT name FROM playlists WHERE name = ?", (candidate,))
                if not cursor.fetchone():
                    return candidate
                suffix += 1

    # ==================== Settings Operations ====================

    def get_all_settings(self) -> dict[str, Any]:
        """Get all settings."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")

            settings = {}
            for row in cursor.fetchall():
                key = row["key"]
                value = row["value"]

                # Parse known types
                if key in ("volume", "sidebar_width", "queue_panel_height"):
                    settings[key] = int(value) if value else 0
                elif key in ("shuffle", "loop_enabled", "repeat_one"):
                    settings[key] = value == "1" or value == "true"
                else:
                    settings[key] = value

            # Set defaults for missing settings
            defaults = {
                "volume": 75,
                "shuffle": False,
                "loop_mode": "none",
                "theme": "dark",
                "sidebar_width": 250,
                "queue_panel_height": 300,
            }
            for key, default in defaults.items():
                if key not in settings:
                    settings[key] = default

            return settings

    def get_setting(self, key: str) -> Any | None:
        """Get a single setting."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else None

    def set_setting(self, key: str, value: Any) -> None:
        """Set a single setting."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            str_value = str(value) if not isinstance(value, bool) else ("1" if value else "0")
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str_value))
            conn.commit()

    def update_settings(self, settings: dict[str, Any]) -> list[str]:
        """Update multiple settings."""
        updated = []
        for key, value in settings.items():
            if value is not None:
                self.set_setting(key, value)
                updated.append(key)
        return updated


# Global database instance (will be initialized in main.py)
_db: DatabaseService | None = None


def init_db(db_path: str | Path) -> DatabaseService:
    """Initialize the global database instance."""
    global _db
    _db = DatabaseService(db_path)
    return _db


def get_db() -> DatabaseService:
    """Get the global database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db
