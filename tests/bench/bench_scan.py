#!/usr/bin/env python
"""Benchmark library scanning performance with different scenarios."""
import argparse
import csv
import random
import shutil
import sys
from datetime import datetime
from pathlib import Path
from tests.bench.fixtures import isolated_database, validate_paths
from tests.bench.instrumentation import measure_phase
from tests.bench.logging_config import setup_benchmark_logger
from tests.bench.reporters import HumanReporter, JSONReporter

# Setup logging
logger = setup_benchmark_logger("bench_scan")

# CSV results file path
CSV_RESULTS_FILE = Path("/tmp/mt-bench/benchmark_results.csv")


def append_to_csv(result: dict) -> None:
    """Append benchmark result to CSV file.

    Args:
        result: Benchmark result dictionary
    """
    csv_file = CSV_RESULTS_FILE
    csv_file.parent.mkdir(parents=True, exist_ok=True)

    # Check if file exists to determine if we need to write header
    file_exists = csv_file.exists()

    # Flatten the result for CSV
    row = {
        "timestamp": result["timestamp"],
        "scenario": result["scenario"],
        "total_files": result.get("total_files", 0),
        "total_time_sec": result["total_time_sec"],
        "throughput_files_sec": result.get("throughput_files_sec", 0),
        "pass": result.get("pass", ""),
        "target_sec": result.get("target_sec", ""),
        "library_root": result["library_root"],
        "db_path": result["db_path"],
    }

    # Add changes for delta scenario
    if "changes" in result:
        row["changes_added"] = result["changes"]["added"]
        row["changes_touched"] = result["changes"]["touched"]
        row["changes_deleted"] = result["changes"]["deleted"]
    else:
        row["changes_added"] = ""
        row["changes_touched"] = ""
        row["changes_deleted"] = ""

    # Add phase timings
    if "phases" in result:
        for phase_name, metrics in result["phases"].items():
            row[f"phase_{phase_name}_sec"] = metrics.wall_time

    # Write to CSV
    with open(csv_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    logger.info(f"Appended result to CSV: {csv_file}")


def benchmark_scan_phases(music_dir: Path, db):
    """Benchmark all scanning phases.

    Args:
        music_dir: Path to music library
        db: MusicDatabase instance

    Returns:
        dict: Results with phase metrics
    """
    results = {}

    # Phase 1: Walk + Stat (using Zig extension)
    with measure_phase("walk_stat") as metrics:
        try:
            from core._scan import count_audio_files

            file_count = count_audio_files(str(music_dir))
            metrics.file_count = file_count
        except (ImportError, NotImplementedError):
            # Fallback to Python implementation
            from utils.files import find_audio_files

            files = find_audio_files(music_dir)
            metrics.file_count = len(files)
            file_count = len(files)

    results["walk_stat"] = metrics

    # Phase 2: DB Diff
    with measure_phase("db_diff") as metrics:
        existing_files = db.get_existing_files()
        metrics.file_count = len(existing_files)

    results["db_diff"] = metrics

    # Phase 3 + 4: Parse + Write (combined in LibraryManager)
    with measure_phase("parse_write") as metrics:
        from core.library import LibraryManager

        lib_mgr = LibraryManager(db)

        # Count files before
        before_count = len(db.get_existing_files())

        # Add files
        lib_mgr.add_files_to_library([music_dir])

        # Count files after
        after_count = len(db.get_existing_files())

        metrics.file_count = file_count
        metrics.files_added = after_count - before_count
        metrics.db_size_bytes = Path(db.db_name).stat().st_size

    results["parse_write"] = metrics

    return results


def scenario_initial_import(music_dir: Path, db_path: Path) -> dict:
    """Benchmark: Fresh database, scan entire library.

    Args:
        music_dir: Path to music library
        db_path: Path to database file

    Returns:
        dict: Benchmark results
    """
    print(f"\n{'='*60}")
    print("Scenario: Initial Import")
    print(f"{'='*60}\n")

    logger.info("Starting initial import scenario")
    logger.info(f"Library: {music_dir}")
    logger.info(f"Database: {db_path}")

    # Ensure fresh database
    if db_path.exists():
        db_path.unlink()

    # Create persistent database for initial import
    # (will be reused by no-op and delta scenarios)
    from core.db import DB_TABLES, MusicDatabase

    bench_dir = Path("/tmp/mt-bench")
    bench_dir.mkdir(exist_ok=True, parents=True)

    db = MusicDatabase(str(db_path), DB_TABLES)

    try:
        results = benchmark_scan_phases(music_dir, db)

        total_time = sum(m.wall_time for m in results.values())
        file_count = results["walk_stat"].file_count

        throughput = file_count / total_time if total_time > 0 else 0

        logger.info(
            f"Initial import completed: {file_count:,} tracks in {total_time:.2f}s "
            f"({throughput:.0f} files/sec)"
        )

        # One-line summary for easy parsing
        logger.info(
            f"SUMMARY: initial_import | {file_count:,} tracks | {total_time:.2f}s | "
            f"{'PASS' if total_time < 300 else 'FAIL'}"
        )

        result = {
            "scenario": "initial_import",
            "timestamp": datetime.now().isoformat(),
            "library_root": str(music_dir),
            "db_path": str(db_path),
            "phases": results,
            "total_time_sec": total_time,
            "total_files": file_count,
            "throughput_files_sec": throughput,
            "pass": total_time < 300,  # < 5 minutes
            "target_sec": 300,
        }

        # Append to CSV results
        append_to_csv(result)

        return result
    finally:
        # Close database but DO NOT delete (persist for no-op/delta scenarios)
        db.close()


def scenario_noop_rescan(music_dir: Path, db_path: Path) -> dict:
    """Benchmark: Same database, no filesystem changes.

    IMPORTANT: This scenario REQUIRES the database to already exist from
    running scenario_initial_import. It does NOT populate the database itself.

    Args:
        music_dir: Path to music library
        db_path: Path to database file (must already exist)

    Returns:
        dict: Benchmark results

    Raises:
        FileNotFoundError: If database doesn't exist (run initial import first)
    """
    print(f"\n{'='*60}")
    print("Scenario: No-op Rescan")
    print(f"{'='*60}\n")

    logger.info("Starting no-op rescan scenario")
    logger.info(f"Library: {music_dir}")
    logger.info(f"Database: {db_path}")

    from tests.bench.fixtures import persistent_database

    with persistent_database(db_path) as (db, _):
        # Get initial track count from existing DB
        initial_count = len(db.get_existing_files())
        print(f"Database has {initial_count:,} tracks\n")
        logger.info(f"Database has {initial_count:,} tracks")

        # Benchmark rescan (should be fast - no changes)
        results = {}

        with measure_phase("walk_stat") as metrics:
            try:
                from core._scan import count_audio_files

                file_count = count_audio_files(str(music_dir))
                metrics.file_count = file_count
            except (ImportError, NotImplementedError):
                from utils.files import find_audio_files

                files = find_audio_files(music_dir)
                metrics.file_count = len(files)

        results["walk_stat"] = metrics

        with measure_phase("db_diff") as metrics:
            existing = db.get_existing_files()
            metrics.file_count = len(existing)

        results["db_diff"] = metrics

        # No parse/write phases (no changes detected)

        total_time = sum(m.wall_time for m in results.values())

        logger.info(
            f"No-op rescan completed: {initial_count:,} tracks in {total_time:.2f}s "
            f"({'PASS' if total_time < 10 else 'FAIL'})"
        )

        # One-line summary for easy parsing
        logger.info(
            f"SUMMARY: noop_rescan | {initial_count:,} tracks | {total_time:.2f}s | "
            f"{'PASS' if total_time < 10 else 'FAIL'}"
        )

        result = {
            "scenario": "noop_rescan",
            "timestamp": datetime.now().isoformat(),
            "library_root": str(music_dir),
            "db_path": str(db_path),
            "phases": results,
            "total_time_sec": total_time,
            "total_files": initial_count,
            "pass": total_time < 10,  # < 10 seconds
            "target_sec": 10,
        }

        # Append to CSV results
        append_to_csv(result)

        return result


def scenario_delta_rescan(
    music_dir: Path,
    db_path: Path,
    delta_add: int = 200,
    delta_touch: int = 200,
    delta_delete: int = 10,
) -> dict:
    """Benchmark: Delta rescan with file changes.

    IMPORTANT: This scenario REQUIRES the database to already exist from
    running scenario_initial_import. It reuses that database and modifies
    files in-place to simulate delta changes.

    Args:
        music_dir: Path to music library
        db_path: Path to database file (must already exist)
        delta_add: Number of files to add
        delta_touch: Number of files to touch (update mtime)
        delta_delete: Number of files to delete

    Returns:
        dict: Benchmark results

    Raises:
        FileNotFoundError: If database doesn't exist (run initial import first)
    """
    print(f"\n{'='*60}")
    print("Scenario: Delta Rescan")
    print(f"{'='*60}\n")
    print(f"Changes: +{delta_add} add, ~{delta_touch} touch, -{delta_delete} delete\n")

    logger.info("Starting delta rescan scenario")
    logger.info(f"Library: {music_dir}")
    logger.info(f"Database: {db_path}")
    logger.info(f"Changes: +{delta_add} add, ~{delta_touch} touch, -{delta_delete} delete")

    from tests.bench.fixtures import persistent_database

    with persistent_database(db_path) as (db, _):
        # Get initial track count from existing DB
        initial_count = len(db.get_existing_files())
        print(f"Database has {initial_count:,} tracks\n")
        logger.info(f"Database has {initial_count:,} tracks")

        # Simulate delta changes IN-PLACE
        print("Setup: Simulating changes in library...")
        all_files = list(music_dir.rglob("*.mp3"))
        all_files.extend(music_dir.rglob("*.flac"))
        all_files.extend(music_dir.rglob("*.m4a"))

        if not all_files:
            print("Error: No audio files found in music directory")
            sys.exit(1)

        # Track which files we modify so we can restore them
        added_files = []
        touched_files = []
        deleted_files = []

        try:
            # Add files (copy with new names)
            added_count = 0
            for i, src in enumerate(random.sample(all_files, min(delta_add, len(all_files)))):
                dst = src.parent / f"added_{i}_{src.name}"
                shutil.copy2(src, dst)
                added_files.append(dst)
                added_count += 1

            # Touch files (update mtime)
            touched_count = 0
            for f in random.sample(all_files, min(delta_touch, len(all_files))):
                f.touch()
                touched_files.append(f)
                touched_count += 1

            # Delete files (save paths for restoration)
            deleted_count = 0
            files_to_delete = random.sample(all_files, min(delta_delete, len(all_files)))
            # Save content before deletion
            deleted_file_data = [(f, f.read_bytes()) for f in files_to_delete]
            for f in files_to_delete:
                f.unlink()
                deleted_files.append(f)
                deleted_count += 1

            print(f"Applied changes: +{added_count}, ~{touched_count}, -{deleted_count}\n")

            # Benchmark rescan
            results = benchmark_scan_phases(music_dir, db)

            total_time = sum(m.wall_time for m in results.values())

            logger.info(
                f"Delta rescan completed: {added_count}+{touched_count}+{deleted_count} changes "
                f"in {total_time:.2f}s"
            )

            # One-line summary for easy parsing
            logger.info(
                f"SUMMARY: delta_rescan | {initial_count:,} tracks | {added_count}+{touched_count}+{deleted_count} changes | "
                f"{total_time:.2f}s"
            )

        finally:
            # Restore library to original state
            print("\nCleaning up: Restoring library to original state...")

            # Remove added files
            for f in added_files:
                if f.exists():
                    f.unlink()

            # Restore deleted files
            for f, content in deleted_file_data:
                f.write_bytes(content)

            print("Library restored\n")

        result = {
            "scenario": "delta_rescan",
            "timestamp": datetime.now().isoformat(),
            "library_root": str(music_dir),
            "db_path": str(db_path),
            "changes": {
                "added": added_count,
                "touched": touched_count,
                "deleted": deleted_count,
            },
            "phases": results,
            "total_time_sec": total_time,
            "total_files": initial_count,
        }

        # Append to CSV results
        append_to_csv(result)

        return result


def main():
    """Main entry point."""
    try:
        run_benchmarks()
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrupted by user (Ctrl+C)")
        print("Cleaning up...")
        # Cleanup will happen automatically via context managers
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"\n\n❌ Benchmark failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_benchmarks():
    """Run benchmark scenarios."""
    parser = argparse.ArgumentParser(description="Benchmark library scanning performance")
    parser.add_argument(
        "--library-root",
        type=Path,
        default=Path("/tmp/mt-bench/library"),
        help="Path to music library (default: /tmp/mt-bench/library)",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("/tmp/mt-bench/mt.db"),
        help="Path to database (default: /tmp/mt-bench/mt.db)",
    )
    parser.add_argument(
        "--scenario",
        choices=["initial", "noop", "delta", "full"],
        default="initial",
        help="Benchmark scenario to run",
    )
    parser.add_argument(
        "--delta-add",
        type=int,
        default=200,
        help="Number of files to add in delta scenario",
    )
    parser.add_argument(
        "--delta-touch",
        type=int,
        default=200,
        help="Number of files to touch in delta scenario",
    )
    parser.add_argument(
        "--delta-delete",
        type=int,
        default=10,
        help="Number of files to delete in delta scenario",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Write JSON results to file",
    )

    args = parser.parse_args()

    # Safety validation
    try:
        validate_paths(str(args.library_root), str(args.db_path))
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Check library exists
    if not args.library_root.exists():
        print(f"Error: Library not found: {args.library_root}")
        print("Run make_synth_library.py first to generate a test library")
        sys.exit(1)

    # Run scenario(s)
    results_list = []

    if args.scenario == "initial":
        results = scenario_initial_import(args.library_root, args.db_path)
        results_list.append(results)

    elif args.scenario == "noop":
        results = scenario_noop_rescan(args.library_root, args.db_path)
        results_list.append(results)

    elif args.scenario == "delta":
        results = scenario_delta_rescan(
            args.library_root,
            args.db_path,
            args.delta_add,
            args.delta_touch,
            args.delta_delete,
        )
        results_list.append(results)

    elif args.scenario == "full":
        # Run all scenarios
        results_list.append(scenario_initial_import(args.library_root, args.db_path))
        results_list.append(scenario_noop_rescan(args.library_root, args.db_path))
        results_list.append(
            scenario_delta_rescan(
                args.library_root,
                args.db_path,
                args.delta_add,
                args.delta_touch,
                args.delta_delete,
            )
        )

    # Report results
    reporter = HumanReporter()
    for results in results_list:
        reporter.report(results)

    # Write JSON output
    if args.output_json:
        json_reporter = JSONReporter()
        for i, results in enumerate(results_list):
            if len(results_list) == 1:
                output_path = args.output_json
            else:
                # Multiple scenarios: append scenario name
                scenario_name = results["scenario"]
                output_path = args.output_json.parent / f"{args.output_json.stem}_{scenario_name}.json"

            json_reporter.report(results, output_path)
            print(f"JSON output written to: {output_path}")


if __name__ == "__main__":
    main()
