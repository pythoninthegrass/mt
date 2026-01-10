"""Unit tests for playlist database operations."""

import pytest
import sqlite3
from core.db import DB_TABLES, MusicDatabase


@pytest.fixture
def in_memory_db():
    """Create an in-memory database for testing."""
    db = MusicDatabase(":memory:", DB_TABLES)

    # Add some test tracks to library for playlist operations
    test_tracks = [
        ("test1.mp3", "Song 1", "Artist A", "Album X", "01", "2020"),
        ("test2.mp3", "Song 2", "Artist B", "Album Y", "02", "2021"),
        ("test3.mp3", "Song 3", "Artist A", "Album X", "03", "2020"),
        ("test4.mp3", "Song 4", "Artist C", "Album Z", "04", "2022"),
        ("test5.mp3", "Song 5", "Artist B", "Album Y", "05", "2021"),
    ]

    for filepath, title, artist, album, track_num, date in test_tracks:
        db.add_to_library(filepath, {
            'title': title,
            'artist': artist,
            'album': album,
            'track_number': track_num,
            'date': date,
            'duration': 180.0
        })

    yield db
    db.close()


class TestPlaylistCRUD:
    """Test basic playlist CRUD operations."""

    def test_create_playlist(self, in_memory_db):
        """Test creating a new playlist."""
        playlist_id = in_memory_db.create_playlist("My Playlist")
        assert playlist_id > 0

        # Verify it exists
        name = in_memory_db.get_playlist_name(playlist_id)
        assert name == "My Playlist"

    def test_create_playlist_unique_name(self, in_memory_db):
        """Test that duplicate names are rejected."""
        in_memory_db.create_playlist("Duplicate")

        with pytest.raises(sqlite3.IntegrityError):
            in_memory_db.create_playlist("Duplicate")

    def test_list_playlists(self, in_memory_db):
        """Test listing all playlists ordered by created_at."""
        id1 = in_memory_db.create_playlist("Playlist 1")
        id2 = in_memory_db.create_playlist("Playlist 2")
        id3 = in_memory_db.create_playlist("Playlist 3")

        playlists = in_memory_db.list_playlists()
        assert len(playlists) == 3
        assert playlists[0] == (id1, "Playlist 1")
        assert playlists[1] == (id2, "Playlist 2")
        assert playlists[2] == (id3, "Playlist 3")

    def test_get_playlist_name(self, in_memory_db):
        """Test getting playlist name by ID."""
        playlist_id = in_memory_db.create_playlist("Test Playlist")
        name = in_memory_db.get_playlist_name(playlist_id)
        assert name == "Test Playlist"

        # Non-existent playlist
        name = in_memory_db.get_playlist_name(9999)
        assert name is None

    def test_rename_playlist(self, in_memory_db):
        """Test renaming a playlist."""
        playlist_id = in_memory_db.create_playlist("Old Name")
        success = in_memory_db.rename_playlist(playlist_id, "New Name")
        assert success is True

        name = in_memory_db.get_playlist_name(playlist_id)
        assert name == "New Name"

    def test_rename_playlist_duplicate_fails(self, in_memory_db):
        """Test that renaming to existing name fails."""
        in_memory_db.create_playlist("Playlist 1")
        playlist_id2 = in_memory_db.create_playlist("Playlist 2")

        with pytest.raises(sqlite3.IntegrityError):
            in_memory_db.rename_playlist(playlist_id2, "Playlist 1")

    def test_delete_playlist(self, in_memory_db):
        """Test deleting a playlist removes items too (cascade)."""
        # Create playlist and add tracks
        playlist_id = in_memory_db.create_playlist("To Delete")
        track_id = in_memory_db.get_track_id_by_filepath("test1.mp3")
        in_memory_db.add_tracks_to_playlist(playlist_id, [track_id])

        # Verify items exist
        items = in_memory_db.get_playlist_items(playlist_id)
        assert len(items) == 1

        # Delete playlist
        success = in_memory_db.delete_playlist(playlist_id)
        assert success is True

        # Verify playlist is gone
        name = in_memory_db.get_playlist_name(playlist_id)
        assert name is None

        # Verify items are gone (cascaded)
        items = in_memory_db.get_playlist_items(playlist_id)
        assert len(items) == 0


class TestPlaylistTrackManagement:
    """Test adding, removing, and reordering tracks in playlists."""

    def test_add_tracks_to_playlist(self, in_memory_db):
        """Test adding tracks to a playlist."""
        playlist_id = in_memory_db.create_playlist("Test Playlist")

        track_id1 = in_memory_db.get_track_id_by_filepath("test1.mp3")
        track_id2 = in_memory_db.get_track_id_by_filepath("test2.mp3")

        added = in_memory_db.add_tracks_to_playlist(playlist_id, [track_id1, track_id2])
        assert added == 2

        items = in_memory_db.get_playlist_items(playlist_id)
        assert len(items) == 2
        assert items[0][0] == "test1.mp3"  # filepath
        assert items[1][0] == "test2.mp3"

    def test_add_duplicate_track_ignored(self, in_memory_db):
        """Test that adding same track twice is idempotent."""
        playlist_id = in_memory_db.create_playlist("Test Playlist")
        track_id = in_memory_db.get_track_id_by_filepath("test1.mp3")

        # Add once
        added = in_memory_db.add_tracks_to_playlist(playlist_id, [track_id])
        assert added == 1

        # Add again - should be ignored
        added = in_memory_db.add_tracks_to_playlist(playlist_id, [track_id])
        assert added == 0

        # Verify only one copy
        items = in_memory_db.get_playlist_items(playlist_id)
        assert len(items) == 1

    def test_remove_tracks_from_playlist(self, in_memory_db):
        """Test removing tracks from playlist (not library)."""
        playlist_id = in_memory_db.create_playlist("Test Playlist")

        track_id1 = in_memory_db.get_track_id_by_filepath("test1.mp3")
        track_id2 = in_memory_db.get_track_id_by_filepath("test2.mp3")
        track_id3 = in_memory_db.get_track_id_by_filepath("test3.mp3")

        in_memory_db.add_tracks_to_playlist(playlist_id, [track_id1, track_id2, track_id3])

        # Remove middle track
        removed = in_memory_db.remove_tracks_from_playlist(playlist_id, [track_id2])
        assert removed == 1

        items = in_memory_db.get_playlist_items(playlist_id)
        assert len(items) == 2
        assert items[0][0] == "test1.mp3"
        assert items[1][0] == "test3.mp3"

        # Verify track still in library
        track = in_memory_db.get_track_by_filepath("test2.mp3")
        assert track is not None

    def test_get_playlist_items_ordered(self, in_memory_db):
        """Test that items are returned in position order."""
        playlist_id = in_memory_db.create_playlist("Test Playlist")

        track_id1 = in_memory_db.get_track_id_by_filepath("test1.mp3")
        track_id2 = in_memory_db.get_track_id_by_filepath("test2.mp3")
        track_id3 = in_memory_db.get_track_id_by_filepath("test3.mp3")

        in_memory_db.add_tracks_to_playlist(playlist_id, [track_id1, track_id2, track_id3])

        items = in_memory_db.get_playlist_items(playlist_id)
        assert len(items) == 3
        assert items[0][0] == "test1.mp3"
        assert items[1][0] == "test2.mp3"
        assert items[2][0] == "test3.mp3"

    def test_reorder_playlist(self, in_memory_db):
        """Test reordering tracks persists correctly."""
        playlist_id = in_memory_db.create_playlist("Test Playlist")

        track_id1 = in_memory_db.get_track_id_by_filepath("test1.mp3")
        track_id2 = in_memory_db.get_track_id_by_filepath("test2.mp3")
        track_id3 = in_memory_db.get_track_id_by_filepath("test3.mp3")

        in_memory_db.add_tracks_to_playlist(playlist_id, [track_id1, track_id2, track_id3])

        # Reorder: 3, 1, 2
        success = in_memory_db.reorder_playlist(playlist_id, [track_id3, track_id1, track_id2])
        assert success is True

        items = in_memory_db.get_playlist_items(playlist_id)
        assert len(items) == 3
        assert items[0][0] == "test3.mp3"
        assert items[1][0] == "test1.mp3"
        assert items[2][0] == "test2.mp3"


class TestPlaylistCascadeAndConstraints:
    """Test foreign key cascades and constraints."""

    def test_library_delete_cascades_to_playlist(self, in_memory_db):
        """Test that deleting from library removes from playlists (FK cascade)."""
        playlist_id = in_memory_db.create_playlist("Test Playlist")

        track_id = in_memory_db.get_track_id_by_filepath("test1.mp3")
        in_memory_db.add_tracks_to_playlist(playlist_id, [track_id])

        # Verify track in playlist
        items = in_memory_db.get_playlist_items(playlist_id)
        assert len(items) == 1

        # Delete from library
        success = in_memory_db.delete_from_library("test1.mp3")
        assert success is True

        # Verify removed from playlist (cascaded)
        items = in_memory_db.get_playlist_items(playlist_id)
        assert len(items) == 0


class TestPlaylistUtilities:
    """Test utility methods for playlist operations."""

    def test_get_track_id_by_filepath(self, in_memory_db):
        """Test resolving filepath to track_id."""
        track_id = in_memory_db.get_track_id_by_filepath("test1.mp3")
        assert track_id is not None
        assert track_id > 0

        # Non-existent file
        track_id = in_memory_db.get_track_id_by_filepath("nonexistent.mp3")
        assert track_id is None

    def test_generate_unique_name(self, in_memory_db):
        """Test auto-suffix generation: New playlist, New playlist (2), etc."""
        # First one should be "New playlist"
        name1 = in_memory_db.generate_unique_name()
        assert name1 == "New playlist"

        # Create it
        in_memory_db.create_playlist(name1)

        # Next should be "New playlist (2)"
        name2 = in_memory_db.generate_unique_name()
        assert name2 == "New playlist (2)"

        # Create it
        in_memory_db.create_playlist(name2)

        # Next should be "New playlist (3)"
        name3 = in_memory_db.generate_unique_name()
        assert name3 == "New playlist (3)"

    def test_generate_unique_name_with_gaps(self, in_memory_db):
        """Test suffix generation when intermediate names exist."""
        # Create playlists with gaps: 1, 3, 5
        in_memory_db.create_playlist("New playlist")
        in_memory_db.create_playlist("New playlist (3)")
        in_memory_db.create_playlist("New playlist (5)")

        # Should find (2)
        name = in_memory_db.generate_unique_name()
        assert name == "New playlist (2)"

    def test_generate_unique_name_custom_base(self, in_memory_db):
        """Test unique name generation with custom base name."""
        name1 = in_memory_db.generate_unique_name("My Favorites")
        assert name1 == "My Favorites"

        in_memory_db.create_playlist(name1)

        name2 = in_memory_db.generate_unique_name("My Favorites")
        assert name2 == "My Favorites (2)"


class TestPlaylistItemMetadata:
    """Test that playlist items return correct metadata."""

    def test_playlist_items_include_metadata(self, in_memory_db):
        """Test that get_playlist_items returns full track metadata."""
        playlist_id = in_memory_db.create_playlist("Test Playlist")

        track_id = in_memory_db.get_track_id_by_filepath("test1.mp3")
        in_memory_db.add_tracks_to_playlist(playlist_id, [track_id])

        items = in_memory_db.get_playlist_items(playlist_id)
        assert len(items) == 1

        # Verify metadata fields: (filepath, artist, title, album, track_number, date, track_id)
        filepath, artist, title, album, track_num, date, track_id_returned = items[0]
        assert filepath == "test1.mp3"
        assert artist == "Artist A"
        assert title == "Song 1"
        assert album == "Album X"
        assert track_num == "01"
        assert date == "2020"
        assert track_id_returned == track_id
