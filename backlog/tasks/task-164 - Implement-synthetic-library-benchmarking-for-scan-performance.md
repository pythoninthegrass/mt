---
id: task-164
title: Implement synthetic library benchmarking for scan performance
status: Done
assignee: []
created_date: '2026-01-17 10:29'
updated_date: '2026-01-24 22:28'
labels:
  - performance
  - testing
  - scanning
dependencies: []
priority: high
ordinal: 39382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create a benchmarking suite to measure and validate library scanning performance before optimizing. The benchmark must prove the architecture can meet targets:
- Initial import of ~41k tracks: < 5 minutes (stretch: < 60s)
- No-op rescan (unchanged library): < 10s
- Incremental rescan (1% delta): proportional to changes

Key architectural requirement: scanning must use a 2-phase approach:
1. Phase 1 (inventory): walk + stat (mtime_ns, size) + DB diff — no tag parsing
2. Phase 2 (parse delta): mutagen only for added/changed files

This requires storing fingerprints (file_mtime_ns, file_size) in the library table.

Benchmarking approach:
- Dataset A (shape-only): 41k tiny files for traversal/DB stress testing
- Dataset B (clone-based): APFS clones of ~400 real seed files to 41k paths for realistic mutagen timing
- Dataset C (pathological): edge cases (2k+ files in one dir, deep nesting, corrupt files, unicode)

Scenarios to benchmark:
1. Initial import (fresh DB)
2. No-op rescan (same DB, no changes)
3. Delta rescan (add 200, touch 200, delete 10)

See docs/benchmark.md for comprehensive planning details.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 tests/bench/ directory created with benchmark scripts
- [x] #2 make_synth_library.py generates Dataset A (shape) and Dataset B (clone) libraries
- [x] #3 bench_scan.py measures walk, stat, DB diff, parse, and DB write phases separately
- [x] #4 Taskfile tasks added: bench:make:shape, bench:make:clone, bench:scan:initial, bench:scan:noop, bench:scan:delta, bench:scan:full
- [x] #5 All benchmarks use isolated DB path (/tmp/mt-bench/mt.db) - never touch production DB
- [x] #6 Benchmark outputs JSON + human-readable metrics: times, counts, throughput, peak RSS
- [x] #7 library table schema updated with file_mtime_ns column for fingerprint storage
- [x] #8 Optional: bench:zig:walk task to compare Zig traversal ceiling vs Python
<!-- AC:END -->
