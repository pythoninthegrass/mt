"""Lyrics management with caching and async fetching."""

import contextlib
import threading
from collections.abc import Callable
from core.db import MusicDatabase
from utils.lyrics import fetch_lyrics


class LyricsManager:
    """Manages lyrics fetching, caching, and retrieval.

    Attributes:
        db: MusicDatabase instance for caching
        _fetch_thread: Background thread for async fetching
        _callbacks: Dict of callbacks for lyrics events
    """

    def __init__(self, db: MusicDatabase):
        """Initialize lyrics manager.

        Args:
            db: MusicDatabase instance
        """
        self.db = db
        self._fetch_thread = None
        self._callbacks = {}

    def get_lyrics(self, artist: str, title: str, album: str | None = None, on_complete: Callable | None = None) -> dict | None:
        """Get lyrics for a song, checking cache first.

        Args:
            artist: Artist name
            title: Song title
            album: Album name (optional)
            on_complete: Callback function(lyrics_dict) called when lyrics are fetched (optional)

        Returns:
            Cached lyrics dict if available, None if needs to be fetched
            If on_complete is provided, returns None and calls callback when ready
        """
        # Check cache first
        cached = self.get_cached_lyrics(artist, title)
        if cached:
            if on_complete:
                on_complete(cached)
            return cached

        # If callback provided, fetch async
        if on_complete:
            self._fetch_async(artist, title, album, on_complete)
            return None

        # Otherwise fetch synchronously
        return self.fetch_and_cache(artist, title, album)

    def get_cached_lyrics(self, artist: str, title: str) -> dict | None:
        """Check cache for lyrics.

        Args:
            artist: Artist name
            title: Song title

        Returns:
            Cached lyrics dict or None if not found
        """
        with contextlib.suppress(Exception):
            cursor = self.db.db_cursor
            cursor.execute(
                '''SELECT artist, title, lyrics, source_url, fetched_at
                   FROM lyrics_cache
                   WHERE LOWER(artist) = LOWER(?) AND LOWER(title) = LOWER(?)''',
                (artist, title)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "artist": row[0],
                    "title": row[1],
                    "lyrics": row[2],
                    "url": row[3],
                    "found": True,
                    "cached": True
                }
        return None

    def fetch_and_cache(self, artist: str, title: str, album: str | None = None) -> dict:
        """Fetch lyrics from API and cache the result.

        Args:
            artist: Artist name
            title: Song title
            album: Album name (optional)

        Returns:
            Lyrics dict from fetch_lyrics()
        """
        result = fetch_lyrics(title, artist, album)

        # Cache the result (even if not found, to avoid repeated API calls)
        self.cache_lyrics(artist, title, result)

        return result

    def cache_lyrics(self, artist: str, title: str, lyrics_data: dict):
        """Save lyrics to cache.

        Args:
            artist: Artist name
            title: Song title
            lyrics_data: Dict from fetch_lyrics()
        """
        with contextlib.suppress(Exception):
            cursor = self.db.db_cursor
            cursor.execute(
                '''INSERT OR REPLACE INTO lyrics_cache (artist, title, lyrics, source_url)
                   VALUES (?, ?, ?, ?)''',
                (
                    artist,
                    title,
                    lyrics_data.get("lyrics", ""),
                    lyrics_data.get("url", "")
                )
            )
            self.db.db_conn.commit()

    def _fetch_async(self, artist: str, title: str, album: str | None, callback: Callable):
        """Fetch lyrics in background thread.

        Args:
            artist: Artist name
            title: Song title
            album: Album name (optional)
            callback: Function to call with results
        """
        def fetch_worker():
            result = self.fetch_and_cache(artist, title, album)
            callback(result)

        # Cancel existing fetch if any
        if self._fetch_thread and self._fetch_thread.is_alive():
            # Let it finish, we'll just start a new one
            pass

        self._fetch_thread = threading.Thread(target=fetch_worker, daemon=True)
        self._fetch_thread.start()

    def clear_cache(self):
        """Clear all cached lyrics."""
        with contextlib.suppress(Exception):
            self.db.db_cursor.execute('DELETE FROM lyrics_cache')
            self.db.db_conn.commit()

    def get_cache_stats(self) -> dict:
        """Get statistics about lyrics cache.

        Returns:
            Dict with cache statistics
        """
        with contextlib.suppress(Exception):
            cursor = self.db.db_cursor
            cursor.execute('SELECT COUNT(*) FROM lyrics_cache')
            total = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM lyrics_cache WHERE lyrics != ""')
            found = cursor.fetchone()[0]

            return {
                "total_entries": total,
                "found_lyrics": found,
                "not_found": total - found
            }
        return {"total_entries": 0, "found_lyrics": 0, "not_found": 0}
