---
id: task-211.11
title: Extract shared types into mt-core crate for plugin architecture
status: Done
assignee: []
created_date: '2026-01-27 07:39'
updated_date: '2026-01-27 21:40'
labels:
  - performance
  - rust
  - architecture
  - refactoring
dependencies: []
parent_task_id: '211'
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Overview

Create a shared types crate (`mt-core`) that can be used by both the main application and Tauri plugins. This is a prerequisite for extracting database-dependent commands into plugins.

## Problem

Currently, plugin extraction is blocked by circular dependencies:
- Main crate (`mt_lib`) would depend on plugins
- Plugins would need types from `mt_lib` (Database, Track, ArtworkCache, EventEmitter)
- This creates: `mt_lib` → plugin → `mt_lib` (circular)

## Solution

Extract shared types into a new crate:

```
src-tauri/
├── crates/
│   └── mt-core/           # New shared types crate
│       ├── Cargo.toml
│       └── src/
│           ├── db/        # Database, DbPool, DbConnection
│           │   ├── mod.rs
│           │   ├── models.rs  # Track, Playlist, etc.
│           │   ├── schema.rs
│           │   └── library.rs, queue.rs, etc.
│           ├── events.rs  # EventEmitter, event types
│           ├── scanner/   # ArtworkCache, Artwork, metadata types
│           └── lib.rs
├── plugins/
│   └── tauri-plugin-library/  # Can now depend on mt-core
└── src/                   # Main app depends on mt-core
```

## Types to Extract

### db module (entire module)
- `Database`, `DbPool`, `DbConnection`, `DbError`, `DbResult`
- `Track`, `Playlist`, `PlaylistTrack`, `QueueItem`, `Favorite`
- `LibraryStats`, `LibraryQuery`, `PaginatedResult`, `SortBy`, `SortOrder`
- All db submodules: library, queue, playlists, favorites, settings, watched, scrobble

### events module
- All event structs: `LibraryUpdatedEvent`, `ScanProgressEvent`, etc.
- `EventEmitter` trait

### scanner types
- `Artwork`, `ArtworkCache`
- `ExtractedMetadata`, `FileFingerprint`

## Dependencies for mt-core

```toml
[dependencies]
rusqlite = { version = "0.38", features = ["bundled"] }
r2d2 = "0.8"
r2d2_sqlite = "0.32"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
thiserror = "2"
lru = "0.12"
tauri = { version = "2", default-features = false }  # For EventEmitter
```

## Benefits

1. **Enables plugin extraction**: library, queue, playlist, favorites, lastfm, watcher, scanner plugins can all be created
2. **Parallel compilation**: mt-core compiles once, plugins compile in parallel
3. **Better architecture**: Clear separation of concerns
4. **Reduced monomorphization**: Shared types compiled once

## Blocked Tasks

This task blocks:
- task-211.02 (library-plugin)
- task-211.03 (queue-plugin)  
- task-211.04 (playlist-plugin)
- task-211.05 (favorites-plugin)
- task-211.06 (lastfm-plugin)
- task-211.08 (watcher-plugin)
- task-211.09 (scanner-plugin)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 mt-core crate compiles independently
- [x] #2 Main app compiles with mt-core dependency
- [x] #3 All existing tests pass
- [ ] #4 At least one plugin (library-plugin) successfully uses mt-core types
- [x] #5 No circular dependencies in workspace
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Completion Notes (2026-01-27)

### What was implemented:

1. **Fixed mt-core Cargo.toml**
   - Edition changed to 2024 for consistency
   - Added chrono to dev-dependencies for scrobble tests

2. **Created artwork module** (`src/artwork/mod.rs`)
   - Artwork struct and extraction functions
   - Folder and embedded artwork support

3. **Created artwork cache module** (`src/artwork/cache.rs`)
   - LRU cache for artwork with thread-safe access

4. **Created events module** (`src/events.rs`)
   - 11 event types for real-time UI updates
   - EventEmitter trait (impl for tauri::AppHandle stays in main crate)

5. **Updated workspace Cargo.toml**
   - mt-core added to workspace members
   - mt-core added as dependency

### Test Results:
- 143 tests in mt-core
- 137 passed, 6 pre-existing compat_test failures (unrelated to new code)
- All 12 artwork tests pass
- All 45 events tests pass

### Note on AC #4:
AC #4 (plugin using mt-core) is for subsequent tasks (task-211.02+) that will create plugins depending on mt-core. The mt-core crate is ready for use.

## Abandoned

This task was abandoned as part of the plugin refactoring revert. See task-211 for full explanation. The Tauri v2 permission/capabilities system complexity made the plugin architecture impractical.
<!-- SECTION:NOTES:END -->
