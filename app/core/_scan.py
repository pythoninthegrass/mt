"""
Python interface to the Zig-based music scanning functionality.

This module provides high-performance directory scanning for audio files
using a Zig extension compiled with Pydust.
"""

try:
    from core._scan import (
        FileInfo,
        ScanStats,
        benchmark_directory,
        count_audio_files,
        get_supported_extensions,
        is_audio_file,
        scan_music_directory,
    )
except ImportError:
    import warnings

    warnings.warn(
        "Zig scanning extension not available. Install with 'pip install -e .' or use Python fallback.",
        ImportWarning,
        stacklevel=2,
    )

    # Provide stub implementations
    def scan_music_directory(path: str):
        raise NotImplementedError("Zig extension not available")

    def count_audio_files(path: str) -> int:
        raise NotImplementedError("Zig extension not available")

    def is_audio_file(filename: str) -> bool:
        raise NotImplementedError("Zig extension not available")

    def get_supported_extensions():
        raise NotImplementedError("Zig extension not available")

    def benchmark_directory(path: str, iterations: int):
        raise NotImplementedError("Zig extension not available")

    class FileInfo:
        pass

    class ScanStats:
        pass


__all__ = [
    "scan_music_directory",
    "count_audio_files",
    "is_audio_file",
    "get_supported_extensions",
    "benchmark_directory",
    "FileInfo",
    "ScanStats",
]
