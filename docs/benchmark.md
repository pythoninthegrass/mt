# Library Scanning Benchmark Plan

This document describes the synthetic benchmarking strategy for validating library scanning performance before optimizing. The goal is to prove the architecture can meet performance targets without risking the production database or requiring access to the full 267GB library.

## Performance Targets

| Scenario | Target | Stretch Goal |
|----------|--------|--------------|
| Initial import (~41k tracks) | < 5 minutes | < 60 seconds |
| No-op rescan (unchanged) | < 10 seconds | < 5 seconds |
| Incremental rescan (1% delta) | Proportional to changes | — |

## Current Architecture Analysis

### Scan Flow (as of January 2026)

```
Frontend (Tauri)
    │
    ▼ POST /api/library/scan
FastAPI (Python sidecar)
    │
    ├─► scan_paths() [backend/services/scanner.py]
    │       │
    │       ├─► os.walk() — enumerate directories
    │       ├─► extension filter — identify audio files
    │       └─► extract_metadata() — mutagen parse (EVERY file)
    │
    └─► For each file:
            ├─► get_track_by_filepath() — SELECT (duplicate check)
            ├─► add_track() — INSERT + commit() per track
            └─► Return added track
```

### Current Bottlenecks

1. **Tag parsing on every file**: `scan_paths()` calls `extract_metadata()` for all audio files before checking if they exist in DB. This means no-op rescans still parse all tags.

2. **Per-track commits**: `add_track()` commits after every INSERT. At 41k tracks, this alone can push import time to minutes.

3. **No change detection**: There's no stored fingerprint (`mtime`, `size`) to detect whether a file has changed, so rescans must re-parse everything.

### Zig Module (Available but Unused)

The repo contains a Zig scanning module (`app/src/scan.zig`) with:
- `scan_music_directory(root_path)` — fast recursive file counting
- `count_audio_files(root_path)` — file counting
- `is_audio_file(filename)` — extension check
- `benchmark_directory(root_path, iterations)` — performance measurement

This is currently used only in tests/benchmarks, not in the production scan path.

## Required Architectural Change

To meet the **no-op < 10s** target, scanning must be split into two phases:

### Phase 1: Inventory (Fast, No Tag Parsing)

```python
# For each audio file candidate:
stat_result = os.stat(filepath)
fingerprint = (stat_result.st_mtime_ns, stat_result.st_size)

# Compare against DB:
# - Not in DB → ADDED
# - In DB, same fingerprint → UNCHANGED (skip)
# - In DB, different fingerprint → MODIFIED
# - In DB but not on disk → DELETED
```

### Phase 2: Parse Delta Only

```python
# Only for ADDED and MODIFIED files:
metadata = extract_metadata(filepath)  # mutagen
# Then bulk insert/update with single transaction
```

### Schema Requirement

Add to `library` table:
```sql
file_mtime_ns INTEGER,  -- nanosecond precision mtime
file_size INTEGER       -- already exists, ensure always populated
```

## Synthetic Datasets

### Why Synthetic?

- **Safety**: Never risk corrupting the production database
- **Repeatability**: Same inputs produce comparable results across runs
- **Speed**: Generate test data in seconds, not hours
- **Isolation**: Benchmark specific components (walk, parse, DB) independently

### Dataset A: Shape-Only (Traversal + DB Stress)

**Purpose**: Measure filesystem traversal and SQLite throughput without mutagen overhead.

**Characteristics**:
- 41,000 files (matching real library scale)
- Tiny files (0-1 byte) — mutagen will fail fast
- Realistic directory structure: `Artist/Album/Track.ext`
- Extension distribution: ~75% mp3, ~15% flac, ~8% m4a, ~2% other
- Optional `cover.jpg` placeholders per album

**What it measures**:
- Directory enumeration speed
- `stat()` call overhead
- SQLite INSERT throughput
- DB diff/query performance

### Dataset B: Clone-Based (Realistic Parse Cost)

**Purpose**: Measure true end-to-end scan time with realistic mutagen work.

**Characteristics**:
- ~400 real audio files as seed (your existing test libraries)
- Replicated to 41,000 paths using APFS clone copies
- Minimal disk usage (clones are space-efficient)
- Real ID3/MP4/FLAC tags for mutagen to parse

**Why APFS clones (not hardlinks)**:
- Clones behave as independent files (separate inodes)
- Safer if tracking inode/dev for move detection later
- No "one file changed affects many entries" weirdness
- macOS does support hardlinks to files, but clones are cleaner

**What it measures**:
- Realistic mutagen parse time per file type
- File open/read/close overhead
- True initial import time

### Dataset C: Pathological Cases (Robustness)

**Purpose**: Ensure the scanner doesn't explode on edge cases.

**Characteristics**:
- One directory with 2,000+ tracks (compilations)
- Deep nesting (10+ levels)
- Corrupt/truncated audio files
- Very long filenames
- Unicode/emoji in paths
- Wrong extensions (e.g., `.mp3` file that's actually FLAC)

**What it measures**:
- Error handling robustness
- Worst-case traversal behavior
- Graceful degradation

## Benchmark Scenarios

### Scenario 1: Initial Import (Fresh DB)

```bash
# Setup
rm -f /tmp/mt-bench/mt.db
# Run
task bench:scan:initial
```

**Measures**: Full pipeline — walk + stat + parse all + DB insert all

**Target**: < 5 minutes (stretch: < 60s)

**Expected breakdown** (hypothetical):
| Phase | Time |
|-------|------|
| Walk + stat | 5-15s |
| Metadata parse | 60-180s |
| DB writes | 10-60s |
| **Total** | ~2-4 min |

### Scenario 2: No-Op Rescan

```bash
# Run immediately after initial import (same DB)
task bench:scan:noop
```

**Measures**: Phase 1 only — walk + stat + DB diff (no parsing)

**Target**: < 10 seconds

**Expected breakdown**:
| Phase | Time |
|-------|------|
| Walk + stat | 5-10s |
| DB diff | 1-3s |
| Parse (0 files) | 0s |
| DB writes (0) | 0s |
| **Total** | ~6-13s |

If this exceeds 10s, investigate:
- Is traversal too slow? (Compare with Zig benchmark)
- Is DB diff query inefficient? (Check indexes)

### Scenario 3: Delta Rescan (1% Change)

```bash
# Mutate the synthetic library first:
# - Add 200 new files
# - Touch mtime on 200 existing files
# - Delete 10 files
task bench:scan:delta
```

**Measures**: Phase 1 + Phase 2 for ~410 files

**Target**: Proportional to delta size (not full library)

**Expected breakdown**:
| Phase | Time |
|-------|------|
| Walk + stat | 5-10s |
| DB diff | 1-3s |
| Parse (~410 files) | 5-15s |
| DB writes (~410) | 1-3s |
| **Total** | ~12-30s |

### Scenario 4: Burst Changes (Watcher Simulation)

```bash
# Add 500 files at once
# Rename an artist directory
task bench:scan:burst
```

**Purpose**: Validate that filesystem watcher events can be debounced and batched effectively.

## Benchmark Tooling

### Directory Structure

```
tests/bench/
├── __init__.py
├── make_synth_library.py   # Generate synthetic datasets
├── bench_scan.py           # Run benchmark scenarios
├── bench_zig_walk.py       # Compare Zig vs Python traversal
└── report.py               # Aggregate results, detect regressions
```

### `make_synth_library.py`

```bash
# Dataset A: shape-only
python tests/bench/make_synth_library.py \
  --out-root /tmp/mt-bench/library \
  --tracks 41000 \
  --mode shape

# Dataset B: clone-based
python tests/bench/make_synth_library.py \
  --out-root /tmp/mt-bench/library \
  --seed-dir /path/to/seed1 \
  --seed-dir /path/to/seed2 \
  --tracks 41000 \
  --mode clone
```

**Options**:
- `--out-root`: Output directory for synthetic library
- `--seed-dir`: Source directories for real audio files (clone mode)
- `--tracks`: Number of tracks to generate (default: 41000)
- `--mode`: `shape` (tiny files) or `clone` (APFS clones)
- `--ext-ratio`: Extension distribution (default: mp3=0.75,flac=0.15,m4a=0.08,other=0.02)
- `--albums`: Number of albums (default: auto-calculated)
- `--with-covers`: Include `cover.jpg` placeholders

### `bench_scan.py`

```bash
# Initial import
python tests/bench/bench_scan.py \
  --library-root /tmp/mt-bench/library \
  --db-path /tmp/mt-bench/mt.db \
  --scenario initial

# No-op rescan
python tests/bench/bench_scan.py \
  --library-root /tmp/mt-bench/library \
  --db-path /tmp/mt-bench/mt.db \
  --scenario noop

# Delta rescan
python tests/bench/bench_scan.py \
  --library-root /tmp/mt-bench/library \
  --db-path /tmp/mt-bench/mt.db \
  --scenario delta \
  --delta-add 200 \
  --delta-touch 200 \
  --delta-delete 10
```

**Options**:
- `--library-root`: Path to synthetic library
- `--db-path`: Path to benchmark database (NEVER production!)
- `--scenario`: `initial`, `noop`, `delta`, or `full` (runs all)
- `--delta-*`: Parameters for delta scenario
- `--repeat`: Number of iterations (default: 1)
- `--output-json`: Write results to JSONL file

### Output Format

**Human-readable** (stdout):
```
=== Benchmark: initial ===
Library: /tmp/mt-bench/library
Database: /tmp/mt-bench/mt.db
Tracks: 41,000

Phase Timings:
  Walk + filter:    8.234s
  Stat collection:  4.567s
  DB diff:          0.000s (fresh DB)
  Metadata parse:  127.891s
  DB writes:       23.456s
  ─────────────────────────
  Total:          164.148s (2m 44s)

Counts:
  Visited:     52,341
  Candidates:  41,000
  Added:       41,000
  Changed:          0
  Unchanged:        0
  Deleted:          0
  Errors:          12

Throughput:
  Walk:        6,356 files/sec
  Parse:         320 files/sec
  DB write:    1,748 rows/sec

Memory:
  Peak RSS:    234.5 MB

Result: PASS (< 5 minutes)
```

**JSON** (for aggregation):
```json
{
  "scenario": "initial",
  "timestamp": "2026-01-17T15:30:00Z",
  "library_root": "/tmp/mt-bench/library",
  "db_path": "/tmp/mt-bench/mt.db",
  "timings": {
    "walk_filter_sec": 8.234,
    "stat_sec": 4.567,
    "db_diff_sec": 0.0,
    "parse_sec": 127.891,
    "db_write_sec": 23.456,
    "total_sec": 164.148
  },
  "counts": {
    "visited": 52341,
    "candidates": 41000,
    "added": 41000,
    "changed": 0,
    "unchanged": 0,
    "deleted": 0,
    "errors": 12
  },
  "throughput": {
    "walk_files_per_sec": 6356,
    "parse_files_per_sec": 320,
    "db_rows_per_sec": 1748
  },
  "memory": {
    "peak_rss_mb": 234.5
  },
  "pass": true,
  "target_sec": 300
}
```

## Taskfile Integration

```yaml
# taskfiles/bench.yml (included in main Taskfile.yml)

version: "3.0"

vars:
  BENCH_ROOT: "/tmp/mt-bench"
  BENCH_LIBRARY: "{{.BENCH_ROOT}}/library"
  BENCH_DB: "{{.BENCH_ROOT}}/mt.db"

tasks:
  make:shape:
    desc: "Generate shape-only synthetic library (41k tiny files)"
    cmds:
      - mkdir -p {{.BENCH_ROOT}}
      - python tests/bench/make_synth_library.py
          --out-root {{.BENCH_LIBRARY}}
          --tracks 41000
          --mode shape
          {{.CLI_ARGS}}

  make:clone:
    desc: "Generate clone-based synthetic library (requires --seed-dir)"
    cmds:
      - mkdir -p {{.BENCH_ROOT}}
      - python tests/bench/make_synth_library.py
          --out-root {{.BENCH_LIBRARY}}
          --tracks 41000
          --mode clone
          {{.CLI_ARGS}}

  scan:initial:
    desc: "Benchmark initial import (fresh DB)"
    cmds:
      - rm -f {{.BENCH_DB}}
      - python tests/bench/bench_scan.py
          --library-root {{.BENCH_LIBRARY}}
          --db-path {{.BENCH_DB}}
          --scenario initial
          {{.CLI_ARGS}}

  scan:noop:
    desc: "Benchmark no-op rescan (unchanged library)"
    cmds:
      - python tests/bench/bench_scan.py
          --library-root {{.BENCH_LIBRARY}}
          --db-path {{.BENCH_DB}}
          --scenario noop
          {{.CLI_ARGS}}

  scan:delta:
    desc: "Benchmark delta rescan (1% changes)"
    cmds:
      - python tests/bench/bench_scan.py
          --library-root {{.BENCH_LIBRARY}}
          --db-path {{.BENCH_DB}}
          --scenario delta
          --delta-add 200
          --delta-touch 200
          --delta-delete 10
          {{.CLI_ARGS}}

  scan:full:
    desc: "Run all scenarios (initial + noop + delta) with 3 iterations"
    cmds:
      - task: scan:initial
      - task: scan:noop
      - task: scan:delta
      - task: scan:noop  # Verify delta didn't break noop

  zig:walk:
    desc: "Benchmark Zig traversal (discovery ceiling)"
    cmds:
      - python tests/bench/bench_zig_walk.py
          --library-root {{.BENCH_LIBRARY}}
          --iterations 5
          {{.CLI_ARGS}}

  clean:
    desc: "Remove benchmark artifacts"
    cmds:
      - rm -rf {{.BENCH_ROOT}}
```

## Safety Guarantees

### Hard Rules

1. **Never touch production DB**: All benchmarks use `/tmp/mt-bench/mt.db`
2. **Never point at real library**: Always use synthetic library under `/tmp/mt-bench/library`
3. **Isolated environment**: Benchmark scripts refuse to run if paths look like production

### Safeguards in Code

```python
# In bench_scan.py
def validate_paths(library_root: str, db_path: str):
    """Refuse to run against production paths."""
    dangerous_patterns = [
        "Library/Application Support",
        "com.mt.desktop",
        "/Music/",
        os.path.expanduser("~/Music"),
    ]
    for pattern in dangerous_patterns:
        if pattern in library_root or pattern in db_path:
            raise ValueError(
                f"Refusing to benchmark against production path: {pattern}\n"
                f"Use /tmp/mt-bench/ for benchmarks."
            )
```

## Interpreting Results

### If No-Op Rescan > 10s

**Likely causes**:
1. **Traversal too slow**: Compare with `task bench:zig:walk`
   - If Zig is much faster → optimize Python walker (use `os.scandir` recursion)
   - If Zig is also slow → filesystem/disk issue
2. **DB diff too slow**: Check if `filepath` column is indexed
3. **Still parsing tags**: Verify Phase 1 is truly skipping `extract_metadata()`

### If Initial Import > 5 Minutes

**Check phase breakdown**:
1. **Parse dominates**: mutagen is slow
   - Consider parallel parsing (multiprocessing)
   - Consider Rust-based tag reader (lofty-rs)
2. **DB writes dominate**: transaction strategy is wrong
   - Switch to single transaction per scan
   - Use `executemany()` for bulk inserts
   - Enable WAL mode + `synchronous=NORMAL`

### Typical Bottleneck Distribution

For a well-optimized scanner at 41k tracks:

| Phase | Expected % of Time |
|-------|-------------------|
| Walk + stat | 5-10% |
| DB diff | 2-5% |
| Metadata parse | 60-80% |
| DB writes | 10-20% |

If your distribution differs significantly, that's where to focus optimization.

## Future Enhancements

### File Watching Integration

Once benchmarks pass, implement hybrid monitoring:
1. **Startup scan**: Fast Phase-1-only to catch changes while app was closed
2. **Runtime watcher**: `notify` crate (Rust) or `watchdog` (Python) for live changes
3. **Debouncing**: Buffer events for 500ms-1s before triggering rescan

### Move Detection (Optional)

If users frequently reorganize libraries:
- Store `(inode, dev)` in addition to `(mtime_ns, size)`
- Detect "same content, different path" as MOVED rather than DELETE+ADD
- Preserves play counts, favorites, playlist membership

### Parallel Parsing

For initial import speedup:
- Use `multiprocessing.Pool` for `extract_metadata()` calls
- Or move to Rust with `rayon` + `lofty-rs`

## Related Tasks

- **task-164**: Implement synthetic library benchmarking (this plan)
- **task-012**: Implement performance optimizations (depends on task-164)

## References

- [SQLite INSERT Performance](https://www.sqlite.org/faq.html#q19)
- [APFS Clone Copies](https://developer.apple.com/documentation/foundation/filemanager/2293212-copyitem)
- [notify-rs (Rust file watcher)](https://github.com/notify-rs/notify)
- [mutagen (Python audio metadata)](https://mutagen.readthedocs.io/)
