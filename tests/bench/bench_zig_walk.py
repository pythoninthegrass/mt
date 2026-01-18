#!/usr/bin/env python
"""Benchmark Zig walk performance ceiling (no metadata extraction)."""
import argparse
import sys
from pathlib import Path


def main():
    """Main entry point."""
    try:
        run_benchmark()
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrupted by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_benchmark():
    """Run Zig walk benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark Zig directory traversal performance"
    )
    parser.add_argument(
        "--library-root",
        type=Path,
        default=Path("/tmp/mt-bench/library"),
        help="Path to music library",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of benchmark iterations",
    )

    args = parser.parse_args()

    if not args.library_root.exists():
        print(f"Error: Library not found: {args.library_root}")
        sys.exit(1)

    try:
        from core._scan import benchmark_directory, count_audio_files
    except (ImportError, NotImplementedError):
        print("Error: Zig extension not available")
        print("The core._scan module is required for this benchmark")
        sys.exit(1)

    music_dir = str(args.library_root)

    # Run benchmark
    print(f"\n{'='*60}")
    print("Zig Walk Performance Ceiling")
    print(f"{'='*60}\n")
    print(f"Directory: {music_dir}")
    print(f"Iterations: {args.iterations}\n")

    # First get file count
    total_files = count_audio_files(music_dir)
    print(f"Total audio files: {total_files:,}\n")

    # Run benchmark iterations
    avg_time_ms = benchmark_directory(music_dir, args.iterations)
    avg_time_sec = avg_time_ms / 1000

    throughput = total_files / avg_time_sec if avg_time_sec > 0 else 0

    print("Results:")
    print(f"  Average time: {avg_time_sec:.3f}s")
    print(f"  Throughput:   {throughput:,.0f} files/sec")
    print(f"\n{'='*60}\n")

    # This represents the performance ceiling for filesystem traversal
    print("Note: This is the raw traversal ceiling without metadata parsing.")
    print("Actual scan times will be higher due to mutagen overhead.")


if __name__ == "__main__":
    main()
