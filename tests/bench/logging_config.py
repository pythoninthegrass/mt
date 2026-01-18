"""Centralized logging configuration for benchmark suite."""
import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_benchmark_logger(
    name: str, log_dir: Path = Path("/tmp/mt-bench/logs")
) -> logging.Logger:
    """Configure logger with both console and file output.

    Args:
        name: Logger name (e.g., "bench_scan", "make_synth_library")
        log_dir: Directory for log files (default: /tmp/mt-bench/logs)

    Returns:
        Configured logger instance
    """
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{name}_{timestamp}.log"

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)

    # File handler (DEBUG and above)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.info(f"Logging to: {log_file}")

    return logger
