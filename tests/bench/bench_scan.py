#!/usr/bin/env python
"""Benchmark library scanning performance with different scenarios."""
import argparse
import random
import shutil
import sys
from datetime import datetime
from pathlib import Path
from tests.bench.fixtures import isolated_database, validate_paths
from tests.bench.instrumentation import measure_phase
from tests.bench.reporters import HumanReporter, JSONReporter


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

    # Ensure fresh database
    if db_path.exists():
        db_path.unlink()

    with isolated_database() as (db, _):
        results = benchmark_scan_phases(music_dir, db)

        total_time = sum(m.wall_time for m in results.values())
        file_count = results["walk_stat"].file_count

        throughput = file_count / total_time if total_time > 0 else 0

        return {
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


def scenario_noop_rescan(music_dir: Path, db_path: Path) -> dict:
    """Benchmark: Same database, no filesystem changes.

    Args:
        music_dir: Path to music library
        db_path: Path to database file

    Returns:
        dict: Benchmark results
    """
    print(f"\n{'='*60}")
    print("Scenario: No-op Rescan")
    print(f"{'='*60}\n")

    with isolated_database() as (db, _):
        # Setup: Populate database first
        print("Setup: Populating database...")
        from core.library import LibraryManager

        lib_mgr = LibraryManager(db)
        lib_mgr.add_files_to_library([music_dir])

        initial_count = len(db.get_existing_files())
        print(f"Database populated with {initial_count:,} tracks\n")

        # Now benchmark rescan (should be fast - no changes)
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

        return {
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


def scenario_delta_rescan(
    music_dir: Path,
    db_path: Path,
    delta_add: int = 200,
    delta_touch: int = 200,
    delta_delete: int = 10,
) -> dict:
    """Benchmark: Delta rescan with file changes.

    Args:
        music_dir: Path to music library
        db_path: Path to database file
        delta_add: Number of files to add
        delta_touch: Number of files to touch (update mtime)
        delta_delete: Number of files to delete

    Returns:
        dict: Benchmark results
    """
    print(f"\n{'='*60}")
    print("Scenario: Delta Rescan")
    print(f"{'='*60}\n")
    print(f"Changes: +{delta_add} add, ~{delta_touch} touch, -{delta_delete} delete\n")

    # Create temp copy of music directory
    temp_music_dir = Path("/tmp/mt-bench/music-delta")
    if temp_music_dir.exists():
        shutil.rmtree(temp_music_dir)

    print("Setup: Copying music directory...")
    shutil.copytree(music_dir, temp_music_dir)

    with isolated_database() as (db, _):
        # Populate initial database
        print("Setup: Populating database...")
        from core.library import LibraryManager

        lib_mgr = LibraryManager(db)
        lib_mgr.add_files_to_library([temp_music_dir])

        initial_count = len(db.get_existing_files())
        print(f"Database populated with {initial_count:,} tracks\n")

        # Simulate delta changes
        print("Setup: Simulating changes...")
        all_files = list(temp_music_dir.rglob("*.mp3"))
        all_files.extend(temp_music_dir.rglob("*.flac"))
        all_files.extend(temp_music_dir.rglob("*.m4a"))

        if not all_files:
            print("Error: No audio files found in music directory")
            shutil.rmtree(temp_music_dir)
            sys.exit(1)

        # Add files (copy with new names)
        added_count = 0
        for i, src in enumerate(random.sample(all_files, min(delta_add, len(all_files)))):
            dst = src.parent / f"added_{i}_{src.name}"
            shutil.copy2(src, dst)
            added_count += 1

        # Touch files (update mtime)
        touched_count = 0
        for f in random.sample(all_files, min(delta_touch, len(all_files))):
            f.touch()
            touched_count += 1

        # Delete files
        deleted_count = 0
        for f in random.sample(all_files, min(delta_delete, len(all_files))):
            f.unlink()
            deleted_count += 1

        print(f"Applied changes: +{added_count}, ~{touched_count}, -{deleted_count}\n")

        # Benchmark rescan
        results = benchmark_scan_phases(temp_music_dir, db)

        total_time = sum(m.wall_time for m in results.values())

        # Cleanup
        shutil.rmtree(temp_music_dir)

        return {
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


def main():
    """Main entry point."""
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
