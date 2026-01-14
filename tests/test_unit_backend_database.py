"""Unit tests for backend database service (Tauri migration)."""

import pytest
import sqlite3
import tempfile
from backend.services.database import DatabaseService
from pathlib import Path


@pytest.fixture
def backend_db():
    """Create an in-memory backend database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db = DatabaseService(db_path)
    yield db

    db_path.unlink(missing_ok=True)


@pytest.fixture
def backend_db_with_tracks(backend_db):
    """Backend database pre-populated with test tracks."""
    tracks = [
        ("/path/song1.mp3", {"title": "Song 1", "artist": "Artist 1", "album": "Album 1"}),
        ("/path/song2.mp3", {"title": "Song 2", "artist": "Artist 2", "album": "Album 2"}),
        ("/path/song3.mp3", {"title": "Song 3", "artist": "Artist 3", "album": "Album 3"}),
    ]
    for filepath, metadata in tracks:
        backend_db.add_track(filepath, metadata)
    return backend_db


class TestBackendDatabaseForeignKeys:
    """Test that foreign key constraints work correctly."""

    def test_foreign_keys_enabled_per_connection(self, backend_db):
        """Verify PRAGMA foreign_keys is ON for each connection."""
        with backend_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys")
            result = cursor.fetchone()[0]
            assert result == 1, "foreign_keys should be enabled"


class TestBackendTrackDeletion:
    """Test track deletion and metadata cleanup."""

    def test_delete_track_removes_from_library(self, backend_db_with_tracks):
        """Deleting a track removes it from the library table."""
        tracks, _ = backend_db_with_tracks.get_all_tracks()
        assert len(tracks) == 3

        track_id = tracks[0]["id"]
        result = backend_db_with_tracks.delete_track(track_id)
        assert result is True

        tracks_after, _ = backend_db_with_tracks.get_all_tracks()
        assert len(tracks_after) == 2
        assert all(t["id"] != track_id for t in tracks_after)

    def test_delete_track_removes_from_favorites(self, backend_db_with_tracks):
        """Deleting a track removes it from favorites."""
        tracks, _ = backend_db_with_tracks.get_all_tracks()
        track_id = tracks[0]["id"]

        backend_db_with_tracks.add_favorite(track_id)
        is_fav, _ = backend_db_with_tracks.is_favorite(track_id)
        assert is_fav is True

        backend_db_with_tracks.delete_track(track_id)

        favorites, total = backend_db_with_tracks.get_favorites()
        assert total == 0
        assert len(favorites) == 0

    def test_delete_track_removes_from_playlist_items(self, backend_db_with_tracks):
        """Deleting a track removes it from all playlists."""
        tracks, _ = backend_db_with_tracks.get_all_tracks()
        track_id = tracks[0]["id"]

        playlist = backend_db_with_tracks.create_playlist("Test Playlist")
        playlist_id = playlist["id"]
        backend_db_with_tracks.add_tracks_to_playlist(playlist_id, [track_id])

        playlist_before = backend_db_with_tracks.get_playlist(playlist_id)
        assert playlist_before["track_count"] == 1

        backend_db_with_tracks.delete_track(track_id)

        playlist_after = backend_db_with_tracks.get_playlist(playlist_id)
        assert playlist_after["track_count"] == 0

    def test_delete_track_removes_from_top_25(self, backend_db_with_tracks):
        """Deleting a track removes it from top 25 most played."""
        tracks, _ = backend_db_with_tracks.get_all_tracks()
        track_id = tracks[0]["id"]

        for _ in range(5):
            backend_db_with_tracks.update_play_count(track_id)

        top_25 = backend_db_with_tracks.get_top_25()
        assert len(top_25) == 1
        assert top_25[0]["id"] == track_id

        backend_db_with_tracks.delete_track(track_id)

        top_25_after = backend_db_with_tracks.get_top_25()
        assert len(top_25_after) == 0

    def test_delete_nonexistent_track_returns_false(self, backend_db):
        """Deleting a nonexistent track returns False."""
        result = backend_db.delete_track(99999)
        assert result is False

    def test_delete_track_preserves_other_tracks(self, backend_db_with_tracks):
        """Deleting one track doesn't affect other tracks."""
        tracks, _ = backend_db_with_tracks.get_all_tracks()
        track_to_delete = tracks[0]["id"]
        other_track_ids = [t["id"] for t in tracks[1:]]

        for tid in other_track_ids:
            backend_db_with_tracks.add_favorite(tid)
            backend_db_with_tracks.update_play_count(tid)

        backend_db_with_tracks.delete_track(track_to_delete)

        tracks_after, _ = backend_db_with_tracks.get_all_tracks()
        assert len(tracks_after) == 2

        favorites, _ = backend_db_with_tracks.get_favorites()
        assert len(favorites) == 2

        top_25 = backend_db_with_tracks.get_top_25()
        assert len(top_25) == 2


class TestBackendPlayCount:
    """Test play count and last played updates."""

    def test_update_play_count_increments(self, backend_db_with_tracks):
        """Play count increments correctly."""
        tracks, _ = backend_db_with_tracks.get_all_tracks()
        track_id = tracks[0]["id"]

        result = backend_db_with_tracks.update_play_count(track_id)
        assert result["play_count"] == 1

        result = backend_db_with_tracks.update_play_count(track_id)
        assert result["play_count"] == 2

    def test_update_play_count_sets_last_played(self, backend_db_with_tracks):
        """Updating play count also sets last_played timestamp."""
        tracks, _ = backend_db_with_tracks.get_all_tracks()
        track_id = tracks[0]["id"]

        track_before = backend_db_with_tracks.get_track_by_id(track_id)
        assert track_before["last_played"] is None

        backend_db_with_tracks.update_play_count(track_id)

        track_after = backend_db_with_tracks.get_track_by_id(track_id)
        assert track_after["last_played"] is not None

    def test_update_play_count_nonexistent_track(self, backend_db):
        """Updating play count for nonexistent track returns None."""
        result = backend_db.update_play_count(99999)
        assert result is None


class TestBackendDynamicPlaylists:
    """Test dynamic playlist queries after deletion."""

    def test_deleted_track_not_in_recently_added(self, backend_db_with_tracks):
        """Deleted tracks don't appear in recently added results."""
        tracks, _ = backend_db_with_tracks.get_all_tracks(sort_by="added_date", sort_order="desc")
        track_id = tracks[0]["id"]

        backend_db_with_tracks.delete_track(track_id)

        tracks_after, _ = backend_db_with_tracks.get_all_tracks(sort_by="added_date", sort_order="desc")
        assert all(t["id"] != track_id for t in tracks_after)

    def test_deleted_track_not_in_top_25(self, backend_db_with_tracks):
        """Deleted tracks don't appear in top 25."""
        tracks, _ = backend_db_with_tracks.get_all_tracks()
        track_id = tracks[0]["id"]

        for _ in range(10):
            backend_db_with_tracks.update_play_count(track_id)

        backend_db_with_tracks.delete_track(track_id)

        top_25 = backend_db_with_tracks.get_top_25()
        assert all(t["id"] != track_id for t in top_25)
