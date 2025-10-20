"""Property-based tests for database operations using Hypothesis.

These tests verify invariants in database operations like favorites toggle,
queue integrity, and metadata consistency. They run fast with the 'fast' profile.
"""

import pytest
import sys
from hypothesis import assume, given, strategies as st
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.db import DB_TABLES, MusicDatabase


def create_test_db():
    """Helper to create a test database."""
    return MusicDatabase(":memory:", DB_TABLES)


class TestFavoritesToggleInvariants:
    """Test invariants of favorites toggle operations."""

    @given(st.integers(min_value=1, max_value=50))
    def test_toggle_favorite_even_times_returns_to_original(self, n):
        """Test that toggling favorite an even number of times returns to original state."""
        db = create_test_db()
        try:
            filepath = "/test/path.mp3"
            metadata = {"artist": "Artist", "title": "Title", "album": "Album"}
            db.add_to_library(filepath, metadata)

            initial_state = db.is_favorite(filepath)

            # Toggle n*2 times (even number)
            for _ in range(n * 2):
                if db.is_favorite(filepath):
                    db.remove_favorite(filepath)
                else:
                    db.add_favorite(filepath)

            final_state = db.is_favorite(filepath)
            assert initial_state == final_state
        finally:
            db.close()

    @given(st.lists(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=15), min_size=1, max_size=10, unique=True))
    def test_favorite_count_matches_operations(self, filenames):
        """Test that the number of favorited tracks matches add_favorite operations."""
        db = create_test_db()
        try:
            for filename in filenames:
                filepath = f"/path/{filename}.mp3"
                db.add_to_library(filepath, {"artist": "Artist", "title": filename, "album": "Album"})
                db.add_favorite(filepath)

            liked_songs = db.get_liked_songs()
            assert len(liked_songs) == len(filenames)
        finally:
            db.close()

    def test_favorite_is_idempotent(self):
        """Test that adding a favorite multiple times has same effect as adding once."""
        db = create_test_db()
        try:
            filepath = "/test/song.mp3"
            db.add_to_library(filepath, {"artist": "Artist", "title": "Title", "album": "Album"})

            for _ in range(5):
                db.add_favorite(filepath)

            assert db.is_favorite(filepath) is True
            assert len(db.get_liked_songs()) == 1
        finally:
            db.close()

    def test_unfavorite_is_idempotent(self):
        """Test that removing a favorite multiple times has same effect as removing once."""
        db = create_test_db()
        try:
            filepath = "/test/song.mp3"
            db.add_to_library(filepath, {"artist": "Artist", "title": "Title", "album": "Album"})
            db.add_favorite(filepath)

            for _ in range(5):
                db.remove_favorite(filepath)

            assert db.is_favorite(filepath) is False
            assert len(db.get_liked_songs()) == 0
        finally:
            db.close()


class TestQueueIntegrityInvariants:
    """Test invariants of queue operations."""

    @given(st.integers(min_value=1, max_value=15))
    def test_queue_size_matches_additions(self, n):
        """Test that queue size matches number of additions."""
        db = create_test_db()
        try:
            for i in range(n):
                filepath = f"/path/song{i}.mp3"
                db.add_to_library(filepath, {"artist": f"Artist {i}", "title": f"Title {i}", "album": "Album"})
                db.add_to_queue(filepath)

            queue_items = db.get_queue_items()
            assert len(queue_items) == n
        finally:
            db.close()

    def test_clear_queue_removes_all_items(self):
        """Test that clear_queue removes all items regardless of queue size."""
        db = create_test_db()
        try:
            for i in range(10):
                filepath = f"/path/song{i}.mp3"
                db.add_to_library(filepath, {"artist": "Artist", "title": f"Title {i}", "album": "Album"})
                db.add_to_queue(filepath)

            db.clear_queue()
            assert len(db.get_queue_items()) == 0
        finally:
            db.close()

    def test_clear_empty_queue_is_safe(self):
        """Test that clearing an empty queue doesn't raise errors."""
        db = create_test_db()
        try:
            for _ in range(3):
                db.clear_queue()
            assert len(db.get_queue_items()) == 0
        finally:
            db.close()


class TestMetadataConsistency:
    """Test metadata consistency invariants."""

    @given(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=1, max_size=20),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=1, max_size=20),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=1, max_size=20),
    )
    def test_metadata_roundtrip_preserves_values(self, artist, title, album):
        """Test that metadata written can be read back unchanged."""
        artist = artist.strip()
        title = title.strip()
        album = album.strip()
        assume(artist and title and album)

        db = create_test_db()
        try:
            filepath = "/test/song.mp3"
            metadata = {"artist": artist, "title": title, "album": album}
            db.add_to_library(filepath, metadata)

            retrieved = db.get_metadata_by_filepath(filepath)
            assert retrieved["artist"] == artist
            assert retrieved["title"] == title
            assert retrieved["album"] == album
        finally:
            db.close()

    @given(st.lists(st.integers(min_value=1, max_value=10), min_size=1, max_size=15))
    def test_play_count_updates_succeed(self, play_sequence):
        """Test that play count updates succeed without errors."""
        db = create_test_db()
        try:
            filepath = "/test/song.mp3"
            db.add_to_library(filepath, {"artist": "Artist", "title": "Title", "album": "Album"})

            for _ in play_sequence:
                db.update_play_count(filepath)
            # Test succeeds if no exceptions raised
        finally:
            db.close()


class TestPreferencesPersistence:
    """Test preferences persistence invariants."""

    @given(st.booleans(), st.booleans())
    def test_loop_and_shuffle_independent(self, loop_state, shuffle_state):
        """Test that loop and shuffle settings are independent."""
        db = create_test_db()
        try:
            db.set_loop_enabled(loop_state)
            db.set_shuffle_enabled(shuffle_state)

            assert db.get_loop_enabled() == loop_state
            assert db.get_shuffle_enabled() == shuffle_state
        finally:
            db.close()

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=1, max_size=15))
    def test_ui_preference_overwrites_previous_value(self, key):
        """Test that setting a UI preference multiple times keeps only the last value."""
        db = create_test_db()
        try:
            db.set_ui_preference(key, "value1")
            db.set_ui_preference(key, "value2")
            db.set_ui_preference(key, "value3")

            result = db.get_ui_preference(key)
            assert result == "value3"
        finally:
            db.close()

    @given(st.integers(min_value=100, max_value=2000), st.integers(min_value=100, max_value=1500))
    def test_window_size_persistence(self, width, height):
        """Test that window size is persisted correctly."""
        db = create_test_db()
        try:
            db.set_window_size(width, height)
            retrieved = db.get_window_size()
            assert retrieved == (width, height)
        finally:
            db.close()


class TestLibrarySearchInvariants:
    """Test search operation invariants."""

    def test_search_empty_library_returns_empty(self):
        """Test that searching empty library always returns empty results."""
        db = create_test_db()
        try:
            for search_term in ["test", "artist", "album", ""]:
                results = db.search_library(search_term)
                assert results == []
        finally:
            db.close()

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=15))
    def test_search_is_case_insensitive(self, search_term):
        """Test that search works case-insensitively."""
        db = create_test_db()
        try:
            filepath = "/test/song.mp3"
            db.add_to_library(filepath, {"artist": "Artist", "title": search_term, "album": "Album"})

            results_lower = db.search_library(search_term.lower())
            results_upper = db.search_library(search_term.upper())
            results_mixed = db.search_library(search_term.capitalize())

            assert len(results_lower) > 0
            assert len(results_upper) > 0
            assert len(results_mixed) > 0
        finally:
            db.close()
