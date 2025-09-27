"""
Template filters for HTMX base templates.
These would typically be registered with your template engine (Jinja2, etc.)
"""


def format_duration(seconds):
    """
    Format duration in seconds to MM:SS format
    """
    if not seconds or seconds == 0:
        return "0:00"

    try:
        seconds = int(seconds)
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"
    except (ValueError, TypeError):
        return "0:00"


def format_file_size(bytes_size):
    """
    Format file size in bytes to human readable format
    """
    if not bytes_size:
        return "0 B"

    try:
        bytes_size = int(bytes_size)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return ".1f"
            bytes_size /= 1024.0
        return ".1f"
    except (ValueError, TypeError):
        return "0 B"


def pluralize(count, singular, plural=None):
    """
    Return singular or plural form based on count
    """
    if plural is None:
        plural = singular + 's'

    try:
        count = int(count)
        return singular if count == 1 else plural
    except (ValueError, TypeError):
        return plural


# Example usage in templates:
# {{ track.duration|format_duration }}
# {{ file.size|format_file_size }}
# {{ count|pluralize('track', 'tracks') }}
