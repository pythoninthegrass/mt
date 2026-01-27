"""
Logging configuration for MT music player using eliot.

This module provides structured logging throughout the application using eliot,
which provides context-aware logging with support for distributed tracing
and structured data.
"""

import eliot
import json
import logging
import os
import sys
from eliot import log_call, start_action, to_file, write_traceback
from eliot.stdlib import EliotHandler
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """
    Set up eliot logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to (always logs to stdout as well)
    """
    # Create a custom destination that outputs human-readable logs
    class HumanReadableDestination:
        """Destination that formats logs in a human-readable format."""

        def __init__(self, file):
            self.file = file

        def __call__(self, message):
            """Format and write log message."""
            # Skip internal Eliot messages (action start/status messages)
            if message.get("action_type") and not message.get("message_type"):
                return
            if message.get("action_status") in ("started", "succeeded", "failed") and not message.get("message_type"):
                return

            # Extract key information
            msg_type = message.get("message_type", "")
            action = message.get("action", msg_type)
            description = message.get("description", "")
            trigger = message.get("trigger_source", "")

            # Skip certain noisy/duplicate message types
            skip_messages = {
                "playback_paused",  # Duplicate of play_pause_pressed
                "playback_started",  # Duplicate of Started playing
                "queue_operation",  # Too noisy, not useful
                "volume_change_success",  # Duplicate of Volume changed
                "play_selected",  # Covered by Started playing
            }
            if msg_type in skip_messages:
                return

            # Format based on message type
            if "player_action" in msg_type:
                # Player action logs
                track = message.get("track", message.get("current_track", ""))
                old_state = message.get("old_state", "")
                new_state = message.get("new_state", "")

                # Require trigger_source for player actions
                if not trigger:
                    return

                if track and old_state and new_state:
                    output = f"[{trigger.upper()}] {action}: {track} ({old_state} → {new_state})"
                elif track:
                    output = f"[{trigger.upper()}] {action}: {track}"
                elif description:
                    output = f"[{trigger.upper()}] {description}"
                else:
                    output = f"[{trigger.upper()}] {action}"

            elif "api_request" in msg_type:
                # API request logs
                output = f"[API] {action}"
                if description:
                    output += f": {description}"

            elif msg_type == "application_ready":
                # Add newline after application startup completes
                output = message.get("message", description)
                if output and output.strip():
                    self.file.write(output + "\n\n")  # Extra newline
                    self.file.flush()
                return

            elif description:
                # Generic message with description
                output = description
            elif "message" in message:
                # Generic message
                output = message["message"]
            else:
                # Skip messages without useful content
                return

            # Write to file only if there's actual content
            if output and output.strip():
                self.file.write(output + "\n")
                self.file.flush()

    # Use human-readable output for stdout
    eliot.add_destination(HumanReadableDestination(sys.stdout))

    # Also log to file if specified (raw JSON format for machine parsing)
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        eliot.to_file(open(log_file, "a"))

    # Set up Python logging to work with eliot
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Add eliot handler to root logger
    handler = EliotHandler()
    logger.addHandler(handler)

    # Log the logging setup
    from eliot import log_message

    log_message(
        message_type="logging_setup", log_level=log_level, log_file=log_file or "stdout", message="Eliot logging configured"
    )


def get_logger(name: str):
    """
    Get an eliot logger instance for a specific module.

    Note: This returns an eliot Logger object that can be used with start_action()
    for creating action contexts. It does NOT have a .log() method for logging messages.
    Use eliot.log_message() directly for logging messages.

    Args:
        name: Module or component name

    Returns:
        Eliot Logger instance for use with start_action()
    """
    from eliot import Logger

    return Logger()


# Global logger instances for different components
app_logger = get_logger("mt_app")
player_logger = get_logger("mt_player")
db_logger = get_logger("mt_database")
library_logger = get_logger("mt_library")
queue_logger = get_logger("mt_queue")
controls_logger = get_logger("mt_controls")
api_logger = get_logger("mt_api")


def log_function_call(logger: eliot.Logger, action_type: str):
    """
    Decorator to log function calls with eliot.

    Args:
        logger: Eliot logger instance
        action_type: Type of action being performed

    Returns:
        Decorated function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            with start_action(logger, action_type, function=func.__name__):
                try:
                    result = func(*args, **kwargs)
                    from eliot import log_message

                    log_message(
                        message_type=f"{action_type}_success",
                        function=func.__name__,
                        result_type=type(result).__name__ if result is not None else None,
                    )
                    return result
                except Exception as e:
                    write_traceback(logger, exc_info=sys.exc_info())
                    from eliot import log_message

                    log_message(
                        message_type=f"{action_type}_error", function=func.__name__, error=str(e), error_type=type(e).__name__
                    )
                    raise

        return wrapper

    return decorator


def log_database_operation(operation: str, table: str = None, **context):
    """
    Log database operations with context.

    Args:
        operation: Type of database operation (SELECT, INSERT, UPDATE, DELETE)
        table: Database table name
        **context: Additional context data
    """
    from eliot import log_message

    log_message(message_type="database_operation", operation=operation, table=table, **context)


def log_player_action(action: str, **context):
    """
    Log player actions with context.

    Args:
        action: Player action (play, pause, next, previous, etc.)
        **context: Additional context data
    """
    from eliot import log_message

    log_message(message_type="player_action", action=action, **context)


def log_file_operation(operation: str, filepath: str, **context):
    """
    Log file operations with context.

    Args:
        operation: File operation type (read, write, scan, etc.)
        filepath: Path to the file
        **context: Additional context data
    """
    from eliot import log_message

    log_message(message_type="file_operation", operation=operation, filepath=filepath, **context)


def log_queue_operation(operation: str, **context):
    """
    Log queue operations with context.

    Args:
        operation: Queue operation (add, remove, reorder, etc.)
        **context: Additional context data
    """
    from eliot import log_message

    log_message(message_type="queue_operation", operation=operation, **context)


def log_error(logger: eliot.Logger, error: Exception, **context):
    """
    Log errors with full context and traceback.

    Args:
        logger: Eliot logger instance
        error: Exception that occurred
        **context: Additional context data
    """
    write_traceback(logger, exc_info=sys.exc_info())
    from eliot import log_message

    log_message(message_type="error_occurred", error_message=str(error), error_type=type(error).__name__, **context)


def log_performance(logger: eliot.Logger, operation: str, duration_ms: float, **context):
    """
    Log performance metrics.

    Args:
        logger: Eliot logger instance
        operation: Name of the operation
        duration_ms: Duration in milliseconds
        **context: Additional context data
    """
    from eliot import log_message

    log_message(message_type="performance_metric", operation=operation, duration_ms=duration_ms, **context)


def log_api_request(action: str, trigger_source: str = "api", **context):
    """
    Log API requests with context.

    Args:
        action: API action being performed
        trigger_source: Source of the request (default: "api")
        **context: Additional context data (request parameters, response, etc.)
    """
    from eliot import log_message

    log_message(message_type="api_request", action=action, trigger_source=trigger_source, **context)
