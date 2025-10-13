"""Unit tests for LibraryManager using mocked database.

These tests use mocked database to avoid external dependencies.
They run fast (<1s total) and test core logic deterministically.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.library import LibraryManager


@pytest.fixture
def mock_db():
    """Mock MusicDatabase."""
    db = Mock()
    db.get_library_items.return_value = []
    db.get_existing_files.return_value = set()
    db.add_to_library.return_value = None
    db.find_file_by_metadata.return_value = None
    db.search_library.return_value = []
    db.get_library_statistics.return_value = {}
    db.get_top_25_most_played.return_value = []
    db.delete_from_library.return_value = True
    return db


@pytest.fixture
def library_manager(mock_db):
    """Create LibraryManager with mocked database."""
    return LibraryManager(mock_db)


class TestLibraryManagerInitialization:
    """Test LibraryManager initialization."""

    def test_initialization(self, library_manager, mock_db):
        """Test that LibraryManager initializes with correct database reference."""
        assert library_manager.db == mock_db


class TestLibraryManagerBasicOperations:
    """Test basic library operations."""

    def test_get_library_items(self, library_manager, mock_db):
        """Test getting library items."""
        expected_items = [
            {"id": 1, "filepath": "/test/song1.mp3", "title": "Song 1"},
            {"id": 2, "filepath": "/test/song2.mp3", "title": "Song 2"},
        ]
        mock_db.get_library_items.return_value = expected_items

        items = library_manager.get_library_items()

        assert items == expected_items
        mock_db.get_library_items.assert_called_once()

    def test_get_existing_files(self, library_manager, mock_db):
        """Test getting set of existing files."""
        expected_files = {"/test/song1.mp3", "/test/song2.mp3"}
        mock_db.get_existing_files.return_value = expected_files

        files = library_manager.get_existing_files()

        assert files == expected_files
        mock_db.get_existing_files.assert_called_once()

    def test_delete_from_library(self, library_manager, mock_db):
        """Test deleting a file from library."""
        filepath = "/test/song.mp3"
        mock_db.delete_from_library.return_value = True

        result = library_manager.delete_from_library(filepath)

        assert result is True
        mock_db.delete_from_library.assert_called_once_with(filepath)

    def test_delete_from_library_failure(self, library_manager, mock_db):
        """Test deleting a non-existent file from library."""
        filepath = "/test/nonexistent.mp3"
        mock_db.delete_from_library.return_value = False

        result = library_manager.delete_from_library(filepath)

        assert result is False
        mock_db.delete_from_library.assert_called_once_with(filepath)


class TestLibraryManagerSearch:
    """Test library search functionality."""

    def test_find_file_by_metadata(self, library_manager, mock_db):
        """Test finding a file by metadata."""
        title = "Test Song"
        artist = "Test Artist"
        expected_result = "/test/song.mp3"
        mock_db.find_file_by_metadata.return_value = expected_result

        result = library_manager.find_file_by_metadata(title, artist)

        assert result == expected_result
        mock_db.find_file_by_metadata.assert_called_once_with(title, artist, None, None)

    def test_search_library(self, library_manager, mock_db):
        """Test searching library."""
        query = "test query"
        expected_results = [
            {"id": 1, "title": "Test Song 1"},
            {"id": 2, "title": "Test Song 2"},
        ]
        mock_db.search_library.return_value = expected_results

        results = library_manager.search_library(query)

        assert results == expected_results
        mock_db.search_library.assert_called_once_with(query)


class TestLibraryManagerStatistics:
    """Test library statistics functionality."""

    def test_get_library_statistics(self, library_manager, mock_db):
        """Test getting library statistics."""
        expected_stats = {
            "total_tracks": 100,
            "total_artists": 25,
            "total_albums": 15,
            "total_duration": 36000,
        }
        mock_db.get_library_statistics.return_value = expected_stats

        stats = library_manager.get_library_statistics()

        assert stats == expected_stats
        mock_db.get_library_statistics.assert_called_once()

    def test_get_top_25_most_played(self, library_manager, mock_db):
        """Test getting top 25 most played tracks."""
        expected_tracks = [
            {"id": 1, "title": "Popular Song 1", "play_count": 50},
            {"id": 2, "title": "Popular Song 2", "play_count": 45},
        ]
        mock_db.get_top_25_most_played.return_value = expected_tracks

        tracks = library_manager.get_top_25_most_played()

        assert tracks == expected_tracks
        mock_db.get_top_25_most_played.assert_called_once()
