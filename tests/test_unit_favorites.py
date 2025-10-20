"""Unit tests for FavoritesManager using mocked database.

These tests use mocked database to avoid external dependencies.
They run fast (<1s total) and test core logic deterministically.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, call

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.favorites import FavoritesManager


@pytest.fixture
def mock_db():
    """Mock MusicDatabase."""
    db = Mock()
    db.is_favorite.return_value = False
    db.add_favorite.return_value = True
    db.remove_favorite.return_value = True
    db.get_liked_songs.return_value = []
    return db


@pytest.fixture
def favorites_manager(mock_db):
    """Create FavoritesManager with mocked database."""
    return FavoritesManager(mock_db)


class TestFavoritesManagerInitialization:
    """Test FavoritesManager initialization."""

    def test_initialization(self, favorites_manager, mock_db):
        """Test that FavoritesManager initializes with correct database reference."""
        assert favorites_manager.db == mock_db
        assert favorites_manager._on_favorites_changed_callback is None


class TestFavoritesManagerCallback:
    """Test callback registration and invocation."""

    def test_set_callback(self, favorites_manager):
        """Test setting favorites changed callback."""
        callback = Mock()
        favorites_manager.set_on_favorites_changed_callback(callback)
        assert favorites_manager._on_favorites_changed_callback == callback

    def test_callback_invoked_on_favorite(self, favorites_manager, mock_db):
        """Test callback is invoked when a track is favorited."""
        callback = Mock()
        favorites_manager.set_on_favorites_changed_callback(callback)

        mock_db.is_favorite.return_value = False
        mock_db.add_favorite.return_value = True

        favorites_manager.toggle_favorite("/path/to/track.mp3")
        callback.assert_called_once()

    def test_callback_invoked_on_unfavorite(self, favorites_manager, mock_db):
        """Test callback is invoked when a track is unfavorited."""
        callback = Mock()
        favorites_manager.set_on_favorites_changed_callback(callback)

        mock_db.is_favorite.return_value = True
        mock_db.remove_favorite.return_value = True

        favorites_manager.toggle_favorite("/path/to/track.mp3")
        callback.assert_called_once()

    def test_callback_not_invoked_when_not_set(self, favorites_manager, mock_db):
        """Test no error when callback is not set."""
        mock_db.is_favorite.return_value = False
        mock_db.add_favorite.return_value = True

        # Should not raise an error
        favorites_manager.toggle_favorite("/path/to/track.mp3")

    def test_callback_not_invoked_on_db_failure(self, favorites_manager, mock_db):
        """Test callback is not invoked when database operation fails."""
        callback = Mock()
        favorites_manager.set_on_favorites_changed_callback(callback)

        mock_db.is_favorite.return_value = False
        mock_db.add_favorite.return_value = False  # Simulate failure

        favorites_manager.toggle_favorite("/path/to/track.mp3")
        callback.assert_not_called()


class TestFavoritesManagerToggleFavorite:
    """Test toggle_favorite functionality."""

    def test_toggle_favorite_adds_when_not_favorited(self, favorites_manager, mock_db):
        """Test toggling a non-favorited track adds it to favorites."""
        mock_db.is_favorite.return_value = False
        mock_db.add_favorite.return_value = True

        result = favorites_manager.toggle_favorite("/path/to/track.mp3")

        assert result is True
        mock_db.is_favorite.assert_called_once_with("/path/to/track.mp3")
        mock_db.add_favorite.assert_called_once_with("/path/to/track.mp3")
        mock_db.remove_favorite.assert_not_called()

    def test_toggle_favorite_removes_when_favorited(self, favorites_manager, mock_db):
        """Test toggling a favorited track removes it from favorites."""
        mock_db.is_favorite.return_value = True
        mock_db.remove_favorite.return_value = True

        result = favorites_manager.toggle_favorite("/path/to/track.mp3")

        assert result is False
        mock_db.is_favorite.assert_called_once_with("/path/to/track.mp3")
        mock_db.remove_favorite.assert_called_once_with("/path/to/track.mp3")
        mock_db.add_favorite.assert_not_called()

    def test_toggle_favorite_returns_false_on_remove_failure(self, favorites_manager, mock_db):
        """Test toggle returns False when remove operation fails."""
        mock_db.is_favorite.return_value = True
        mock_db.remove_favorite.return_value = False  # Simulate failure

        result = favorites_manager.toggle_favorite("/path/to/track.mp3")

        assert result is False
        mock_db.remove_favorite.assert_called_once_with("/path/to/track.mp3")

    def test_toggle_favorite_returns_true_on_add_failure(self, favorites_manager, mock_db):
        """Test toggle returns True when add operation fails (still attempts to favorite)."""
        mock_db.is_favorite.return_value = False
        mock_db.add_favorite.return_value = False  # Simulate failure

        result = favorites_manager.toggle_favorite("/path/to/track.mp3")

        assert result is True
        mock_db.add_favorite.assert_called_once_with("/path/to/track.mp3")

    def test_toggle_favorite_multiple_times(self, favorites_manager, mock_db):
        """Test toggling a track multiple times alternates state."""
        # First toggle: add
        mock_db.is_favorite.return_value = False
        mock_db.add_favorite.return_value = True
        result1 = favorites_manager.toggle_favorite("/path/to/track.mp3")
        assert result1 is True

        # Second toggle: remove
        mock_db.is_favorite.return_value = True
        mock_db.remove_favorite.return_value = True
        result2 = favorites_manager.toggle_favorite("/path/to/track.mp3")
        assert result2 is False

        # Third toggle: add again
        mock_db.is_favorite.return_value = False
        mock_db.add_favorite.return_value = True
        result3 = favorites_manager.toggle_favorite("/path/to/track.mp3")
        assert result3 is True

    def test_toggle_favorite_with_different_paths(self, favorites_manager, mock_db):
        """Test toggling different tracks independently."""
        mock_db.is_favorite.return_value = False
        mock_db.add_favorite.return_value = True

        favorites_manager.toggle_favorite("/path/to/track1.mp3")
        favorites_manager.toggle_favorite("/path/to/track2.mp3")

        assert mock_db.add_favorite.call_count == 2
        mock_db.add_favorite.assert_any_call("/path/to/track1.mp3")
        mock_db.add_favorite.assert_any_call("/path/to/track2.mp3")


class TestFavoritesManagerIsFavorite:
    """Test is_favorite functionality."""

    def test_is_favorite_true(self, favorites_manager, mock_db):
        """Test is_favorite returns True for favorited tracks."""
        mock_db.is_favorite.return_value = True

        result = favorites_manager.is_favorite("/path/to/track.mp3")

        assert result is True
        mock_db.is_favorite.assert_called_once_with("/path/to/track.mp3")

    def test_is_favorite_false(self, favorites_manager, mock_db):
        """Test is_favorite returns False for non-favorited tracks."""
        mock_db.is_favorite.return_value = False

        result = favorites_manager.is_favorite("/path/to/track.mp3")

        assert result is False
        mock_db.is_favorite.assert_called_once_with("/path/to/track.mp3")

    def test_is_favorite_different_paths(self, favorites_manager, mock_db):
        """Test is_favorite with different file paths."""
        def mock_is_favorite(filepath):
            return filepath == "/favorited/track.mp3"

        mock_db.is_favorite.side_effect = mock_is_favorite

        assert favorites_manager.is_favorite("/favorited/track.mp3") is True
        assert favorites_manager.is_favorite("/not/favorited/track.mp3") is False


class TestFavoritesManagerGetLikedSongs:
    """Test get_liked_songs functionality."""

    def test_get_liked_songs_empty(self, favorites_manager, mock_db):
        """Test get_liked_songs returns empty list when no favorites."""
        mock_db.get_liked_songs.return_value = []

        result = favorites_manager.get_liked_songs()

        assert result == []
        mock_db.get_liked_songs.assert_called_once()

    def test_get_liked_songs_with_tracks(self, favorites_manager, mock_db):
        """Test get_liked_songs returns list of favorited tracks."""
        expected_songs = [
            ("/path/to/track1.mp3", "Artist 1", "Title 1", "Album 1", 1, "2024-01-01"),
            ("/path/to/track2.mp3", "Artist 2", "Title 2", "Album 2", 2, "2024-01-02"),
        ]
        mock_db.get_liked_songs.return_value = expected_songs

        result = favorites_manager.get_liked_songs()

        assert result == expected_songs
        mock_db.get_liked_songs.assert_called_once()

    def test_get_liked_songs_preserves_order(self, favorites_manager, mock_db):
        """Test get_liked_songs preserves the order from database (FIFO)."""
        songs_in_order = [
            ("/first.mp3", "Artist", "First", "Album", 1, "2024-01-01"),
            ("/second.mp3", "Artist", "Second", "Album", 2, "2024-01-02"),
            ("/third.mp3", "Artist", "Third", "Album", 3, "2024-01-03"),
        ]
        mock_db.get_liked_songs.return_value = songs_in_order

        result = favorites_manager.get_liked_songs()

        assert result == songs_in_order
        assert result[0][2] == "First"
        assert result[1][2] == "Second"
        assert result[2][2] == "Third"


class TestFavoritesManagerIntegration:
    """Test integration scenarios."""

    def test_full_favorite_workflow(self, favorites_manager, mock_db):
        """Test complete workflow: check, favorite, check again, unfavorite."""
        filepath = "/path/to/track.mp3"

        # Initially not favorited
        mock_db.is_favorite.return_value = False
        assert favorites_manager.is_favorite(filepath) is False

        # Favorite the track
        mock_db.add_favorite.return_value = True
        result = favorites_manager.toggle_favorite(filepath)
        assert result is True

        # Now it's favorited
        mock_db.is_favorite.return_value = True
        assert favorites_manager.is_favorite(filepath) is True

        # Unfavorite the track
        mock_db.remove_favorite.return_value = True
        result = favorites_manager.toggle_favorite(filepath)
        assert result is False

        # Back to not favorited
        mock_db.is_favorite.return_value = False
        assert favorites_manager.is_favorite(filepath) is False

    def test_callback_invoked_twice_in_workflow(self, favorites_manager, mock_db):
        """Test callback is invoked for both favorite and unfavorite operations."""
        callback = Mock()
        favorites_manager.set_on_favorites_changed_callback(callback)

        # Favorite
        mock_db.is_favorite.return_value = False
        mock_db.add_favorite.return_value = True
        favorites_manager.toggle_favorite("/path/to/track.mp3")

        # Unfavorite
        mock_db.is_favorite.return_value = True
        mock_db.remove_favorite.return_value = True
        favorites_manager.toggle_favorite("/path/to/track.mp3")

        assert callback.call_count == 2
