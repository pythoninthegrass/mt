#!/usr/bin/env python

import os
import traceback
from core.db import MusicDatabase
from typing import Optional

# Global database instance for the application
_db_instance = None


def get_db_instance() -> MusicDatabase | None:
    """
    Get the global database instance.

    This function provides access to the shared database instance
    throughout the application.

    Returns:
        MusicDatabase: The global database instance, or None if not initialized
    """
    global _db_instance
    return _db_instance


def set_db_instance(db: MusicDatabase) -> None:
    """
    Set the global database instance.

    This function sets the shared database instance for the application.

    Args:
        db: The database instance to set as the global instance
    """
    global _db_instance
    _db_instance = db


def format_time(seconds: int) -> str:
    """
    Format seconds into a readable time string.

    Args:
        seconds: Time in seconds

    Returns:
        str: Formatted time string in the format "minutes:seconds"
    """
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes}:{seconds:02d}"


def safe_path_join(*args) -> str:
    """
    Safely join path components.

    This function joins path components, handling edge cases like
    empty components or absolute paths.

    Args:
        *args: Path components to join

    Returns:
        str: The joined path
    """
    return os.path.join(*args)
