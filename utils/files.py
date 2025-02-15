import os
import sys
from config import AUDIO_EXTENSIONS, MAX_SCAN_DEPTH
from pathlib import Path


def normalize_path(path_str):
    if isinstance(path_str, Path):
        return path_str

    path_str = path_str.strip('{}').strip('"')

    if sys.platform == 'darwin' and '/Volumes/' in path_str:
        try:
            abs_path = os.path.abspath(path_str)
            real_path = os.path.realpath(abs_path)
            if os.path.exists(real_path):
                return Path(real_path)
        except (OSError, ValueError):
            pass

    return Path(path_str)

def find_audio_files(directory, max_depth=MAX_SCAN_DEPTH):
    found_files = []
    base_path = normalize_path(directory)

    def scan_directory(path, current_depth):
        if current_depth > max_depth:
            return

        try:
            # Get all items in directory and sort them
            items = sorted(path.iterdir())
            for item in items:
                try:
                    if item.is_file() and item.suffix.lower() in AUDIO_EXTENSIONS:
                        found_files.append(str(item))
                    elif item.is_dir() and not item.is_symlink():
                        scan_directory(item, current_depth + 1)
                except OSError:
                    continue
        except (PermissionError, OSError):
            pass

    scan_directory(base_path, 1)
    return found_files
