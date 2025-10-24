"""Unit tests for lyrics functionality."""

import pytest
from core.db import DB_TABLES, MusicDatabase
from core.lyrics import LyricsManager
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture
def test_db(tmp_path):
    """Create test database."""
    db_path = tmp_path / "test_lyrics.db"
    db = MusicDatabase(str(db_path), DB_TABLES)
    yield db
    db.close()


@pytest.fixture
def lyrics_manager(test_db):
    """Create LyricsManager with test database."""
    return LyricsManager(test_db)


def test_lyrics_manager_init(lyrics_manager, test_db):
    """Test LyricsManager initialization."""
    assert lyrics_manager.db == test_db
    assert lyrics_manager._fetch_thread is None


def test_cache_lyrics(lyrics_manager):
    """Test caching lyrics."""
    lyrics_data = {
        "title": "Test Song",
        "artist": "Test Artist",
        "lyrics": "Test lyrics content",
        "url": "https://genius.com/test",
        "found": True
    }

    lyrics_manager.cache_lyrics("Test Artist", "Test Song", lyrics_data)

    # Verify cache
    cached = lyrics_manager.get_cached_lyrics("Test Artist", "Test Song")
    assert cached is not None
    assert cached["title"] == "Test Song"
    assert cached["artist"] == "Test Artist"
    assert cached["lyrics"] == "Test lyrics content"
    assert cached["found"] is True
    assert cached["cached"] is True


def test_cache_lyrics_case_insensitive(lyrics_manager):
    """Test cache retrieval is case-insensitive."""
    lyrics_data = {
        "title": "Test Song",
        "artist": "Test Artist",
        "lyrics": "Test lyrics",
        "url": "https://genius.com/test",
        "found": True
    }

    lyrics_manager.cache_lyrics("Test Artist", "Test Song", lyrics_data)

    # Try different case
    cached = lyrics_manager.get_cached_lyrics("test artist", "test song")
    assert cached is not None
    assert cached["title"] == "Test Song"


def test_get_cached_lyrics_not_found(lyrics_manager):
    """Test get_cached_lyrics returns None when not found."""
    cached = lyrics_manager.get_cached_lyrics("Nonexistent Artist", "Nonexistent Song")
    assert cached is None


@patch('core.lyrics.fetch_lyrics')
def test_fetch_and_cache(mock_fetch_lyrics, lyrics_manager):
    """Test fetch_and_cache method."""
    mock_fetch_lyrics.return_value = {
        "title": "Fetched Song",
        "artist": "Fetched Artist",
        "lyrics": "Fetched lyrics",
        "url": "https://genius.com/fetched",
        "found": True
    }

    result = lyrics_manager.fetch_and_cache("Fetched Artist", "Fetched Song")

    assert result["found"] is True
    assert result["lyrics"] == "Fetched lyrics"

    # Verify it was cached
    cached = lyrics_manager.get_cached_lyrics("Fetched Artist", "Fetched Song")
    assert cached is not None
    assert cached["lyrics"] == "Fetched lyrics"


@patch('core.lyrics.fetch_lyrics')
def test_get_lyrics_synchronous(mock_fetch_lyrics, lyrics_manager):
    """Test synchronous lyrics retrieval."""
    mock_fetch_lyrics.return_value = {
        "title": "Sync Song",
        "artist": "Sync Artist",
        "lyrics": "Sync lyrics",
        "url": "https://genius.com/sync",
        "found": True
    }

    # Get lyrics without callback (synchronous)
    result = lyrics_manager.get_lyrics("Sync Artist", "Sync Song")

    assert result is not None
    assert result["found"] is True
    assert result["lyrics"] == "Sync lyrics"


def test_clear_cache(lyrics_manager):
    """Test clearing lyrics cache."""
    # Add some cached lyrics
    lyrics_data = {
        "title": "Test Song",
        "artist": "Test Artist",
        "lyrics": "Test lyrics",
        "url": "https://genius.com/test",
        "found": True
    }
    lyrics_manager.cache_lyrics("Test Artist", "Test Song", lyrics_data)

    # Verify cached
    cached = lyrics_manager.get_cached_lyrics("Test Artist", "Test Song")
    assert cached is not None

    # Clear cache
    lyrics_manager.clear_cache()

    # Verify cleared
    cached = lyrics_manager.get_cached_lyrics("Test Artist", "Test Song")
    assert cached is None


def test_get_cache_stats(lyrics_manager):
    """Test cache statistics."""
    # Add some lyrics
    lyrics_manager.cache_lyrics("Artist 1", "Song 1", {
        "title": "Song 1",
        "artist": "Artist 1",
        "lyrics": "Lyrics 1",
        "url": "https://genius.com/1",
        "found": True
    })

    lyrics_manager.cache_lyrics("Artist 2", "Song 2", {
        "title": "Song 2",
        "artist": "Artist 2",
        "lyrics": "",  # Not found
        "url": "",
        "found": False
    })

    stats = lyrics_manager.get_cache_stats()
    assert stats["total_entries"] == 2
    assert stats["found_lyrics"] == 1
    assert stats["not_found"] == 1


def test_get_lyrics_with_cached_and_callback(lyrics_manager):
    """Test get_lyrics returns cached lyrics and calls callback when both provided."""
    # Cache some lyrics first
    lyrics_data = {
        "title": "Cached Song",
        "artist": "Cached Artist",
        "lyrics": "Cached lyrics",
        "url": "https://genius.com/cached",
        "found": True
    }
    lyrics_manager.cache_lyrics("Cached Artist", "Cached Song", lyrics_data)

    # Call with callback - should call callback with cached data
    callback = MagicMock()
    result = lyrics_manager.get_lyrics("Cached Artist", "Cached Song", on_complete=callback)

    assert result is not None  # Returns cached data immediately
    assert result["lyrics"] == "Cached lyrics"
    assert callback.called
    callback.assert_called_once_with(result)


@patch('core.lyrics.fetch_lyrics')
def test_get_lyrics_async_with_callback(mock_fetch_lyrics, lyrics_manager):
    """Test get_lyrics fetches async when callback provided and not cached."""
    mock_fetch_lyrics.return_value = {
        "title": "Async Song",
        "artist": "Async Artist",
        "lyrics": "Async lyrics",
        "url": "https://genius.com/async",
        "found": True
    }

    callback = MagicMock()
    result = lyrics_manager.get_lyrics("Async Artist", "Async Song", on_complete=callback)

    # Should return None immediately (async fetch)
    assert result is None

    # Wait for background thread to complete
    import time
    time.sleep(0.5)

    # Callback should have been called
    assert callback.called
    callback.assert_called_once()
    called_data = callback.call_args[0][0]
    assert called_data["lyrics"] == "Async lyrics"


@patch('core.lyrics.fetch_lyrics')
def test_fetch_async_cancels_existing_thread(mock_fetch_lyrics, lyrics_manager):
    """Test _fetch_async handles existing thread gracefully."""
    mock_fetch_lyrics.return_value = {
        "title": "Song",
        "artist": "Artist",
        "lyrics": "Lyrics",
        "url": "https://genius.com/song",
        "found": True
    }

    callback1 = MagicMock()
    callback2 = MagicMock()

    # Start first fetch
    lyrics_manager.get_lyrics("Artist", "Song", on_complete=callback1)

    # Start second fetch immediately (should handle existing thread)
    lyrics_manager.get_lyrics("Artist", "Song 2", on_complete=callback2)

    # Wait for threads to complete
    import time
    time.sleep(0.5)

    # Both callbacks should have been called
    assert callback1.called or callback2.called


def test_get_cache_stats_with_db_error(lyrics_manager):
    """Test get_cache_stats returns default dict on database error."""
    # Close the database to simulate error
    lyrics_manager.db.close()

    # Should return default stats without raising exception
    stats = lyrics_manager.get_cache_stats()
    assert stats == {"total_entries": 0, "found_lyrics": 0, "not_found": 0}
