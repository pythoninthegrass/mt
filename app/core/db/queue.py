import sqlite3


class QueueManager:
    """Manages playback queue operations."""

    def __init__(self, db_conn: sqlite3.Connection, db_cursor: sqlite3.Cursor):
        self.db_conn = db_conn
        self.db_cursor = db_cursor

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

    def search_queue(self, search_text):
        """Search queue items by text across artist, title, and album."""
        search_term = f'%{search_text}%'
        query = '''
            SELECT q.filepath, l.artist, l.title, l.album, l.track_number, l.date
            FROM queue q
            LEFT JOIN library l ON q.filepath = l.filepath
            WHERE l.artist LIKE ? OR l.title LIKE ? OR l.album LIKE ?
            ORDER BY q.id
        '''
        self.db_cursor.execute(query, (search_term, search_term, search_term))
        return self.db_cursor.fetchall()

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

    def clear_queue(self):
        """Clear all items from the queue."""
        self.db_cursor.execute('DELETE FROM queue')
        self.db_conn.commit()
