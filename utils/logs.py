#!/usr/bin/env python

import logging
import os
import sys
from typing import Optional


def setup_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Set up and configure a logger instance.

    Creates a logger with the specified name and configures it with
    appropriate handlers and formatters.

    Args:
        name: The name for the logger
        log_level: The logging level (default: logging.INFO)

    Returns:
        logging.Logger: The configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Avoid adding handlers if they already exist
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)

    return logger


# Create application-wide logger
player_logger = setup_logger('mt.player')
app_logger = setup_logger('mt.app')


def get_player_logger() -> logging.Logger:
    """
    Get the player-specific logger.

    Returns:
        logging.Logger: The player logger instance
    """
    return player_logger


def get_app_logger() -> logging.Logger:
    """
    Get the application-wide logger.

    Returns:
        logging.Logger: The application logger instance
    """
    return app_logger
