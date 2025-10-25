import sqlite3
from core.logging import log_error


class FavoritesManager:
    """Manages favorite tracks and special views (most played, recently added/played)."""

    def __init__(self, db_conn: sqlite3.Connection, db_cursor: sqlite3.Cursor):
        self.db_conn = db_conn
        self.db_cursor = db_cursor

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
            self.db_cursor.execute('INSERT INTO favorites (track_id) VALUES (?)', (track_id,))
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
                log_error(e, "Failed to get top 25 most played")
            except ImportError:
                pass
            return []

    def get_recently_added(self) -> list[tuple]:
        """Get tracks added within the last 14 days, ordered by added_date (descending).

        Returns:
            list[tuple]: List of (filepath, artist, title, album, track_number, date, added_date) tuples
        """
        try:
            from core.logging import player_logger
            from eliot import start_action

            with start_action(player_logger, "db_get_recently_added"):
                query = '''
                    SELECT filepath, artist, title, album, track_number, date, added_date
                    FROM library
                    WHERE added_date >= datetime('now', '-14 days')
                    ORDER BY added_date DESC
                '''
                self.db_cursor.execute(query)
                results = self.db_cursor.fetchall()
                return results
        except Exception as e:
            try:
                log_error(e, "Failed to get recently added tracks")
            except ImportError:
                pass
            return []

    def get_recently_played(self) -> list[tuple]:
        """Get tracks played within the last 14 days, ordered by last_played (descending).

        Returns:
            list[tuple]: List of (filepath, artist, title, album, track_number, date, last_played) tuples
        """
        try:
            from core.logging import player_logger
            from eliot import start_action

            with start_action(player_logger, "db_get_recently_played"):
                query = '''
                    SELECT filepath, artist, title, album, track_number, date, last_played
                    FROM library
                    WHERE last_played IS NOT NULL
                    AND last_played >= datetime('now', '-14 days')
                    ORDER BY last_played DESC
                '''
                self.db_cursor.execute(query)
                results = self.db_cursor.fetchall()
                return results
        except Exception as e:
            try:
                log_error(e, "Failed to get recently played tracks")
            except ImportError:
                pass
            return []
