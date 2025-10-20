"""Unit tests for file utility functions.

These tests use mocked filesystem operations and temporary directories.
They run fast (<1s total) and test core logic deterministically.
"""

import pytest
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.files import find_audio_files, normalize_path


class TestNormalizePath:
    """Test normalize_path functionality."""

    def test_normalize_path_with_path_object(self):
        """Test normalize_path returns Path object unchanged."""
        path_obj = Path("/some/path")
        result = normalize_path(path_obj)
        assert result == path_obj
        assert isinstance(result, Path)

    def test_normalize_path_with_simple_string(self):
        """Test normalize_path converts simple string to Path."""
        result = normalize_path("/some/path")
        assert isinstance(result, Path)
        assert str(result) == "/some/path"

    def test_normalize_path_strips_curly_braces(self):
        """Test normalize_path removes curly braces from tkinter drop strings."""
        result = normalize_path("{/some/path}")
        assert str(result) == "/some/path"

    def test_normalize_path_strips_quotes(self):
        """Test normalize_path removes quotes from paths."""
        result = normalize_path('"/some/path"')
        assert str(result) == "/some/path"

    def test_normalize_path_strips_both_braces_and_quotes(self):
        """Test normalize_path removes both curly braces and quotes."""
        result = normalize_path('{"/some/path"}')
        assert str(result) == "/some/path"

    def test_normalize_path_with_spaces(self):
        """Test normalize_path handles paths with spaces."""
        result = normalize_path("/some/path with spaces")
        assert str(result) == "/some/path with spaces"

    def test_normalize_path_with_special_characters(self):
        """Test normalize_path handles paths with special characters."""
        result = normalize_path("/some/path/file-name_123.mp3")
        assert str(result) == "/some/path/file-name_123.mp3"

    @patch('sys.platform', 'darwin')
    @patch('os.path.exists')
    @patch('os.path.realpath')
    @patch('os.path.abspath')
    def test_normalize_path_macos_volumes_exists(self, mock_abspath, mock_realpath, mock_exists):
        """Test normalize_path resolves /Volumes/ paths on macOS when they exist."""
        mock_abspath.return_value = "/Volumes/External/music"
        mock_realpath.return_value = "/Volumes/External/music"
        mock_exists.return_value = True

        result = normalize_path("/Volumes/External/music")

        assert isinstance(result, Path)
        assert str(result) == "/Volumes/External/music"
        mock_abspath.assert_called_once_with("/Volumes/External/music")
        mock_realpath.assert_called_once_with("/Volumes/External/music")
        mock_exists.assert_called_once_with("/Volumes/External/music")

    @patch('sys.platform', 'darwin')
    @patch('os.path.exists')
    @patch('os.path.realpath')
    @patch('os.path.abspath')
    def test_normalize_path_macos_volumes_not_exists(self, mock_abspath, mock_realpath, mock_exists):
        """Test normalize_path falls back when /Volumes/ path doesn't exist."""
        mock_abspath.return_value = "/Volumes/External/music"
        mock_realpath.return_value = "/Volumes/External/music"
        mock_exists.return_value = False

        result = normalize_path("/Volumes/External/music")

        assert isinstance(result, Path)
        assert str(result) == "/Volumes/External/music"

    @patch('sys.platform', 'darwin')
    @patch('os.path.abspath', side_effect=OSError("Mock error"))
    def test_normalize_path_macos_volumes_oserror(self, mock_abspath):
        """Test normalize_path handles OSError gracefully for /Volumes/ paths."""
        result = normalize_path("/Volumes/External/music")

        assert isinstance(result, Path)
        assert str(result) == "/Volumes/External/music"

    @patch('sys.platform', 'darwin')
    @patch('os.path.abspath', side_effect=ValueError("Mock error"))
    def test_normalize_path_macos_volumes_valueerror(self, mock_abspath):
        """Test normalize_path handles ValueError gracefully for /Volumes/ paths."""
        result = normalize_path("/Volumes/External/music")

        assert isinstance(result, Path)
        assert str(result) == "/Volumes/External/music"

    @patch('sys.platform', 'linux')
    def test_normalize_path_non_macos_volumes(self):
        """Test normalize_path doesn't resolve /Volumes/ on non-macOS platforms."""
        result = normalize_path("/Volumes/External/music")

        assert isinstance(result, Path)
        assert str(result) == "/Volumes/External/music"

    def test_normalize_path_idempotent(self):
        """Test normalize_path is idempotent (applying twice gives same result)."""
        path1 = normalize_path("/some/path")
        path2 = normalize_path(path1)
        assert path1 == path2


class TestFindAudioFiles:
    """Test find_audio_files functionality."""

    def test_find_audio_files_empty_directory(self, tmp_path):
        """Test find_audio_files returns empty list for empty directory."""
        result = find_audio_files(tmp_path)
        assert result == []

    def test_find_audio_files_with_mp3_files(self, tmp_path):
        """Test find_audio_files finds MP3 files."""
        # Create test files
        (tmp_path / "song1.mp3").touch()
        (tmp_path / "song2.mp3").touch()
        (tmp_path / "not_audio.txt").touch()

        result = find_audio_files(tmp_path)

        assert len(result) == 2
        assert any("song1.mp3" in path for path in result)
        assert any("song2.mp3" in path for path in result)
        assert all("not_audio.txt" not in path for path in result)

    def test_find_audio_files_with_multiple_formats(self, tmp_path):
        """Test find_audio_files finds multiple audio formats."""
        # Create test files with different audio extensions
        (tmp_path / "song1.mp3").touch()
        (tmp_path / "song2.m4a").touch()
        (tmp_path / "song3.flac").touch()
        (tmp_path / "song4.wav").touch()

        result = find_audio_files(tmp_path)

        assert len(result) == 4
        assert any("song1.mp3" in path for path in result)
        assert any("song2.m4a" in path for path in result)
        assert any("song3.flac" in path for path in result)
        assert any("song4.wav" in path for path in result)

    def test_find_audio_files_case_insensitive(self, tmp_path):
        """Test find_audio_files is case insensitive for extensions."""
        # Create files with mixed case extensions
        (tmp_path / "song1.MP3").touch()
        (tmp_path / "song2.Mp3").touch()
        (tmp_path / "song3.M4A").touch()

        result = find_audio_files(tmp_path)

        assert len(result) == 3
        assert any("song1.MP3" in path for path in result)
        assert any("song2.Mp3" in path for path in result)
        assert any("song3.M4A" in path for path in result)

    def test_find_audio_files_recursive(self, tmp_path):
        """Test find_audio_files scans subdirectories recursively."""
        # Create nested directory structure
        subdir1 = tmp_path / "subdir1"
        subdir2 = subdir1 / "subdir2"
        subdir1.mkdir()
        subdir2.mkdir()

        (tmp_path / "root.mp3").touch()
        (subdir1 / "sub1.mp3").touch()
        (subdir2 / "sub2.mp3").touch()

        result = find_audio_files(tmp_path)

        assert len(result) == 3
        assert any("root.mp3" in path for path in result)
        assert any("sub1.mp3" in path for path in result)
        assert any("sub2.mp3" in path for path in result)

    def test_find_audio_files_respects_max_depth(self, tmp_path):
        """Test find_audio_files respects max_depth parameter."""
        # Create nested directory structure beyond max_depth
        # Note: scan_directory starts at depth 1, so max_depth=2 means root + 1 subdir level
        subdir1 = tmp_path / "subdir1"
        subdir2 = subdir1 / "subdir2"
        subdir3 = subdir2 / "subdir3"
        subdir1.mkdir()
        subdir2.mkdir()
        subdir3.mkdir()

        (tmp_path / "root.mp3").touch()
        (subdir1 / "depth1.mp3").touch()
        (subdir2 / "depth2.mp3").touch()
        (subdir3 / "depth3.mp3").touch()

        # Scan with max_depth=2 (scans root + 1 level deep)
        result = find_audio_files(tmp_path, max_depth=2)

        assert len(result) == 2
        assert any("root.mp3" in path for path in result)
        assert any("depth1.mp3" in path for path in result)
        assert not any("depth2.mp3" in path for path in result)
        assert not any("depth3.mp3" in path for path in result)

    def test_find_audio_files_max_depth_one(self, tmp_path):
        """Test find_audio_files with max_depth=1 only scans immediate files."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        (tmp_path / "root.mp3").touch()
        (subdir / "sub.mp3").touch()

        result = find_audio_files(tmp_path, max_depth=1)

        assert len(result) == 1
        assert any("root.mp3" in path for path in result)
        assert not any("sub.mp3" in path for path in result)

    def test_find_audio_files_sorted_order(self, tmp_path):
        """Test find_audio_files returns files in sorted order."""
        # Create files in non-alphabetical order
        (tmp_path / "z_song.mp3").touch()
        (tmp_path / "a_song.mp3").touch()
        (tmp_path / "m_song.mp3").touch()

        result = find_audio_files(tmp_path)

        # Extract filenames and check they're sorted
        filenames = [Path(path).name for path in result]
        assert filenames == sorted(filenames)

    def test_find_audio_files_ignores_symlinks(self, tmp_path):
        """Test find_audio_files doesn't follow symlinks."""
        # Create a real directory with a file
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        (real_dir / "song.mp3").touch()

        # Create a symlink to the directory
        symlink_dir = tmp_path / "symlink"
        try:
            symlink_dir.symlink_to(real_dir)
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks not supported on this platform")

        result = find_audio_files(tmp_path)

        # Should only find the file once (not through symlink)
        assert len(result) == 1
        assert any("song.mp3" in path for path in result)

    def test_find_audio_files_handles_permission_error(self, tmp_path):
        """Test find_audio_files handles permission errors gracefully."""
        # Create a subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "accessible.mp3").touch()
        (subdir / "inaccessible.mp3").touch()

        # Mock iterdir to raise PermissionError for subdir
        original_iterdir = Path.iterdir

        def mock_iterdir(self):
            if self == subdir:
                raise PermissionError("Permission denied")
            return original_iterdir(self)

        with patch.object(Path, 'iterdir', mock_iterdir):
            result = find_audio_files(tmp_path)

        # Should still find the accessible file
        assert len(result) >= 1
        assert any("accessible.mp3" in path for path in result)

    def test_find_audio_files_handles_oserror_on_file(self, tmp_path):
        """Test find_audio_files handles OSError on individual files gracefully."""
        (tmp_path / "good.mp3").touch()
        (tmp_path / "bad.mp3").touch()

        # Mock is_file to raise OSError for bad.mp3
        original_is_file = Path.is_file

        def mock_is_file(self):
            if self.name == "bad.mp3":
                raise OSError("Mock error")
            return original_is_file(self)

        with patch.object(Path, 'is_file', mock_is_file):
            result = find_audio_files(tmp_path)

        # Should still find the good file
        assert len(result) >= 1
        assert any("good.mp3" in path for path in result)

    def test_find_audio_files_with_string_path(self, tmp_path):
        """Test find_audio_files accepts string paths."""
        (tmp_path / "song.mp3").touch()

        result = find_audio_files(str(tmp_path))

        assert len(result) == 1
        assert any("song.mp3" in path for path in result)

    def test_find_audio_files_with_path_object(self, tmp_path):
        """Test find_audio_files accepts Path objects."""
        (tmp_path / "song.mp3").touch()

        result = find_audio_files(tmp_path)

        assert len(result) == 1
        assert any("song.mp3" in path for path in result)

    def test_find_audio_files_excludes_non_audio_extensions(self, tmp_path):
        """Test find_audio_files only returns audio files."""
        # Create various non-audio files
        (tmp_path / "document.txt").touch()
        (tmp_path / "image.jpg").touch()
        (tmp_path / "video.mp4").touch()
        (tmp_path / "script.py").touch()
        (tmp_path / "song.mp3").touch()

        result = find_audio_files(tmp_path)

        assert len(result) == 1
        assert any("song.mp3" in path for path in result)

    def test_find_audio_files_returns_absolute_paths(self, tmp_path):
        """Test find_audio_files returns absolute paths."""
        (tmp_path / "song.mp3").touch()

        result = find_audio_files(tmp_path)

        assert len(result) == 1
        assert Path(result[0]).is_absolute()
