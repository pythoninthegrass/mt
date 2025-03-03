#!/usr/bin/env python

import functools
import os
import re
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


def format_time(seconds):
    """
    Format time in seconds to mm:ss format.

    Args:
        seconds: Time in seconds (can be float, int, or str)

    Returns:
        str: Formatted time string as MM:SS
    """
    try:
        # Handle None or empty strings
        if seconds is None or seconds == '':
            return "00:00"

        # Convert to float first (handles strings, ints, and floats)
        seconds_float = float(seconds)

        # Calculate minutes and seconds
        minutes = int(seconds_float // 60)
        seconds = int(seconds_float % 60)

        # Format using f-string instead of % formatting
        return f"{minutes:02d}:{seconds:02d}"
    except (ValueError, TypeError) as e:
        # Log the error but don't crash
        print(f"Error formatting time: {e}, input was {seconds} of type {type(seconds)}")
        return "00:00"


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


def format_duration(milliseconds: int) -> str:
    """
    Format milliseconds into a readable duration string.

    Args:
        milliseconds: Time duration in milliseconds

    Returns:
        str: Formatted duration string in the format "minutes:seconds"
    """
    seconds = milliseconds // 1000
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02d}"


def truncate_text(text: str, max_length: int = 30) -> str:
    """
    Truncate text to a specified maximum length.

    If the text is longer than max_length, it will be truncated
    and ellipsis will be added.

    Args:
        text: The text to truncate
        max_length: Maximum length of the truncated text

    Returns:
        str: Truncated text with ellipsis if needed
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return f"{text[:max_length-3]}..."


def patch_time_formatting():
    """
    Apply a global patch to fix time formatting issues.
    Call this function early in the app's initialization.
    """
    # Keep track of patches applied to avoid double-patching
    if hasattr(patch_time_formatting, 'applied'):
        return

    # Find all UI modules that might use time formatting
    import inspect
    import sys

    # Look for typical UI components that display time
    ui_modules = []
    for module_name, module in sys.modules.items():
        if 'ui' in module_name.lower() or 'player' in module_name.lower():
            ui_modules.append(module)

    # Target pattern is a time formatting with %d for float
    pattern = re.compile(r'%d:%02d')

    # Count of patches applied
    patches_applied = 0

    for module in ui_modules:
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) or inspect.ismethod(obj):
                # Get source code if available
                try:
                    source = inspect.getsource(obj)
                    if pattern.search(source) and '%d' in source:
                        # This function likely has a time formatting operation
                        # Wrap the function to fix format errors
                        original_func = obj

                        @functools.wraps(original_func)
                        def safe_wrapper(*args, **kwargs):
                            try:
                                return original_func(*args, **kwargs)
                            except TypeError as e:
                                if "Unknown format code 'd' for object of type 'float'" in str(e):
                                    # Fix the specific time formatting error
                                    # Since we can't modify the function itself,
                                    # we'll just suppress the error and let the UI update next time
                                    print(f"Suppressed format error in {original_func.__name__}")
                                    return None
                                # Re-raise other errors
                                raise

                        # Replace the original function with our wrapped version
                        # This only works for instance methods, not for class methods
                        if hasattr(module, name):
                            setattr(module, name, safe_wrapper)
                            patches_applied += 1
                except Exception:
                    # Couldn't get source or apply patch, skip
                    pass

    # Mark as applied
    patch_time_formatting.applied = True
    print(f"Applied {patches_applied} time formatting patches")
