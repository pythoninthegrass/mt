"""Benchmark fixtures for database isolation and safety guards."""
import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def isolated_database() -> Generator[tuple[object, Path], None, None]:
    """Create temporary benchmark database - never touches production.

    Yields:
        tuple: (MusicDatabase instance, database Path)

    Raises:
        ValueError: If trying to use production paths
    """
    from core.db import DB_TABLES, MusicDatabase

    bench_dir = Path("/tmp/mt-bench")
    bench_dir.mkdir(exist_ok=True, parents=True)

    db_path = bench_dir / "mt.db"

    # Safety check: ensure we're not touching production
    validate_paths(str(bench_dir), str(db_path))

    # Initialize database
    db = MusicDatabase(str(db_path), DB_TABLES)

    try:
        yield db, db_path
    finally:
        # Cleanup
        db.close()
        if db_path.exists():
            db_path.unlink()


def validate_paths(library_root: str, db_path: str) -> None:
    """Refuse to run against production paths.

    Args:
        library_root: Path to library directory
        db_path: Path to database file

    Raises:
        ValueError: If any production paths are detected
    """
    dangerous_patterns = [
        "Library/Application Support",
        "com.mt.desktop",
        "/Music/",
        "~/.mt/mt.db",
        os.path.expanduser("~/.mt"),
        os.path.expanduser("~/Music"),
    ]

    for pattern in dangerous_patterns:
        if pattern in library_root or pattern in db_path:
            raise ValueError(
                f"Production path detected: {pattern}\n"
                f"Library root: {library_root}\n"
                f"Database path: {db_path}\n"
                f"Benchmarks must use /tmp/mt-bench/ for safety."
            )

    # Additional check: database path must be in /tmp
    db_path_obj = Path(db_path)
    if not str(db_path_obj.resolve()).startswith("/tmp/"):
        raise ValueError(
            f"Database must be in /tmp/ directory for safety.\n"
            f"Got: {db_path}"
        )


def cleanup_benchmark_artifacts() -> None:
    """Remove all benchmark artifacts from /tmp/mt-bench."""
    import shutil

    bench_dir = Path("/tmp/mt-bench")
    if bench_dir.exists():
        shutil.rmtree(bench_dir)
