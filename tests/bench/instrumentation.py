"""Performance measurement and instrumentation for benchmarking."""
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class PhaseMetrics:
    """Metrics for a single benchmark phase."""

    name: str
    wall_time: float = 0.0  # seconds
    cpu_time: float = 0.0  # seconds
    file_count: int = 0
    files_added: int = 0
    files_changed: int = 0
    files_deleted: int = 0
    throughput_files_sec: float = 0.0
    throughput_mb_sec: float = 0.0
    memory_peak_mb: float = 0.0
    db_size_bytes: int = 0
    errors: list[str] = field(default_factory=list)

    def calculate_throughput(self) -> None:
        """Calculate throughput based on wall time and file count."""
        if self.wall_time > 0:
            self.throughput_files_sec = self.file_count / self.wall_time
        else:
            self.throughput_files_sec = 0.0

    def to_dict(self) -> dict:
        """Convert metrics to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "wall_time_sec": self.wall_time,
            "cpu_time_sec": self.cpu_time,
            "file_count": self.file_count,
            "files_added": self.files_added,
            "files_changed": self.files_changed,
            "files_deleted": self.files_deleted,
            "throughput_files_sec": self.throughput_files_sec,
            "throughput_mb_sec": self.throughput_mb_sec,
            "memory_peak_mb": self.memory_peak_mb,
            "db_size_bytes": self.db_size_bytes,
            "error_count": len(self.errors),
        }


@contextmanager
def measure_phase(phase_name: str) -> Generator[PhaseMetrics, None, None]:
    """Context manager to measure phase execution.

    Args:
        phase_name: Name of the phase being measured

    Yields:
        PhaseMetrics: Metrics object that gets populated during execution

    Example:
        with measure_phase("walk_stat") as metrics:
            file_count = count_audio_files(music_dir)
            metrics.file_count = file_count
    """
    # Get process handle if psutil available
    process = None
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
        except Exception:
            process = None

    # Start timing
    start_wall = time.perf_counter()
    start_cpu = time.process_time()
    mem_before = process.memory_info().rss if process else 0

    # Create metrics object
    metrics = PhaseMetrics(name=phase_name)

    try:
        yield metrics
    finally:
        # End timing
        metrics.wall_time = time.perf_counter() - start_wall
        metrics.cpu_time = time.process_time() - start_cpu

        # Memory measurement
        if process:
            try:
                mem_after = process.memory_info().rss
                metrics.memory_peak_mb = (mem_after - mem_before) / (1024 * 1024)
            except Exception:
                metrics.memory_peak_mb = 0.0

        # Calculate throughput
        metrics.calculate_throughput()


def format_time(seconds: float) -> str:
    """Format seconds into human-readable time string.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted string like "2m 34s" or "5.234s"
    """
    if seconds >= 60:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"
    else:
        return f"{seconds:.3f}s"


def format_throughput(files_per_sec: float) -> str:
    """Format throughput into human-readable string.

    Args:
        files_per_sec: Files processed per second

    Returns:
        Formatted string like "1,234 files/sec"
    """
    return f"{files_per_sec:,.0f} files/sec"


def format_size(bytes_count: int) -> str:
    """Format byte count into human-readable size.

    Args:
        bytes_count: Size in bytes

    Returns:
        Formatted string like "1.5 MB" or "234 KB"
    """
    if bytes_count >= 1024 * 1024 * 1024:
        return f"{bytes_count / (1024 * 1024 * 1024):.2f} GB"
    elif bytes_count >= 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.2f} MB"
    elif bytes_count >= 1024:
        return f"{bytes_count / 1024:.2f} KB"
    else:
        return f"{bytes_count} bytes"
