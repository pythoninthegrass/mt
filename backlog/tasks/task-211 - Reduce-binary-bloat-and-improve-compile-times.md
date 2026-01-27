---
id: task-211
title: Reduce binary bloat and improve compile times
status: In Progress
assignee: []
created_date: '2026-01-27 02:50'
updated_date: '2026-01-27 04:23'
labels:
  - performance
  - rust
  - build-system
dependencies:
  - task-211.01
  - task-211.02
  - task-211.03
  - task-211.04
  - task-211.05
  - task-211.06
  - task-211.07
  - task-211.08
  - task-211.09
  - task-211.10
priority: high
ordinal: 812.5
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem

Profiling with `cargo bloat --release --crates` reveals significant binary bloat:

- **Binary size**: 13.9MB total
- **.text section**: 7.8MB
- **`mt_lib` contribution**: 2.6MB (32.7% of .text)

The main culprit is monomorphization bloat from 89 Tauri commands registered in a single `invoke_handler` closure in `src-tauri/src/lib.rs:211-300`.

## Analysis

### Top Contributors (cargo bloat)

| Crate | % of .text | Size |
|-------|------------|------|
| mt_lib | 32.7% | 2.6MiB |
| [Unknown] | 10.6% | 852.2KiB |
| std | 9.9% | 789.6KiB |
| tauri | 5.1% | 408.2KiB |
| lofty | 4.3% | 346.5KiB |
| regex_automata | 3.8% | 301.6KiB |
| reqwest | 3.6% | 289.3KiB |
| h2 | 3.5% | 282.9KiB |
| tonic | 1.6% | 125.9KiB |

### Largest Functions

| Size | Function |
|------|----------|
| 136.6KB | `mt_lib::run::inner::{{closure}}` |
| 59.5KB | `mt_lib::run::{{closure}}` |
| 50.8KB | `lofty::id3::v2::read::read_all_frames_into_tag` (appears 4x!) |

### Root Causes

1. **89 Tauri commands in single handler** - All IPC serialization monomorphized into one 196KB closure
2. **Generic duplication** - lofty ID3 parsing appears 4x due to generic instantiation
3. **HTTP stack duplication** - h2/hyper duplicated across reqwest, tonic, mt_lib
4. **devtools plugin** - Adds entire gRPC/HTTP stack (tonic, h2, devtools_*)

### Current Release Profile (already optimized)

```toml
[profile.release]
panic = "abort"
codegen-units = 1
lto = true
opt-level = "s"
strip = true
```

## Impact on Compile Times

The single 196KB `run::inner` closure recompiles whenever ANY command changes, making incremental builds slower than necessary.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Binary size reduced by at least 15%
- [ ] #2 Incremental compile time for single command change under 10 seconds
- [x] #3 devtools excluded from release builds
- [ ] #4 Commands split into logical plugin groups
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Action Items (by impact)

### 1. Feature-gate devtools in release builds (Quick Win)
- Verify `devtools` feature is not enabled in release profile
- Check `Cargo.toml` default features
- Expected savings: ~300KB (tonic + devtools_* + h2 duplication)

### 2. Split commands into Tauri plugins (High Impact)
Refactor 89 commands into logical plugin groups:

| Plugin | Commands | Files |
|--------|----------|-------|
| `audio-plugin` | audio_*, media_* | 12 commands |
| `library-plugin` | library_* | 13 commands |
| `queue-plugin` | queue_* | 10 commands |
| `playlist-plugin` | playlist_* | 9 commands |
| `favorites-plugin` | favorites_* | 6 commands |
| `lastfm-plugin` | lastfm_* | 9 commands |
| `settings-plugin` | settings_* | 5 commands |
| `watcher-plugin` | watched_folders_* | 7 commands |
| `scanner-plugin` | scan_*, extract_*, get_track_artwork* | 5 commands |
| `core-plugin` | app_*, dialog_*, export_* | 6 commands |

Benefits:
- Parallel compilation of plugins
- Isolated monomorphization (smaller closures)
- Better code organization
- Faster incremental builds (only changed plugin recompiles)

### 3. Consolidate similar commands (Medium Impact)
- `settings_get`, `settings_set`, `settings_update`, `settings_reset`, `settings_get_all` → single `settings_op` with action enum
- Similar pattern for other CRUD-style command groups

### 4. Investigate lofty generic duplication (Low-Medium Impact)
- Profile why `read_all_frames_into_tag` appears 4x
- Consider using concrete types instead of generics where possible
- Check if lofty has feature flags to reduce code paths

### 5. Audit HTTP client usage (Low Impact)
- Verify only one HTTP client is needed (reqwest)
- Check if tonic/gRPC is only from devtools
- Consider lighter alternatives if multiple clients exist

## Measurement Commands

```bash
# Baseline measurements
cargo bloat --release --crates > baseline-crates.txt
cargo bloat --release -n 50 > baseline-functions.txt
time cargo build --release  # Full build time
touch src/lib.rs && time cargo build --release  # Incremental build time

# After changes, compare
cargo bloat --release --crates > after-crates.txt
diff baseline-crates.txt after-crates.txt
```
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Progress (2026-01-26)

### Completed: Feature-gate devtools in release builds

**Commit:** `2e2b23c` - perf: feature-gate devtools to reduce release binary size

**Changes:**
- Removed `devtools` from default features in Cargo.toml
- Removed `tauri = { features = ["devtools"] }` (now empty features)
- Updated devtools feature to include `tauri/devtools` when enabled
- Added `#[allow(unused_mut)]` for builder variable

**Results:**

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Binary size | 13.9MB | 8.7MB | **-37.6%** |
| .text section | 7.8MB | 6.1MB | -22% |
| mt_lib size | 2.6MB | 1.7MB | -35% |
| h2 (HTTP/2) | 282.9KB | 53.6KB | -81% |
| tonic (gRPC) | 125.9KB | 0 | -100% |
| Crate count | 160 | 136 | -15% |

Devtools can still be enabled for development with:
```bash
cargo build --features devtools
cargo tauri dev --features devtools
```

### Remaining Work

#### Incremental compile time (<10s) - Not achieved

The 10-second incremental compile target is fundamentally at odds with the current release profile:
- `lto = true` requires reprocessing at link time (~40-60s overhead)
- `codegen-units = 1` prevents parallel codegen
- `opt-level = "s"` adds optimization overhead

**Options for future work:**
1. Create a `[profile.release-dev]` for faster iteration without LTO
2. Accept slower release builds as tradeoff for smaller binary
3. Use `cargo check` for fast validation, reserve full builds for CI

#### Plugin architecture - Not implemented

Splitting 89 commands into Tauri plugins would:
- Enable parallel plugin compilation
- Reduce invoke_handler closure size (currently 136.5KB)
- Improve code organization

However, this is a significant refactoring with risk. The commands are already well-organized in modules:
- `commands/audio.rs` (8 commands)
- `commands/favorites.rs` (7 commands)
- `commands/lastfm.rs` (10 commands)
- `commands/playlists.rs` (10 commands)
- `commands/queue.rs` (11 commands)
- `commands/settings.rs` (5 commands)
- `library/commands.rs` (14 commands)
- `scanner/commands.rs` (5 commands)
- `watcher/` (7 commands)
- `lib.rs` (12 commands)

Recommend creating a separate task for plugin migration if incremental compile time becomes a priority.

## Child Tasks Created (2026-01-26)

10 plugin tasks created as dependencies:

| Task | Plugin | Commands | Priority |
|------|--------|----------|----------|
| 211.01 | audio-plugin | 12 | Medium |
| 211.02 | library-plugin | 14 | Medium |
| 211.03 | queue-plugin | 11 | Medium |
| 211.04 | playlist-plugin | 10 | Medium |
| 211.05 | favorites-plugin | 7 | Low |
| 211.06 | lastfm-plugin | 10 | Low |
| 211.07 | settings-plugin | 5 | Low |
| 211.08 | watcher-plugin | 7 | Low |
| 211.09 | scanner-plugin | 5 | Low |
| 211.10 | core-plugin | 6 | Low |

**Total: 87 commands across 10 plugins**

Recommended order: Start with medium priority tasks (audio, library, queue, playlist) as they cover the most frequently changed code paths.
<!-- SECTION:NOTES:END -->
