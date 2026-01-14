"""Artwork extraction service for the mt music player backend.

Extracts album artwork from audio files (embedded) and folder-based images.
"""

import base64
import os
from pathlib import Path
from typing import Any

ARTWORK_FILENAMES = [
    "cover.jpg",
    "cover.jpeg",
    "cover.png",
    "folder.jpg",
    "folder.jpeg",
    "folder.png",
    "album.jpg",
    "album.jpeg",
    "album.png",
    "front.jpg",
    "front.jpeg",
    "front.png",
    "artwork.jpg",
    "artwork.jpeg",
    "artwork.png",
]


def get_embedded_artwork(filepath: str) -> dict[str, Any] | None:
    """Extract embedded artwork from an audio file.

    Args:
        filepath: Path to the audio file

    Returns:
        Dictionary with 'data' (base64), 'mime_type', and 'source' or None
    """
    import mutagen
    import mutagen.flac
    import mutagen.id3
    import mutagen.mp4
    import mutagen.oggvorbis

    try:
        audio = mutagen.File(filepath)
        if audio is None:
            return None

        # MP3 (ID3) - APIC frame
        if hasattr(audio, "tags") and isinstance(audio.tags, mutagen.id3.ID3):
            for key in audio.tags:
                if key.startswith("APIC"):
                    apic = audio.tags[key]
                    return {
                        "data": base64.b64encode(apic.data).decode("utf-8"),
                        "mime_type": apic.mime,
                        "source": "embedded",
                    }

        # MP4/M4A - covr atom
        if isinstance(audio.tags, mutagen.mp4.MP4Tags):
            if "covr" in audio.tags:
                cover = audio.tags["covr"][0]
                mime_type = "image/jpeg" if cover.imageformat == mutagen.mp4.MP4Cover.FORMAT_JPEG else "image/png"
                return {
                    "data": base64.b64encode(bytes(cover)).decode("utf-8"),
                    "mime_type": mime_type,
                    "source": "embedded",
                }

        # FLAC - pictures
        if isinstance(audio, mutagen.flac.FLAC):
            if audio.pictures:
                pic = audio.pictures[0]
                return {
                    "data": base64.b64encode(pic.data).decode("utf-8"),
                    "mime_type": pic.mime,
                    "source": "embedded",
                }

        # OGG Vorbis - metadata_block_picture
        if isinstance(audio, mutagen.oggvorbis.OggVorbis):
            if "metadata_block_picture" in audio:
                import mutagen.flac

                pic_data = base64.b64decode(audio["metadata_block_picture"][0])
                pic = mutagen.flac.Picture(pic_data)
                return {
                    "data": base64.b64encode(pic.data).decode("utf-8"),
                    "mime_type": pic.mime,
                    "source": "embedded",
                }

    except Exception as e:
        print(f"Error extracting embedded artwork from {filepath}: {e}")

    return None


def get_folder_artwork(filepath: str) -> dict[str, Any] | None:
    """Find artwork file in the same folder as the audio file.

    Args:
        filepath: Path to the audio file

    Returns:
        Dictionary with 'data' (base64), 'mime_type', and 'source' or None
    """
    folder = Path(filepath).parent

    for filename in ARTWORK_FILENAMES:
        artwork_path = folder / filename
        if artwork_path.exists():
            try:
                with open(artwork_path, "rb") as f:
                    data = f.read()

                ext = artwork_path.suffix.lower()
                mime_type = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

                return {
                    "data": base64.b64encode(data).decode("utf-8"),
                    "mime_type": mime_type,
                    "source": "folder",
                    "filename": filename,
                }
            except Exception as e:
                print(f"Error reading folder artwork {artwork_path}: {e}")
                continue

    # Also check case-insensitive
    try:
        folder_files = {f.name.lower(): f for f in folder.iterdir() if f.is_file()}
        for filename in ARTWORK_FILENAMES:
            if filename.lower() in folder_files:
                artwork_path = folder_files[filename.lower()]
                try:
                    with open(artwork_path, "rb") as f:
                        data = f.read()

                    ext = artwork_path.suffix.lower()
                    mime_type = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

                    return {
                        "data": base64.b64encode(data).decode("utf-8"),
                        "mime_type": mime_type,
                        "source": "folder",
                        "filename": artwork_path.name,
                    }
                except Exception:
                    continue
    except Exception:
        pass

    return None


def get_artwork(filepath: str) -> dict[str, Any] | None:
    """Get artwork for an audio file, trying embedded first then folder-based.

    Args:
        filepath: Path to the audio file

    Returns:
        Dictionary with 'data' (base64), 'mime_type', and 'source' or None
    """
    # Try embedded artwork first
    artwork = get_embedded_artwork(filepath)
    if artwork:
        return artwork

    # Fall back to folder-based artwork
    return get_folder_artwork(filepath)
