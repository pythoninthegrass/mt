"""Music file scanner service for the mt backend.

Scans directories and files for audio content, extracts metadata,
and adds tracks to the library.
"""

import os
from pathlib import Path
from typing import Any

# Supported audio extensions
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".flac", ".ogg", ".wav", ".aac", ".wma", ".opus"}


def is_audio_file(path: Path) -> bool:
    """Check if a file is a supported audio file."""
    return path.suffix.lower() in AUDIO_EXTENSIONS


def extract_metadata(filepath: str) -> dict[str, Any]:
    """Extract metadata from an audio file using mutagen.

    Args:
        filepath: Path to the audio file

    Returns:
        Dictionary with metadata fields
    """
    import mutagen
    import mutagen.id3
    import mutagen.mp4

    metadata: dict[str, Any] = {
        "title": None,
        "artist": None,
        "album": None,
        "album_artist": None,
        "track_number": None,
        "track_total": None,
        "date": None,
        "duration": None,
    }

    try:
        audio = mutagen.File(filepath)
        if audio is None:
            # Use filename as title if mutagen can't read the file
            metadata["title"] = Path(filepath).stem
            return metadata

        # Get duration
        try:
            metadata["duration"] = audio.info.length
        except Exception:
            pass

        # Handle different tag formats
        if hasattr(audio, "tags") and audio.tags:
            tags = audio.tags

            # MP3 (ID3)
            if isinstance(tags, mutagen.id3.ID3):
                metadata.update(
                    {
                        "title": str(tags.get("TIT2", [""])[0]) if "TIT2" in tags else None,
                        "artist": str(tags.get("TPE1", [""])[0]) if "TPE1" in tags else None,
                        "album": str(tags.get("TALB", [""])[0]) if "TALB" in tags else None,
                        "album_artist": str(tags.get("TPE2", [""])[0]) if "TPE2" in tags else None,
                        "track_number": str(tags.get("TRCK", [""])[0]) if "TRCK" in tags else None,
                        "date": str(tags.get("TDRC", [""])[0]) if "TDRC" in tags else None,
                    }
                )
            # MP4/M4A tags
            elif isinstance(tags, mutagen.mp4.MP4Tags):
                metadata.update(
                    {
                        "title": str(tags.get("\xa9nam", [""])[0]) if "\xa9nam" in tags else None,
                        "artist": str(tags.get("\xa9ART", [""])[0]) if "\xa9ART" in tags else None,
                        "album": str(tags.get("\xa9alb", [""])[0]) if "\xa9alb" in tags else None,
                        "album_artist": str(tags.get("aART", [""])[0]) if "aART" in tags else None,
                        "track_number": str(tags.get("trkn", [(0, 0)])[0][0]) if "trkn" in tags and tags["trkn"][0][0] else None,
                        "track_total": str(tags.get("trkn", [(0, 0)])[0][1]) if "trkn" in tags and tags["trkn"][0][1] else None,
                        "date": str(tags.get("\xa9day", [""])[0]) if "\xa9day" in tags else None,
                    }
                )
            # FLAC, OGG, etc.
            else:
                metadata.update(
                    {
                        "title": str(tags.get("title", [""])[0]) if "title" in tags else None,
                        "artist": str(tags.get("artist", [""])[0]) if "artist" in tags else None,
                        "album": str(tags.get("album", [""])[0]) if "album" in tags else None,
                        "album_artist": str(tags.get("albumartist", [""])[0]) if "albumartist" in tags else None,
                        "track_number": str(tags.get("tracknumber", [""])[0]) if "tracknumber" in tags else None,
                        "track_total": str(tags.get("tracktotal", [""])[0]) if "tracktotal" in tags else None,
                        "date": str(tags.get("date", [""])[0]) if "date" in tags else None,
                    }
                )

        # Use filename as title if no title found
        if not metadata["title"]:
            metadata["title"] = Path(filepath).stem

    except Exception as e:
        # On error, use filename as title
        metadata["title"] = Path(filepath).stem
        print(f"Error extracting metadata from {filepath}: {e}")

    return metadata


def scan_paths(paths: list[str], recursive: bool = True) -> list[dict[str, Any]]:
    """Scan paths for audio files and extract metadata.

    Args:
        paths: List of file or directory paths to scan
        recursive: Whether to scan directories recursively

    Returns:
        List of dictionaries with filepath and metadata
    """
    results: list[dict[str, Any]] = []
    seen_paths: set[str] = set()

    for path_str in paths:
        path = Path(path_str)

        if not path.exists():
            continue

        if path.is_file():
            # Single file
            if is_audio_file(path) and str(path) not in seen_paths:
                seen_paths.add(str(path))
                metadata = extract_metadata(str(path))
                results.append(
                    {
                        "filepath": str(path),
                        "metadata": metadata,
                    }
                )
        elif path.is_dir():
            # Directory - scan for audio files
            if recursive:
                for root, _, files in os.walk(path):
                    for filename in files:
                        filepath = Path(root) / filename
                        if is_audio_file(filepath) and str(filepath) not in seen_paths:
                            seen_paths.add(str(filepath))
                            metadata = extract_metadata(str(filepath))
                            results.append(
                                {
                                    "filepath": str(filepath),
                                    "metadata": metadata,
                                }
                            )
            else:
                for filepath in path.iterdir():
                    if filepath.is_file() and is_audio_file(filepath) and str(filepath) not in seen_paths:
                        seen_paths.add(str(filepath))
                        metadata = extract_metadata(str(filepath))
                        results.append(
                            {
                                "filepath": str(filepath),
                                "metadata": metadata,
                            }
                        )

    return results


def get_file_size(filepath: str) -> int:
    """Get file size in bytes."""
    try:
        return os.path.getsize(filepath)
    except Exception:
        return 0
