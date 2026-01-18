"""2-phase music file scanner for optimized library scanning.

Phase 1 (Inventory): Fast filesystem walk + stat + DB diff
Phase 2 (Parse Delta): Tag parsing only for changed files

This enables no-op rescans to complete in <10s without parsing any tags.
"""

import os
from backend.services.scanner import AUDIO_EXTENSIONS, extract_metadata
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ScanStats:
    """Statistics from a 2-phase scan operation."""

    visited: int = 0  # Total files visited
    added: int = 0  # New files added to library
    modified: int = 0  # Existing files with changed fingerprint
    unchanged: int = 0  # Existing files with unchanged fingerprint
    deleted: int = 0  # Files in DB but not on filesystem
    errors: int = 0  # Files that failed to process


def scan_library_2phase(
    paths: list[str],
    db_fingerprints: dict[str, tuple[int | None, int]],
    recursive: bool = True,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> tuple[dict[str, list[tuple[str, dict[str, Any]]]], ScanStats]:
    """Scan library using 2-phase approach for optimal performance.

    Phase 1: Inventory - Walk + stat filesystem, compare fingerprints with DB
    Phase 2: Parse - Extract metadata only for changed files (handled by caller)

    Args:
        paths: List of file or directory paths to scan
        db_fingerprints: Dict mapping filepath -> (file_mtime_ns, file_size) from DB
        recursive: Whether to scan directories recursively
        progress_callback: Optional callback(phase, current, total) for progress updates

    Returns:
        Tuple of (changes_dict, stats) where changes_dict contains:
            - "added": List of (filepath, empty_metadata) tuples for new files
            - "modified": List of (filepath, empty_metadata) tuples for changed files
            - "deleted": List of filepaths for removed files
            - "unchanged": List of filepaths that haven't changed
    """
    stats = ScanStats()
    changes: dict[str, list] = {
        "added": [],
        "modified": [],
        "deleted": [],
        "unchanged": [],
    }

    # Phase 1: Inventory - Walk filesystem and classify files
    filesystem_files: dict[str, tuple[int | None, int]] = {}

    for path_str in paths:
        path = Path(path_str)

        if not path.exists():
            continue

        if path.is_file():
            # Single file
            if _is_audio_file(path):
                try:
                    stat_result = os.stat(path)
                    fingerprint = (stat_result.st_mtime_ns, stat_result.st_size)
                    filesystem_files[str(path)] = fingerprint
                    stats.visited += 1
                except Exception:
                    stats.errors += 1

        elif path.is_dir():
            # Directory - scan for audio files
            if recursive:
                for root, _, files in os.walk(path):
                    for filename in files:
                        filepath = Path(root) / filename
                        if _is_audio_file(filepath):
                            try:
                                stat_result = os.stat(filepath)
                                fingerprint = (stat_result.st_mtime_ns, stat_result.st_size)
                                filesystem_files[str(filepath)] = fingerprint
                                stats.visited += 1

                                if progress_callback:
                                    progress_callback("inventory", stats.visited, 0)
                            except Exception:
                                stats.errors += 1
            else:
                for filepath in path.iterdir():
                    if filepath.is_file() and _is_audio_file(filepath):
                        try:
                            stat_result = os.stat(filepath)
                            fingerprint = (stat_result.st_mtime_ns, stat_result.st_size)
                            filesystem_files[str(filepath)] = fingerprint
                            stats.visited += 1
                        except Exception:
                            stats.errors += 1

    # Classify files by comparing fingerprints
    for filepath, fs_fingerprint in filesystem_files.items():
        if filepath not in db_fingerprints:
            # New file - not in DB
            changes["added"].append((filepath, {}))  # Empty metadata for now
            stats.added += 1
        else:
            db_fingerprint = db_fingerprints[filepath]
            if fs_fingerprint != db_fingerprint:
                # File exists but fingerprint changed
                changes["modified"].append((filepath, {}))  # Empty metadata for now
                stats.modified += 1
            else:
                # File exists with same fingerprint
                changes["unchanged"].append(filepath)
                stats.unchanged += 1

    # Find deleted files (in DB but not on filesystem)
    filesystem_set = set(filesystem_files.keys())
    for db_filepath in db_fingerprints:
        if db_filepath not in filesystem_set:
            changes["deleted"].append(db_filepath)
            stats.deleted += 1

    return changes, stats


def parse_changed_files(
    changed_files: list[tuple[str, dict[str, Any]]],
    progress_callback: Callable[[str, int, int], None] | None = None,
    parallel: bool = True,
    max_workers: int | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    """Parse metadata for changed files (Phase 2).

    Args:
        changed_files: List of (filepath, empty_metadata) tuples
        progress_callback: Optional callback(phase, current, total) for progress
        parallel: Whether to use parallel processing (default: True)
        max_workers: Max worker processes (default: CPU count)

    Returns:
        List of (filepath, metadata) tuples with extracted metadata
    """
    if not changed_files:
        return []

    # For small batches, serial processing is faster (avoid process overhead)
    if len(changed_files) < 20 or not parallel:
        return _parse_serial(changed_files, progress_callback)

    # Use parallel processing for larger batches
    return _parse_parallel(changed_files, progress_callback, max_workers)


def _parse_serial(
    changed_files: list[tuple[str, dict[str, Any]]],
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    """Parse metadata serially (for small batches)."""
    results = []
    total = len(changed_files)

    for idx, (filepath, _) in enumerate(changed_files):
        try:
            metadata = extract_metadata(filepath)
            results.append((filepath, metadata))

            if progress_callback:
                progress_callback("parse", idx + 1, total)
        except Exception as e:
            print(f"Error parsing metadata from {filepath}: {e}")
            # Still include with minimal metadata
            results.append((filepath, {"title": Path(filepath).stem, "file_size": 0}))

    return results


def _parse_parallel(
    changed_files: list[tuple[str, dict[str, Any]]],
    progress_callback: Callable[[str, int, int], None] | None = None,
    max_workers: int | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    """Parse metadata in parallel using multiprocessing."""
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor, as_completed

    if max_workers is None:
        max_workers = mp.cpu_count()

    filepaths = [fp for fp, _ in changed_files]
    results = []
    total = len(filepaths)
    completed = 0

    # Use ProcessPoolExecutor for parallel parsing
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_filepath = {executor.submit(_extract_metadata_worker, fp): fp for fp in filepaths}

        # Collect results as they complete
        for future in as_completed(future_to_filepath):
            filepath = future_to_filepath[future]
            try:
                metadata = future.result()
                results.append((filepath, metadata))
            except Exception as e:
                print(f"Error parsing metadata from {filepath}: {e}")
                # Still include with minimal metadata
                results.append((filepath, {"title": Path(filepath).stem, "file_size": 0}))

            completed += 1
            if progress_callback:
                progress_callback("parse", completed, total)

    return results


def _extract_metadata_worker(filepath: str) -> dict[str, Any]:
    """Worker function for parallel metadata extraction.

    This is a top-level function (required for multiprocessing).
    """
    try:
        return extract_metadata(filepath)
    except Exception as e:
        # Return minimal metadata on error
        return {
            "title": Path(filepath).stem,
            "file_size": 0,
            "file_mtime_ns": None,
            "error": str(e),
        }


def _is_audio_file(path: Path) -> bool:
    """Check if a file is a supported audio file."""
    return path.suffix.lower() in AUDIO_EXTENSIONS
