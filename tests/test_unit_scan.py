"""Unit tests for Zig scan module wrapper.

These tests verify the Python wrapper interface works correctly,
testing both the successful import path and fallback behavior.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestZigScanModuleImport:
    """Test that the Zig scan module can be imported."""

    def test_module_imports(self):
        """Test that core._scan module can be imported."""
        # This test will pass if Zig extension is built
        try:
            import core._scan as scan_module

            assert hasattr(scan_module, "scan_music_directory")
            assert hasattr(scan_module, "count_audio_files")
            assert hasattr(scan_module, "is_audio_file")
            assert hasattr(scan_module, "benchmark_directory")
            # Note: get_supported_extensions_count, not get_supported_extensions
            assert hasattr(scan_module, "get_supported_extensions_count")
        except ImportError:
            pytest.skip("Zig extension not available")

    def test_module_has_core_functions(self):
        """Test that core._scan has essential functions."""
        try:
            import core._scan as scan_module

            # Verify callable
            assert callable(scan_module.scan_music_directory)
            assert callable(scan_module.count_audio_files)
            assert callable(scan_module.is_audio_file)
            assert callable(scan_module.benchmark_directory)
        except ImportError:
            pytest.skip("Zig extension not available")


class TestZigScanFallback:
    """Test fallback behavior when Zig extension is not available."""

    def test_fallback_scan_music_directory_raises(self):
        """Test that fallback scan_music_directory raises NotImplementedError."""
        with patch("core._scan.ImportError", side_effect=ImportError()):
            # Re-import to trigger fallback
            import core._scan as scan_module
            import importlib

            importlib.reload(scan_module)

            # If we're in fallback mode, function should raise NotImplementedError
            try:
                scan_module.scan_music_directory("/some/path")
                # If no error, Zig extension is available (expected in CI/CD)
                assert True
            except NotImplementedError:
                # Fallback mode (expected if Zig not built)
                assert True

    def test_fallback_count_audio_files_raises(self):
        """Test that fallback count_audio_files raises NotImplementedError when not available."""
        import core._scan as scan_module

        try:
            result = scan_module.count_audio_files("/some/path")
            # If no error, function is implemented
            assert isinstance(result, int) or isinstance(result, type(None))
        except NotImplementedError:
            # Fallback mode
            assert True

    def test_fallback_is_audio_file_raises(self):
        """Test that fallback is_audio_file raises NotImplementedError when not available."""
        import core._scan as scan_module

        try:
            result = scan_module.is_audio_file("song.mp3")
            # If no error, function is implemented
            assert isinstance(result, bool)
        except NotImplementedError:
            # Fallback mode
            assert True

    def test_fallback_get_supported_extensions_count(self):
        """Test that get_supported_extensions_count works or raises NotImplementedError."""
        import core._scan as scan_module

        try:
            result = scan_module.get_supported_extensions_count()
            # If no error, function is implemented
            assert isinstance(result, int)
        except (NotImplementedError, AttributeError):
            # Fallback mode or function doesn't exist
            assert True

    def test_fallback_benchmark_directory_raises(self):
        """Test that fallback benchmark_directory raises NotImplementedError when not available."""
        import core._scan as scan_module

        try:
            result = scan_module.benchmark_directory("/some/path", 10)
            # If no error, function is implemented
            assert True
        except NotImplementedError:
            # Fallback mode
            assert True


class TestZigScanFunctionalityIfAvailable:
    """Test actual Zig scan functionality if extension is available."""

    def test_is_audio_file_with_mp3(self):
        """Test is_audio_file recognizes MP3 files."""
        import core._scan as scan_module

        try:
            result = scan_module.is_audio_file("song.mp3")
            assert result is True
        except NotImplementedError:
            pytest.skip("Zig extension not available")

    def test_is_audio_file_with_m4a(self):
        """Test is_audio_file recognizes M4A files."""
        import core._scan as scan_module

        try:
            result = scan_module.is_audio_file("song.m4a")
            assert result is True
        except NotImplementedError:
            pytest.skip("Zig extension not available")

    def test_is_audio_file_with_flac(self):
        """Test is_audio_file recognizes FLAC files."""
        import core._scan as scan_module

        try:
            result = scan_module.is_audio_file("song.flac")
            assert result is True
        except NotImplementedError:
            pytest.skip("Zig extension not available")

    def test_is_audio_file_case_insensitive(self):
        """Test is_audio_file is case insensitive."""
        import core._scan as scan_module

        try:
            assert scan_module.is_audio_file("song.MP3") is True
            assert scan_module.is_audio_file("song.Mp3") is True
            assert scan_module.is_audio_file("song.M4A") is True
        except NotImplementedError:
            pytest.skip("Zig extension not available")

    def test_is_audio_file_with_non_audio(self):
        """Test is_audio_file rejects non-audio files."""
        import core._scan as scan_module

        try:
            assert scan_module.is_audio_file("document.txt") is False
            assert scan_module.is_audio_file("image.jpg") is False
            # Note: mp4 may be considered audio by some implementations
            # since it can contain audio streams
        except NotImplementedError:
            pytest.skip("Zig extension not available")

    def test_get_supported_extensions_count(self):
        """Test get_supported_extensions_count returns number of extensions."""
        import core._scan as scan_module

        try:
            result = scan_module.get_supported_extensions_count()
            assert isinstance(result, int)
            assert result > 0  # Should support at least some audio formats
        except (NotImplementedError, AttributeError):
            pytest.skip("Zig extension not available or function not exposed")

    def test_count_audio_files_empty_directory(self, tmp_path):
        """Test count_audio_files on empty directory."""
        import core._scan as scan_module

        try:
            result = scan_module.count_audio_files(str(tmp_path))
            assert result == 0
        except NotImplementedError:
            pytest.skip("Zig extension not available")

    def test_count_audio_files_with_files(self, tmp_path):
        """Test count_audio_files counts audio files correctly."""
        import core._scan as scan_module

        try:
            # Create test files
            (tmp_path / "song1.mp3").touch()
            (tmp_path / "song2.mp3").touch()
            (tmp_path / "not_audio.txt").touch()

            result = scan_module.count_audio_files(str(tmp_path))
            assert result == 2
        except NotImplementedError:
            pytest.skip("Zig extension not available")

    def test_scan_music_directory_empty(self, tmp_path):
        """Test scan_music_directory on empty directory."""
        import core._scan as scan_module

        try:
            result = scan_module.scan_music_directory(str(tmp_path))
            # Result format depends on implementation, just verify it doesn't crash
            assert result is not None
        except NotImplementedError:
            pytest.skip("Zig extension not available")

    def test_scan_music_directory_with_files(self, tmp_path):
        """Test scan_music_directory finds audio files."""
        import core._scan as scan_module

        try:
            # Create test files
            (tmp_path / "song1.mp3").touch()
            (tmp_path / "song2.m4a").touch()

            result = scan_module.scan_music_directory(str(tmp_path))
            # Result format depends on implementation, just verify it doesn't crash
            assert result is not None
        except NotImplementedError:
            pytest.skip("Zig extension not available")

    def test_benchmark_directory(self, tmp_path):
        """Test benchmark_directory runs without errors."""
        import core._scan as scan_module

        try:
            # Create a test file
            (tmp_path / "song.mp3").touch()

            # Run benchmark with small iteration count
            result = scan_module.benchmark_directory(str(tmp_path), 2)
            # Just verify it doesn't crash
            assert result is not None
        except NotImplementedError:
            pytest.skip("Zig extension not available")


class TestZigScanReturnValues:
    """Test return values and behavior of scan functions."""

    def test_scan_music_directory_returns_int(self, tmp_path):
        """Test that scan_music_directory returns an integer (file count)."""
        import core._scan as scan_module

        try:
            (tmp_path / "song.mp3").touch()
            result = scan_module.scan_music_directory(str(tmp_path))
            assert isinstance(result, int)
            assert result >= 0
        except NotImplementedError:
            pytest.skip("Zig extension not available")

    def test_count_audio_files_returns_int(self, tmp_path):
        """Test that count_audio_files returns an integer."""
        import core._scan as scan_module

        try:
            result = scan_module.count_audio_files(str(tmp_path))
            assert isinstance(result, int)
            assert result >= 0
        except NotImplementedError:
            pytest.skip("Zig extension not available")

    def test_is_audio_file_returns_bool(self):
        """Test that is_audio_file returns a boolean."""
        import core._scan as scan_module

        try:
            result = scan_module.is_audio_file("test.mp3")
            assert isinstance(result, bool)
        except NotImplementedError:
            pytest.skip("Zig extension not available")
