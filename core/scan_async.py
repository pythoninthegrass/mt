#!/usr/bin/env python3
"""Async wrapper for enhanced Zig scanning module with WebSocket support."""

import asyncio
import json
import time
from collections.abc import AsyncIterator, Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from fastapi import WebSocket
from pathlib import Path
from typing import Any, Optional


@dataclass
class ScanProgress:
    """Progress information for scanning operations."""

    total_files: int
    processed_files: int
    current_path: str
    percentage: float
    files_per_second: float
    estimated_time_remaining: float


@dataclass
class ScanStats:
    """Statistics from a completed scan."""

    total_files: int
    total_dirs: int
    total_size: int
    scan_duration_ms: float
    files_per_second: float


@dataclass
class FileMetadata:
    """Metadata for an audio file."""

    path: str
    filename: str
    size: int
    modified: float
    extension: str


class ZigScannerAsync:
    """Async wrapper for the enhanced Zig scanning module."""

    def __init__(self, max_workers: int = 4):
        """Initialize the async scanner.

        Args:
            max_workers: Maximum number of thread workers for parallel operations
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._websocket: WebSocket | None = None
        self._progress_callback: Callable | None = None
        self._scan_start_time: float = 0
        self._last_progress_update: float = 0
        self._progress_update_interval: float = 0.1  # Update every 100ms

        # Import the Zig module (always available)
        from core import _scan_enhanced as zig_scanner

        self.zig_scanner = zig_scanner

    async def scan_directory_async(
        self,
        root_path: str,
        max_depth: int = 10,
        follow_symlinks: bool = False,
        skip_hidden: bool = True,
        batch_size: int = 100,
        websocket: WebSocket | None = None,
        progress_callback: Callable | None = None,
    ) -> ScanStats:
        """Scan a directory asynchronously with progress updates.

        Args:
            root_path: Root directory to scan
            max_depth: Maximum recursion depth
            follow_symlinks: Whether to follow symbolic links
            skip_hidden: Whether to skip hidden files/directories
            batch_size: Number of files to process in each batch
            websocket: Optional WebSocket for real-time updates
            progress_callback: Optional callback for progress updates

        Returns:
            ScanStats with scan results
        """
        self._websocket = websocket
        self._progress_callback = progress_callback
        self._scan_start_time = time.time()

        # Use Zig scanner
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self._scan_with_zig_async,
            root_path,
            max_depth,
            follow_symlinks,
            skip_hidden,
            batch_size,
        )
        return ScanStats(**result)

    def _scan_with_zig_async(
        self,
        root_path: str,
        max_depth: int,
        follow_symlinks: bool,
        skip_hidden: bool,
        batch_size: int,
    ) -> dict:
        """Execute Zig scanner in thread pool."""
        return self.zig_scanner.scan_music_directory_async(
            root_path=root_path,
            max_depth=max_depth,
            follow_symlinks=follow_symlinks,
            skip_hidden=skip_hidden,
            batch_size=batch_size,
        )

    async def discover_files(
        self,
        root_path: str,
        return_list: bool = True,
    ) -> list[str] | int:
        """Fast file discovery without metadata extraction.

        Args:
            root_path: Root directory to scan
            return_list: If True, return list of paths; if False, return count

        Returns:
            List of file paths or count of files
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self.zig_scanner.discover_audio_files,
            root_path,
            return_list,
        )
        return result

    async def extract_metadata_batch(
        self,
        file_paths: list[str],
    ) -> list[FileMetadata]:
        """Extract metadata for a batch of files.

        Args:
            file_paths: List of file paths to process

        Returns:
            List of FileMetadata objects
        """
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            self.executor,
            self.zig_scanner.process_file_batch,
            file_paths,
        )
        return [FileMetadata(**r) for r in results]

    async def benchmark_performance(
        self,
        root_path: str,
        iterations: int = 3,
        warmup: bool = True,
    ) -> dict:
        """Benchmark scanning performance.

        Args:
            root_path: Directory to benchmark
            iterations: Number of iterations to run
            warmup: Whether to do a warmup run first

        Returns:
            Dictionary with benchmark results
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.zig_scanner.benchmark_scan_performance,
            root_path,
            iterations,
            warmup,
        )

    async def _send_progress_update(
        self,
        total_files: int,
        processed_files: int,
        current_path: str,
    ):
        """Send progress update via WebSocket or callback."""
        current_time = time.time()

        # Throttle updates
        if current_time - self._last_progress_update < self._progress_update_interval:
            return

        self._last_progress_update = current_time

        elapsed = current_time - self._scan_start_time
        files_per_second = processed_files / elapsed if elapsed > 0 else 0
        percentage = (processed_files / total_files * 100) if total_files > 0 else 0
        estimated_remaining = (total_files - processed_files) / files_per_second if files_per_second > 0 else 0

        progress = ScanProgress(
            total_files=total_files,
            processed_files=processed_files,
            current_path=current_path,
            percentage=percentage,
            files_per_second=files_per_second,
            estimated_time_remaining=estimated_remaining,
        )

        # Send via WebSocket if available
        if self._websocket:
            try:
                await self._websocket.send_json(
                    {
                        'type': 'scan_progress',
                        'data': asdict(progress),
                    }
                )
            except Exception as e:
                print(f"WebSocket send error: {e}")

        # Call progress callback if provided
        if self._progress_callback:
            await self._progress_callback(progress)

    def get_system_info(self) -> dict:
        """Get system information for performance tuning."""
        return self.zig_scanner.get_system_info()
