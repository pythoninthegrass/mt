"""Unit tests for utils/lyrics module."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch


@patch('utils.lyrics.lyricsgenius.Genius')
@patch.object(Path, 'exists')
@patch('decouple.Config')
@patch('decouple.RepositoryEnv')
def test_get_genius_client_with_env_file(mock_repo_env, mock_config_class, mock_exists, mock_genius):
    """Test get_genius_client with .env file present."""
    from utils.lyrics import get_genius_client

    # Mock .env file exists
    mock_exists.return_value = True

    # Mock Config class and instance
    mock_config_instance = MagicMock()
    mock_config_instance.return_value = "test_token_from_env_file"
    mock_config_class.return_value = mock_config_instance

    # Mock Genius client
    mock_genius_instance = MagicMock()
    mock_genius.return_value = mock_genius_instance

    client = get_genius_client()

    # Verify Genius was initialized with token
    mock_genius.assert_called_once_with("test_token_from_env_file")
    assert client.verbose is False
    assert client.remove_section_headers is True
    assert client.skip_non_songs is False
    assert client.excluded_terms == ["(Remix)", "(Live)"]


@patch('utils.lyrics.lyricsgenius.Genius')
@patch.object(Path, 'exists')
@patch('decouple.config')
def test_get_genius_client_without_env_file(mock_config, mock_exists, mock_genius):
    """Test get_genius_client without .env file (uses default config)."""
    from utils.lyrics import get_genius_client

    # Mock .env file doesn't exist
    mock_exists.return_value = False

    # Mock config function to return test token
    mock_config.return_value = "test_token_from_default"

    # Mock Genius client
    mock_genius_instance = MagicMock()
    mock_genius.return_value = mock_genius_instance

    client = get_genius_client()

    # Verify Genius was initialized with token
    mock_genius.assert_called_once_with("test_token_from_default")
    assert client.verbose is False
    assert client.remove_section_headers is True


@patch('utils.lyrics.get_genius_client')
def test_fetch_lyrics_success(mock_get_client):
    """Test successful lyrics fetch."""
    from utils.lyrics import fetch_lyrics

    # Mock Genius client and song
    mock_song = MagicMock()
    mock_song.title = "Test Song"
    mock_song.artist = "Test Artist"
    mock_song.lyrics = "Test lyrics content"
    mock_song.url = "https://genius.com/test-song"

    mock_client = MagicMock()
    mock_client.search_song.return_value = mock_song
    mock_get_client.return_value = mock_client

    result = fetch_lyrics("Test Song", "Test Artist")

    assert result["found"] is True
    assert result["title"] == "Test Song"
    assert result["artist"] == "Test Artist"
    assert result["lyrics"] == "Test lyrics content"
    assert result["url"] == "https://genius.com/test-song"


@patch('utils.lyrics.get_genius_client')
def test_fetch_lyrics_not_found(mock_get_client):
    """Test lyrics fetch when song not found."""
    from utils.lyrics import fetch_lyrics

    # Mock Genius client returning None (not found)
    mock_client = MagicMock()
    mock_client.search_song.return_value = None
    mock_get_client.return_value = mock_client

    result = fetch_lyrics("Unknown Song", "Unknown Artist")

    assert result["found"] is False
    assert result["title"] == "Unknown Song"
    assert result["artist"] == "Unknown Artist"
    assert result["lyrics"] == ""
    assert result["url"] == ""


@patch('utils.lyrics.get_genius_client')
def test_fetch_lyrics_with_exception(mock_get_client):
    """Test lyrics fetch handles exceptions gracefully."""
    from utils.lyrics import fetch_lyrics

    # Mock Genius client to raise exception
    mock_get_client.side_effect = Exception("API Error")

    result = fetch_lyrics("Test Song", "Test Artist")

    assert result["found"] is False
    assert result["title"] == "Test Song"
    assert result["artist"] == "Test Artist"
    assert result["lyrics"] == ""
    assert result["url"] == ""
    assert "error" in result
    assert result["error"] == "API Error"


@patch('utils.lyrics.get_genius_client')
def test_fetch_lyrics_with_search_exception(mock_get_client):
    """Test lyrics fetch handles search_song exceptions."""
    from utils.lyrics import fetch_lyrics

    # Mock search_song to raise exception
    mock_client = MagicMock()
    mock_client.search_song.side_effect = Exception("Search failed")
    mock_get_client.return_value = mock_client

    result = fetch_lyrics("Test Song", "Test Artist")

    assert result["found"] is False
    assert "error" in result
    assert result["error"] == "Search failed"


@patch('utils.lyrics.get_genius_client')
def test_fetch_lyrics_with_album(mock_get_client):
    """Test fetch_lyrics passes through album parameter (for better matching)."""
    from utils.lyrics import fetch_lyrics

    # Mock successful search
    mock_song = MagicMock()
    mock_song.title = "Test Song"
    mock_song.artist = "Test Artist"
    mock_song.lyrics = "Test lyrics"
    mock_song.url = "https://genius.com/test"

    mock_client = MagicMock()
    mock_client.search_song.return_value = mock_song
    mock_get_client.return_value = mock_client

    result = fetch_lyrics("Test Song", "Test Artist", album="Test Album")

    # Album parameter is currently ignored by implementation, but test it's handled
    assert result["found"] is True
    mock_client.search_song.assert_called_once_with("Test Song", "Test Artist")
