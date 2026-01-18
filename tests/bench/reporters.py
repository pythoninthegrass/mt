"""Output reporters for benchmark results."""
import csv
import json
from pathlib import Path
from tests.bench.instrumentation import PhaseMetrics, format_size, format_throughput, format_time


class HumanReporter:
    """Output benchmark results in human-readable format."""

    def report(self, results: dict) -> None:
        """Print formatted results to stdout.

        Args:
            results: Benchmark results dictionary with scenario, phases, and metrics
        """
        scenario = results.get("scenario", "unknown")
        print(f"\n{'='*60}")
        print(f"Benchmark: {scenario}")
        print(f"{'='*60}")

        # Library and database info
        if "library_root" in results:
            print(f"\nLibrary: {results['library_root']}")
        if "db_path" in results:
            print(f"Database: {results['db_path']}")
        if "total_files" in results:
            print(f"Tracks: {results['total_files']:,}")

        # Phase breakdown
        if "phases" in results:
            print("\nPhase Timings:")
            total_time = 0.0
            for phase_name, metrics in results["phases"].items():
                if isinstance(metrics, PhaseMetrics):
                    time_str = format_time(metrics.wall_time)
                    print(f"  {phase_name:20} {time_str:>12}")
                    total_time += metrics.wall_time
                elif isinstance(metrics, dict):
                    time_str = format_time(metrics.get("wall_time_sec", 0))
                    print(f"  {phase_name:20} {time_str:>12}")
                    total_time += metrics.get("wall_time_sec", 0)

            print(f"  {'':-<35}")
            print(f"  {'Total:':20} {format_time(total_time):>12}")

        # Change counts
        if "changes" in results:
            changes = results["changes"]
            print("\nChanges:")
            print(f"  Added:   {changes.get('added', 0):>8,}")
            print(f"  Touched: {changes.get('touched', 0):>8,}")
            print(f"  Deleted: {changes.get('deleted', 0):>8,}")

        # File counts
        counts = results.get("counts", {})
        if counts:
            print("\nCounts:")
            if "visited" in counts:
                print(f"  Visited:     {counts['visited']:>8,}")
            if "candidates" in counts:
                print(f"  Candidates:  {counts['candidates']:>8,}")
            if "added" in counts:
                print(f"  Added:       {counts['added']:>8,}")
            if "changed" in counts:
                print(f"  Changed:     {counts['changed']:>8,}")
            if "unchanged" in counts:
                print(f"  Unchanged:   {counts['unchanged']:>8,}")
            if "deleted" in counts:
                print(f"  Deleted:     {counts['deleted']:>8,}")
            if "errors" in counts:
                print(f"  Errors:      {counts['errors']:>8,}")

        # Throughput
        if "throughput_files_sec" in results:
            print("\nThroughput:")
            throughput = results["throughput_files_sec"]
            print(f"  {format_throughput(throughput)}")

        if "throughput" in results:
            throughput_data = results["throughput"]
            print("\nThroughput:")
            if "walk_files_per_sec" in throughput_data:
                print(f"  Walk:        {format_throughput(throughput_data['walk_files_per_sec'])}")
            if "parse_files_per_sec" in throughput_data:
                print(f"  Parse:       {format_throughput(throughput_data['parse_files_per_sec'])}")
            if "db_rows_per_sec" in throughput_data:
                print(f"  DB write:    {format_throughput(throughput_data['db_rows_per_sec'])}")

        # Memory
        if "memory" in results:
            memory_data = results["memory"]
            print("\nMemory:")
            if "peak_rss_mb" in memory_data:
                print(f"  Peak RSS:    {memory_data['peak_rss_mb']:.1f} MB")

        # Database size
        if "db_size_bytes" in results:
            print(f"\nDatabase Size: {format_size(results['db_size_bytes'])}")

        # Pass/fail
        if "pass" in results:
            status = "PASS" if results["pass"] else "FAIL"
            target = results.get("target_sec", 0)
            actual = results.get("total_time_sec", 0)
            print(f"\nResult: {status} ({format_time(actual)} / {format_time(target)} target)")

        print()


class JSONReporter:
    """Output benchmark results as machine-readable JSON."""

    def report(self, results: dict, output_path: Path) -> None:
        """Write results to JSON file.

        Args:
            results: Benchmark results dictionary
            output_path: Path to output JSON file
        """
        # Convert PhaseMetrics objects to dicts
        serializable_results = self._make_serializable(results)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(serializable_results, f, indent=2, default=str)

    def _make_serializable(self, obj):
        """Recursively convert objects to JSON-serializable format."""
        if isinstance(obj, PhaseMetrics):
            return obj.to_dict()
        elif isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, Path):
            return str(obj)
        else:
            return obj


class CSVReporter:
    """Output benchmark results as CSV for spreadsheet analysis."""

    def report(self, results: dict, output_path: Path) -> None:
        """Write results to CSV file.

        Args:
            results: Benchmark results dictionary
            output_path: Path to output CSV file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "scenario",
                "phase",
                "wall_time_sec",
                "cpu_time_sec",
                "file_count",
                "files_added",
                "files_changed",
                "files_deleted",
                "throughput_files_sec",
                "memory_peak_mb",
                "db_size_bytes",
            ])

            # Rows
            scenario = results.get("scenario", "unknown")
            phases = results.get("phases", {})

            for phase_name, metrics in phases.items():
                if isinstance(metrics, PhaseMetrics):
                    writer.writerow([
                        scenario,
                        phase_name,
                        metrics.wall_time,
                        metrics.cpu_time,
                        metrics.file_count,
                        metrics.files_added,
                        metrics.files_changed,
                        metrics.files_deleted,
                        metrics.throughput_files_sec,
                        metrics.memory_peak_mb,
                        metrics.db_size_bytes,
                    ])
                elif isinstance(metrics, dict):
                    writer.writerow([
                        scenario,
                        phase_name,
                        metrics.get("wall_time_sec", 0),
                        metrics.get("cpu_time_sec", 0),
                        metrics.get("file_count", 0),
                        metrics.get("files_added", 0),
                        metrics.get("files_changed", 0),
                        metrics.get("files_deleted", 0),
                        metrics.get("throughput_files_sec", 0),
                        metrics.get("memory_peak_mb", 0),
                        metrics.get("db_size_bytes", 0),
                    ])


class ComparisonReporter:
    """Compare benchmark results before/after optimization."""

    def compare(self, baseline_path: Path, current_results: dict) -> None:
        """Compare current results against baseline.

        Args:
            baseline_path: Path to baseline JSON results
            current_results: Current benchmark results to compare
        """
        # Load baseline
        with open(baseline_path) as f:
            baseline = json.load(f)

        print(f"\n{'='*60}")
        print("Performance Comparison")
        print(f"{'='*60}")

        # Compare total time
        baseline_time = baseline.get("total_time_sec", 0)
        current_time = current_results.get("total_time_sec", 0)

        if baseline_time > 0:
            improvement = ((baseline_time - current_time) / baseline_time) * 100
        else:
            improvement = 0.0

        print("\nTotal Time:")
        print(f"  Baseline: {format_time(baseline_time)}")
        print(f"  Current:  {format_time(current_time)}")
        print(f"  Change:   {improvement:+.1f}%")

        # Compare phase times
        baseline_phases = baseline.get("phases", {})
        current_phases = current_results.get("phases", {})

        if baseline_phases and current_phases:
            print("\nPhase Breakdown:")
            for phase_name in baseline_phases:
                if phase_name not in current_phases:
                    continue

                baseline_phase_time = baseline_phases[phase_name].get("wall_time_sec", 0)
                current_metrics = current_phases[phase_name]

                if isinstance(current_metrics, PhaseMetrics):
                    current_phase_time = current_metrics.wall_time
                else:
                    current_phase_time = current_metrics.get("wall_time_sec", 0)

                if baseline_phase_time > 0:
                    phase_improvement = ((baseline_phase_time - current_phase_time) / baseline_phase_time) * 100
                else:
                    phase_improvement = 0.0

                print(
                    f"  {phase_name:20} {format_time(baseline_phase_time):>12} "
                    f"→ {format_time(current_phase_time):>12} ({phase_improvement:+.1f}%)"
                )

        print()
