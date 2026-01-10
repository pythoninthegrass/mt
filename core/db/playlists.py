"""Playlist management for custom user-created playlists."""

import sqlite3
from typing import Optional


class PlaylistsManager:
    """Manages custom playlist operations including CRUD, track management, and ordering."""

    def __init__(self, db_conn: sqlite3.Connection, db_cursor: sqlite3.Cursor):
        """Initialize the playlists manager.

        Args:
            db_conn: SQLite database connection
            db_cursor: SQLite database cursor
        """
        self.db_conn = db_conn
        self.db_cursor = db_cursor

    def create_playlist(self, name: str) -> int:
        """Create a new playlist.

        Args:
            name: Playlist name (must be unique)

        Returns:
            int: The ID of the newly created playlist

        Raises:
            sqlite3.IntegrityError: If a playlist with the same name already exists
        """
        self.db_cursor.execute(
            "INSERT INTO playlists (name) VALUES (?)",
            (name,)
        )
        self.db_conn.commit()
        return self.db_cursor.lastrowid

    def list_playlists(self) -> list[tuple[int, str]]:
        """Return list of all custom playlists.

        Returns:
            list[tuple[int, str]]: List of (id, name) tuples ordered by created_at
        """
        self.db_cursor.execute(
            "SELECT id, name FROM playlists ORDER BY created_at ASC"
        )
        return self.db_cursor.fetchall()

    def get_playlist_name(self, playlist_id: int) -> str | None:
        """Get playlist name by ID.

        Args:
            playlist_id: The playlist ID

        Returns:
            Optional[str]: Playlist name, or None if not found
        """
        self.db_cursor.execute(
            "SELECT name FROM playlists WHERE id = ?",
            (playlist_id,)
        )
        result = self.db_cursor.fetchone()
        return result[0] if result else None

    def rename_playlist(self, playlist_id: int, new_name: str) -> bool:
        """Rename a playlist.

        Args:
            playlist_id: The playlist ID
            new_name: New playlist name (must be unique)

        Returns:
            bool: True if successful

        Raises:
            sqlite3.IntegrityError: If new_name conflicts with existing playlist
        """
        self.db_cursor.execute(
            "UPDATE playlists SET name = ? WHERE id = ?",
            (new_name, playlist_id)
        )
        self.db_conn.commit()
        return self.db_cursor.rowcount > 0

    def delete_playlist(self, playlist_id: int) -> bool:
        """Delete a playlist and all its items (cascades automatically).

        Args:
            playlist_id: The playlist ID

        Returns:
            bool: True if successful (playlist existed and was deleted)
        """
        self.db_cursor.execute(
            "DELETE FROM playlists WHERE id = ?",
            (playlist_id,)
        )
        self.db_conn.commit()
        return self.db_cursor.rowcount > 0

    def get_playlist_items(self, playlist_id: int) -> list[tuple]:
        """Get playlist tracks with library metadata, ordered by position.

        Args:
            playlist_id: The playlist ID

        Returns:
            list[tuple]: List of (filepath, artist, title, album, track_number, date, track_id)
        """
        self.db_cursor.execute('''
            SELECT
                l.filepath,
                l.artist,
                l.title,
                l.album,
                l.track_number,
                l.date,
                l.id as track_id
            FROM playlist_items pi
            JOIN library l ON pi.track_id = l.id
            WHERE pi.playlist_id = ?
            ORDER BY pi.position ASC
        ''', (playlist_id,))
        return self.db_cursor.fetchall()

    def add_tracks_to_playlist(self, playlist_id: int, track_ids: list[int]) -> int:
        """Add tracks to a playlist. Ignores duplicates.

        Args:
            playlist_id: The playlist ID
            track_ids: List of track IDs from library table

        Returns:
            int: Number of tracks successfully added
        """
        # Get the current max position
        self.db_cursor.execute(
            "SELECT COALESCE(MAX(position), -1) FROM playlist_items WHERE playlist_id = ?",
            (playlist_id,)
        )
        max_position = self.db_cursor.fetchone()[0]

        added_count = 0
        for track_id in track_ids:
            try:
                max_position += 1
                self.db_cursor.execute('''
                    INSERT INTO playlist_items (playlist_id, track_id, position)
                    VALUES (?, ?, ?)
                ''', (playlist_id, track_id, max_position))
                added_count += 1
            except sqlite3.IntegrityError:
                # Duplicate track (playlist_id, track_id) - skip
                max_position -= 1
                continue

        self.db_conn.commit()
        return added_count

    def remove_tracks_from_playlist(self, playlist_id: int, track_ids: list[int]) -> int:
        """Remove tracks from a playlist (does not delete from library).

        Args:
            playlist_id: The playlist ID
            track_ids: List of track IDs to remove

        Returns:
            int: Number of tracks successfully removed
        """
        if not track_ids:
            return 0

        placeholders = ','.join('?' * len(track_ids))
        self.db_cursor.execute(f'''
            DELETE FROM playlist_items
            WHERE playlist_id = ? AND track_id IN ({placeholders})
        ''', [playlist_id] + track_ids)

        removed_count = self.db_cursor.rowcount
        self.db_conn.commit()

        # Reorder remaining items to close gaps
        self._reindex_positions(playlist_id)

        return removed_count

    def reorder_playlist(self, playlist_id: int, ordered_track_ids: list[int]) -> bool:
        """Update track positions based on new order.

        Args:
            playlist_id: The playlist ID
            ordered_track_ids: List of track IDs in desired order

        Returns:
            bool: True if successful
        """
        for position, track_id in enumerate(ordered_track_ids):
            self.db_cursor.execute('''
                UPDATE playlist_items
                SET position = ?
                WHERE playlist_id = ? AND track_id = ?
            ''', (position, playlist_id, track_id))

        self.db_conn.commit()
        return True

    def get_track_id_by_filepath(self, filepath: str) -> int | None:
        """Resolve filepath to library track ID.

        Args:
            filepath: File path to look up

        Returns:
            Optional[int]: Track ID from library table, or None if not found
        """
        self.db_cursor.execute(
            "SELECT id FROM library WHERE filepath = ?",
            (filepath,)
        )
        result = self.db_cursor.fetchone()
        return result[0] if result else None

    def generate_unique_name(self, base_name: str = "New playlist") -> str:
        """Generate unique playlist name with auto-suffix if needed.

        Args:
            base_name: Base name to use (default: "New playlist")

        Returns:
            str: Unique name like "New playlist", "New playlist (2)", "New playlist (3)", etc.
        """
        # Check if base name is available
        self.db_cursor.execute(
            "SELECT COUNT(*) FROM playlists WHERE name = ?",
            (base_name,)
        )
        if self.db_cursor.fetchone()[0] == 0:
            return base_name

        # Find next available suffix
        counter = 2
        while True:
            candidate = f"{base_name} ({counter})"
            self.db_cursor.execute(
                "SELECT COUNT(*) FROM playlists WHERE name = ?",
                (candidate,)
            )
            if self.db_cursor.fetchone()[0] == 0:
                return candidate
            counter += 1

    def _reindex_positions(self, playlist_id: int):
        """Reindex positions to close gaps after removals.

        Args:
            playlist_id: The playlist ID
        """
        # Get all items ordered by current position
        self.db_cursor.execute('''
            SELECT id FROM playlist_items
            WHERE playlist_id = ?
            ORDER BY position ASC
        ''', (playlist_id,))

        items = self.db_cursor.fetchall()
        for new_position, (item_id,) in enumerate(items):
            self.db_cursor.execute('''
                UPDATE playlist_items
                SET position = ?
                WHERE id = ?
            ''', (new_position, item_id))

        self.db_conn.commit()
