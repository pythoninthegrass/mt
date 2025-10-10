import mutagen
import os
from core.db import MusicDatabase
from core.logging import library_logger, log_error, log_file_operation
from pathlib import Path
from typing import Any
from utils.files import find_audio_files, normalize_path


class LibraryManager:
    def __init__(self, db: MusicDatabase):
        self.db = db

    def get_library_items(self) -> list[tuple]:
        """Get all items in the library with their metadata."""
        return self.db.get_library_items()

    def get_existing_files(self) -> set[str]:
        """Get set of all files currently in library."""
        return self.db.get_existing_files()

    def add_files_to_library(self, paths: list[str | Path]) -> None:
        """Add files to the library with metadata."""
        try:
            from core.logging import library_logger, log_file_operation

            log_file_operation("scan", "multiple_paths", path_count=len(paths))
            from eliot import log_message

            log_message(message_type="library_scan_start", path_count=len(paths), message="Starting library scan for new files")
        except ImportError:
            print("\nProcessing paths for library addition:")

        existing_files = self.get_existing_files()
        files_to_add = []  # Use a list to maintain order

        for path in paths:
            if path is None:
                continue

            try:
                normalized_path = normalize_path(path)
                path_str = str(normalized_path)
                try:
                    from core.logging import library_logger
                    from eliot import log_message

                    log_message(message_type="path_check", path=path_str, exists=normalized_path.exists())
                except ImportError:
                    print(f"\nChecking path: {path_str}")

                if normalized_path.exists():
                    if normalized_path.is_dir():
                        try:
                            from core.logging import library_logger
                            from eliot import log_message

                            log_message(
                                message_type="directory_scan", path=path_str, message="Scanning directory for audio files"
                            )
                        except ImportError:
                            print("Found directory, scanning for audio files...")
                        dir_files = find_audio_files(normalized_path)
                        for file_path in dir_files:
                            if file_path not in existing_files:
                                try:
                                    from core.logging import library_logger
                                    from eliot import log_message

                                    log_message(message_type="new_file_found", filepath=file_path, source="directory_scan")
                                except ImportError:
                                    print(f"Found new audio file: {file_path}")
                                files_to_add.append(file_path)
                    elif normalized_path.is_file() and path_str not in existing_files:
                        try:
                            from core.logging import library_logger
                            from eliot import log_message

                            log_message(message_type="new_file_found", filepath=path_str, source="direct_file")
                        except ImportError:
                            print(f"Found new audio file: {path_str}")
                        files_to_add.append(path_str)
            except (OSError, PermissionError) as e:
                try:
                    from core.logging import log_error

                    log_error(library_logger, e, path=str(path))
                except ImportError:
                    print(f"Error accessing path {path}: {e}")
                continue

        if files_to_add:
            try:
                from core.logging import library_logger
                from eliot import log_message

                log_message(
                    message_type="processing_start",
                    file_count=len(files_to_add),
                    message=f"Processing {len(files_to_add)} new files",
                )
            except ImportError:
                print(f"\nProcessing {len(files_to_add)} new files...")
            for file_path in files_to_add:
                self._process_audio_file(file_path)

    def find_file_by_metadata(self, title: str, artist: str = None, album: str = None, track_num: str = None) -> str | None:
        """Find a file in the library based on its metadata."""
        return self.db.find_file_by_metadata(title, artist, album, track_num)

    def search_library(self, search_text):
        """Search library items by text across artist, title, and album."""
        return self.db.search_library(search_text)

    def get_library_statistics(self) -> dict[str, Any]:
        """Get comprehensive library statistics including file count, size, and total duration."""
        return self.db.get_library_statistics()

    def get_top_25_most_played(self) -> list[tuple]:
        """Get top 25 most played tracks with their metadata."""
        return self.db.get_top_25_most_played()

    def delete_from_library(self, filepath: str) -> bool:
        """Delete a track from the library.
        
        Args:
            filepath: The absolute path to the file to remove from library
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        return self.db.delete_from_library(filepath)

    def _process_audio_file(self, file_path: str) -> None:
        """Process a single audio file and add it to the library."""
        path_obj = Path(file_path)
        if not path_obj.exists():
            return

        try:
            print(f"\nReading metadata for: {file_path}")
            audio = mutagen.File(file_path)
            if audio is not None:
                metadata = self._extract_metadata(audio)

                # If title is not found, use filename without extension
                if not metadata['title']:
                    metadata['title'] = path_obj.stem
                    print(f"No title found, using filename: {metadata['title']}")

                # Check for duplicates before adding
                if not self.db.is_duplicate(metadata, str(file_path)):
                    # Add to library with metadata
                    self.db.add_to_library(str(file_path), metadata)
                    print("Successfully added to library")
                else:
                    print("Skipping duplicate track")
        except Exception as e:
            print(f"Error reading metadata for {file_path}: {e}")
            # Add file without metadata if there's an error and it's not a duplicate
            basic_metadata = {'title': path_obj.stem}
            if not self.db.is_duplicate(basic_metadata, str(file_path)):
                self.db.add_to_library(str(file_path), basic_metadata)
                print("Added to library with filename only")
            else:
                print("Skipping duplicate track")

    def _extract_metadata(self, audio: mutagen.FileType) -> dict[str, Any]:
        """Extract metadata from an audio file."""
        metadata = {
            'title': None,
            'artist': None,
            'album': None,
            'album_artist': None,
            'track_number': None,
            'track_total': None,
            'date': None,
            'duration': None,
        }

        # Try to get duration
        try:
            metadata['duration'] = audio.info.length
        except Exception as e:
            print(f"Error getting duration: {e}")

        # Handle different tag formats
        if hasattr(audio, 'tags'):
            tags = audio.tags
            if tags:
                print("Found tags:", type(tags).__name__)
                # MP3 (ID3)
                if isinstance(tags, mutagen.id3.ID3):
                    metadata.update(
                        {
                            'title': str(tags.get('TIT2', [''])[0]) if 'TIT2' in tags else None,
                            'artist': str(tags.get('TPE1', [''])[0]) if 'TPE1' in tags else None,
                            'album': str(tags.get('TALB', [''])[0]) if 'TALB' in tags else None,
                            'album_artist': str(tags.get('TPE2', [''])[0]) if 'TPE2' in tags else None,
                            'track_number': str(tags.get('TRCK', [''])[0]) if 'TRCK' in tags else None,
                            'date': str(tags.get('TDRC', [''])[0]) if 'TDRC' in tags else None,
                        }
                    )
                # MP4/M4A tags
                elif hasattr(tags, '_DictMixin__dict'):  # MP4Tags
                    # MP4 tags use different keys
                    metadata.update(
                        {
                            'title': str(tags.get('\xa9nam', [''])[0]) if '\xa9nam' in tags else None,
                            'artist': str(tags.get('\xa9ART', [''])[0]) if '\xa9ART' in tags else None,
                            'album': str(tags.get('\xa9alb', [''])[0]) if '\xa9alb' in tags else None,
                            'album_artist': str(tags.get('aART', [''])[0]) if 'aART' in tags else None,
                            'track_number': str(tags.get('trkn', [(0, 0)])[0][0])
                            if 'trkn' in tags and tags['trkn'][0][0]
                            else None,
                            'track_total': str(tags.get('trkn', [(0, 0)])[0][1])
                            if 'trkn' in tags and tags['trkn'][0][1]
                            else None,
                            'date': str(tags.get('\xa9day', [''])[0]) if '\xa9day' in tags else None,
                        }
                    )
                # FLAC, OGG, etc.
                else:
                    metadata.update(
                        {
                            'title': str(tags.get('title', [''])[0]) if 'title' in tags else None,
                            'artist': str(tags.get('artist', [''])[0]) if 'artist' in tags else None,
                            'album': str(tags.get('album', [''])[0]) if 'album' in tags else None,
                            'album_artist': str(tags.get('albumartist', [''])[0]) if 'albumartist' in tags else None,
                            'track_number': str(tags.get('tracknumber', [''])[0]) if 'tracknumber' in tags else None,
                            'track_total': str(tags.get('tracktotal', [''])[0]) if 'tracktotal' in tags else None,
                            'date': str(tags.get('date', [''])[0]) if 'date' in tags else None,
                        }
                    )

        return metadata
