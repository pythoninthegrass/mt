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
        
        # Import the Zig module
        try:
            from core import _scan_enhanced as zig_scanner
            self.zig_scanner = zig_scanner
        except ImportError as e:
            print(f"Warning: Enhanced Zig scanner not available: {e}")
            # Fall back to basic scanner if available
            try:
                from core import _scan as zig_scanner
                self.zig_scanner = zig_scanner
                print("Using basic Zig scanner as fallback")
            except ImportError:
                self.zig_scanner = None
                print("No Zig scanner available, using Python fallback")
    
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
        
        if self.zig_scanner and hasattr(self.zig_scanner, 'scan_music_directory_async'):
            # Use enhanced Zig scanner
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
        else:
            # Fallback to Python implementation
            return await self._scan_with_python_async(
                root_path,
                max_depth,
                follow_symlinks,
                skip_hidden,
                batch_size,
            )
    
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
    
    async def _scan_with_python_async(
        self,
        root_path: str,
        max_depth: int,
        follow_symlinks: bool,
        skip_hidden: bool,
        batch_size: int,
    ) -> ScanStats:
        """Python fallback implementation for scanning."""
        start_time = time.time()
        total_files = 0
        total_dirs = 0
        total_size = 0
        
        audio_extensions = {
            '.mp3', '.flac', '.m4a', '.ogg', '.wav',
            '.wma', '.aac', '.opus', '.m4p', '.mp4'
        }
        
        path = Path(root_path)
        if not path.exists():
            return ScanStats(0, 0, 0, 0, 0)
        
        # Use async generator for directory walking
        async for file_path in self._walk_directory_async(
            path,
            max_depth,
            follow_symlinks,
            skip_hidden,
            audio_extensions,
        ):
            total_files += 1
            try:
                total_size += file_path.stat().st_size
            except OSError:
                pass
            
            # Send progress update if needed
            if total_files % batch_size == 0:
                await self._send_progress_update(
                    total_files,
                    total_files,
                    str(file_path),
                )
        
        duration_ms = (time.time() - start_time) * 1000
        files_per_second = total_files / (duration_ms / 1000) if duration_ms > 0 else 0
        
        return ScanStats(
            total_files=total_files,
            total_dirs=total_dirs,
            total_size=total_size,
            scan_duration_ms=duration_ms,
            files_per_second=files_per_second,
        )
    
    async def _walk_directory_async(
        self,
        path: Path,
        max_depth: int,
        follow_symlinks: bool,
        skip_hidden: bool,
        audio_extensions: set,
        current_depth: int = 0,
    ) -> AsyncIterator[Path]:
        """Async generator for walking directories."""
        if current_depth >= max_depth:
            return
        
        try:
            for item in path.iterdir():
                if skip_hidden and item.name.startswith('.'):
                    continue
                
                if item.is_file():
                    if item.suffix.lower() in audio_extensions:
                        yield item
                elif item.is_dir() or (follow_symlinks and item.is_symlink()):
                    # Recursively walk subdirectories
                    async for subitem in self._walk_directory_async(
                        item,
                        max_depth,
                        follow_symlinks,
                        skip_hidden,
                        audio_extensions,
                        current_depth + 1,
                    ):
                        yield subitem
        except PermissionError:
            pass
    
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
        if self.zig_scanner and hasattr(self.zig_scanner, 'discover_audio_files'):
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self.zig_scanner.discover_audio_files,
                root_path,
                return_list,
            )
            return result
        else:
            # Python fallback
            audio_extensions = {
                '.mp3', '.flac', '.m4a', '.ogg', '.wav',
                '.wma', '.aac', '.opus', '.m4p', '.mp4'
            }
            
            path = Path(root_path)
            files = []
            
            async for file_path in self._walk_directory_async(
                path,
                max_depth=10,
                follow_symlinks=False,
                skip_hidden=True,
                audio_extensions=audio_extensions,
            ):
                if return_list:
                    files.append(str(file_path))
                else:
                    files.append(None)
            
            return files if return_list else len(files)
    
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
        if self.zig_scanner and hasattr(self.zig_scanner, 'process_file_batch'):
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor,
                self.zig_scanner.process_file_batch,
                file_paths,
            )
            return [FileMetadata(**r) for r in results]
        else:
            # Python fallback
            tasks = [
                self._extract_metadata_single(path)
                for path in file_paths
            ]
            return await asyncio.gather(*tasks)
    
    async def _extract_metadata_single(self, file_path: str) -> FileMetadata:
        """Extract metadata for a single file."""
        path = Path(file_path)
        try:
            stat = path.stat()
            return FileMetadata(
                path=str(path),
                filename=path.name,
                size=stat.st_size,
                modified=stat.st_mtime,
                extension=path.suffix,
            )
        except OSError:
            return FileMetadata(
                path=str(path),
                filename=path.name,
                size=0,
                modified=0,
                extension=path.suffix,
            )
    
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
        if self.zig_scanner and hasattr(self.zig_scanner, 'benchmark_scan_performance'):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                self.zig_scanner.benchmark_scan_performance,
                root_path,
                iterations,
                warmup,
            )
        else:
            # Python benchmark fallback
            timings = []
            
            if warmup:
                await self.discover_files(root_path, return_list=False)
            
            for _ in range(iterations):
                start_time = time.time()
                count = await self.discover_files(root_path, return_list=False)
                duration = (time.time() - start_time) * 1000
                timings.append(duration)
            
            avg_time = sum(timings) / len(timings)
            return {
                'iterations': iterations,
                'total_files': count,
                'avg_time_ms': avg_time,
                'min_time_ms': min(timings),
                'max_time_ms': max(timings),
                'files_per_second': count / (avg_time / 1000) if avg_time > 0 else 0,
                'timings': timings,
            }
    
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
        estimated_remaining = (
            (total_files - processed_files) / files_per_second
            if files_per_second > 0
            else 0
        )
        
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
                await self._websocket.send_json({
                    'type': 'scan_progress',
                    'data': asdict(progress),
                })
            except Exception as e:
                print(f"WebSocket send error: {e}")
        
        # Call progress callback if provided
        if self._progress_callback:
            await self._progress_callback(progress)
    
    def get_system_info(self) -> dict:
        """Get system information for performance tuning."""
        if self.zig_scanner and hasattr(self.zig_scanner, 'get_system_info'):
            return self.zig_scanner.get_system_info()
        else:
            import os
            return {
                'cpu_count': os.cpu_count() or 1,
                'page_size': 4096,  # Default page size
                'supported_extensions': 10,
            }