"""Integration tests for native file system functionality."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.filesystem import FileSystemAPI, filesystem_api


class TestFileSystemAPI:
    """Test the FileSystemAPI class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api = FileSystemAPI()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test.mp3"
        self.test_file.write_text("fake mp3 content")

    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove test files
        if self.test_file.exists():
            self.test_file.unlink()
        if self.temp_dir.exists():
            self.temp_dir.rmdir()

    def test_api_initialization(self):
        """Test API initialization."""
        assert self.api._window is None
        assert isinstance(self.api, FileSystemAPI)

    def test_set_window(self):
        """Test setting the PyWebView window."""
        mock_window = Mock()
        self.api.set_window(mock_window)
        assert self.api._window == mock_window

    def test_validate_paths_valid_file(self):
        """Test validating a valid file path."""
        result = self.api.validate_paths([str(self.test_file)])

        assert result["valid"] == [str(self.test_file)]
        assert result["invalid"] == []
        assert result["files"] == [str(self.test_file)]
        assert result["directories"] == []

    def test_validate_paths_valid_directory(self):
        """Test validating a valid directory path."""
        result = self.api.validate_paths([str(self.temp_dir)])

        assert result["valid"] == [str(self.temp_dir)]
        assert result["invalid"] == []
        assert result["files"] == []
        assert result["directories"] == [str(self.temp_dir)]

    def test_validate_paths_invalid_path(self):
        """Test validating an invalid path."""
        invalid_path = str(self.temp_dir / "nonexistent.txt")
        result = self.api.validate_paths([invalid_path])

        assert result["valid"] == []
        assert len(result["invalid"]) == 1
        assert result["invalid"][0]["path"] == invalid_path
        assert "does not exist" in result["invalid"][0]["error"]

    def test_validate_paths_mixed(self):
        """Test validating a mix of valid and invalid paths."""
        invalid_path = str(self.temp_dir / "nonexistent.txt")
        result = self.api.validate_paths([str(self.test_file), invalid_path, str(self.temp_dir)])

        assert len(result["valid"]) == 2
        assert len(result["invalid"]) == 1
        assert str(self.test_file) in result["valid"]
        assert str(self.temp_dir) in result["valid"]
        assert invalid_path in result["invalid"]

    def test_security_path_traversal(self):
        """Test that path traversal attacks are blocked."""
        # Create a malicious path
        malicious_path = str(self.temp_dir / ".." / ".." / "etc" / "passwd")
        result = self.api.validate_paths([malicious_path])

        assert result["valid"] == []
        assert len(result["invalid"]) == 1
        assert "path traversal detected" in result["invalid"][0]["error"]

    def test_security_system_directories(self):
        """Test that system directories are blocked."""
        system_paths = ["/System/Library/Keychains", "/usr/bin", "/private/var"]
        result = self.api.validate_paths(system_paths)

        # All should be invalid due to security restrictions
        assert result["valid"] == []
        assert len(result["invalid"]) == len(system_paths)

        for invalid in result["invalid"]:
            assert "system directory" in invalid["error"]

    def test_security_hidden_files(self):
        """Test that hidden files are flagged."""
        hidden_file = self.temp_dir / ".hidden"
        hidden_file.write_text("hidden content")

        try:
            result = self.api.validate_paths([str(hidden_file)])
            # Hidden files should be blocked
            assert result["valid"] == []
            assert len(result["invalid"]) == 1
            assert "hidden file access" in result["invalid"][0]["error"]
        finally:
            if hidden_file.exists():
                hidden_file.unlink()

    def test_get_path_info_valid_file(self):
        """Test getting info for a valid file."""
        result = self.api.get_path_info(str(self.test_file))

        assert result is not None
        assert result["name"] == "test.mp3"
        assert result["is_file"] is True
        assert result["is_dir"] is False
        assert result["size"] == 17  # "fake mp3 content" length
        assert result["extension"] == ".mp3"
        assert result["stem"] == "test"

    def test_get_path_info_valid_directory(self):
        """Test getting info for a valid directory."""
        result = self.api.get_path_info(str(self.temp_dir))

        assert result is not None
        assert result["is_file"] is False
        assert result["is_dir"] is True
        assert "item_count" in result

    def test_get_path_info_invalid_path(self):
        """Test getting info for an invalid path."""
        result = self.api.get_path_info(str(self.temp_dir / "nonexistent"))
        assert result is None

    def test_list_directory_valid(self):
        """Test listing a valid directory."""
        # Create some test files
        (self.temp_dir / "file1.txt").write_text("content1")
        (self.temp_dir / "file2.txt").write_text("content2")
        subdir = self.temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        try:
            result = self.api.list_directory(str(self.temp_dir))

            assert result["success"] is True
            assert len(result["contents"]) == 3  # 2 files + 1 directory
            assert result["total_items"] == 3

            # Check that we have the expected items
            names = [item["name"] for item in result["contents"]]
            assert "file1.txt" in names
            assert "file2.txt" in names
            assert "subdir" in names

        finally:
            # Clean up
            (self.temp_dir / "file1.txt").unlink()
            (self.temp_dir / "file2.txt").unlink()
            (subdir / "file3.txt").unlink()
            subdir.rmdir()

    def test_list_directory_invalid(self):
        """Test listing an invalid directory."""
        result = self.api.list_directory(str(self.temp_dir / "nonexistent"))

        assert result["success"] is False
        assert "not a valid directory" in result["error"]
        assert result["contents"] == []

    def test_list_directory_recursive(self):
        """Test recursive directory listing."""
        # Create nested structure
        subdir = self.temp_dir / "subdir"
        subdir.mkdir()
        (self.temp_dir / "file1.txt").write_text("content1")
        (subdir / "file2.txt").write_text("content2")

        try:
            result = self.api.list_directory(str(self.temp_dir), recursive=True, max_depth=2)

            assert result["success"] is True
            # Should have file1.txt (depth 0), subdir (depth 0), file2.txt (depth 1)
            assert len(result["contents"]) == 3

            # Check depths
            depths = [item["depth"] for item in result["contents"]]
            assert 0 in depths
            assert 1 in depths

        finally:
            # Clean up
            (self.temp_dir / "file1.txt").unlink()
            (subdir / "file2.txt").unlink()
            subdir.rmdir()

    @patch('app.services.filesystem.webview')
    def test_open_file_dialog_no_window(self, mock_webview):
        """Test file dialog when no window is set."""
        result = self.api.open_file_dialog()
        assert result == []

    @patch('app.services.filesystem.webview')
    def test_open_directory_dialog_no_window(self, mock_webview):
        """Test directory dialog when no window is set."""
        result = self.api.open_directory_dialog()
        assert result is None

    @patch('app.services.filesystem.webview')
    def test_save_file_dialog_no_window(self, mock_webview):
        """Test save dialog when no window is set."""
        result = self.api.save_file_dialog()
        assert result is None


class TestFileSystemIntegration:
    """Integration tests for file system functionality."""

    def test_filesystem_api_global_instance(self):
        """Test that the global filesystem_api instance exists."""
        assert filesystem_api is not None
        assert isinstance(filesystem_api, FileSystemAPI)

    def test_security_comprehensive_check(self):
        """Test comprehensive security validation."""
        api = FileSystemAPI()

        # Test various malicious paths
        malicious_paths = [
            "/etc/passwd",
            "/System/Library/Keychains",
            "../../../etc/passwd",
            "~/.ssh/id_rsa",
            "/private/var/db",
            "/usr/bin/sudo",
        ]

        result = api.validate_paths(malicious_paths)

        # All should be blocked
        assert result["valid"] == []
        assert len(result["invalid"]) == len(malicious_paths)

        # Check that appropriate security errors are reported
        errors = [item["error"] for item in result["invalid"]]
        assert any("system directory" in error for error in errors) or any("path traversal" in error for error in errors)

    def test_safe_path_validation(self):
        """Test that safe paths are allowed."""
        api = FileSystemAPI()

        # Create a safe temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            safe_file = temp_path / "music.mp3"
            safe_file.write_text("music content")
            safe_dir = temp_path / "music_collection"
            safe_dir.mkdir()

            try:
                result = api.validate_paths([str(safe_file), str(safe_dir)])

                assert len(result["valid"]) == 2
                assert result["invalid"] == []
                assert str(safe_file) in result["files"]
                assert str(safe_dir) in result["directories"]

            finally:
                safe_file.unlink()
                safe_dir.rmdir()
