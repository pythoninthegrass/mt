---
id: task-211.02
title: Create library-plugin for library management commands
status: In Progress
assignee: []
created_date: '2026-01-27 04:22'
updated_date: '2026-01-27 08:03'
labels:
  - performance
  - rust
  - refactoring
  - plugin
dependencies:
  - task-211.11
parent_task_id: '211'
priority: medium
ordinal: 14375
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extract library management commands into a dedicated Tauri plugin.

## Commands to migrate (14 total)
- `library_get_all`, `library_get_stats`, `library_get_track`
- `library_get_artwork`, `library_get_artwork_url`
- `library_delete_track`, `library_rescan_track`, `library_update_play_count`
- `library_get_missing`, `library_locate_track`, `library_check_status`
- `library_mark_missing`, `library_mark_present`, `library_reconcile_scan`

## Source files
- `src-tauri/src/library/commands.rs`

## Benefits
- Largest command group - significant monomorphization reduction
- Isolated database access patterns
- Parallel compilation with other plugins
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Plugin compiles independently
- [ ] #2 All library commands work via plugin
- [ ] #3 No regression in library browsing/management
- [ ] #4 Plugin registered in lib.rs with .plugin()
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Architectural Blocker (2026-01-27)

### Problem: Circular Dependency

The library-plugin cannot be extracted using the same pattern as audio-plugin or settings-plugin because:

1. **Audio-plugin pattern**: Self-contained - plugin defines its own types (`AudioState`, `AudioEngine`), main app creates and manages them via `app.manage()`

2. **Settings-plugin pattern**: Uses external Tauri plugin (`tauri_plugin_store`) - no dependency on main crate types

3. **Library-plugin requirement**: Commands need `State<Database>`, `State<ArtworkCache>`, and access to `db::library`, `events::EventEmitter`, `scanner::metadata` - all defined in main crate (`mt_lib`)

### Failed Approach

An incomplete skeleton at `src-tauri/plugins/tauri-plugin-library/Cargo.toml` exists with:
```toml
mt_lib = { path = "../.." }
```

This creates a **circular dependency**:
- `mt_lib` → depends on → `tauri-plugin-library`
- `tauri-plugin-library` → depends on → `mt_lib`

### Solutions (Ordered by Effort)

#### Option A: Create `mt-core` shared crate (Recommended)
Extract shared types into a new crate that both main app and plugins can depend on:

```
mt-core/              # New shared types crate
├── src/
│   ├── db/          # Database, DbConnection, models
│   ├── events/      # EventEmitter, event types
│   ├── scanner/     # ArtworkCache, metadata types
│   └── lib.rs

mt_lib/               # Main app
├── depends on: mt-core, tauri-plugin-library

tauri-plugin-library/ # Library plugin
├── depends on: mt-core (NOT mt_lib)
```

**Effort**: High (~4-8 hours)
**Benefit**: Enables all command plugins, better architecture

#### Option B: Keep library commands in main crate
Accept that library commands can't be extracted without the shared-types refactor. Focus on other plugins that CAN be extracted:

- ✅ audio-plugin (done, self-contained)
- ✅ settings-plugin (done, uses tauri_plugin_store)
- ❌ library-plugin (blocked)
- ❌ queue-plugin (blocked - needs Database)
- ❌ playlist-plugin (blocked - needs Database)
- ❌ favorites-plugin (blocked - needs Database)
- ❌ lastfm-plugin (blocked - needs Database)
- ❌ watcher-plugin (blocked - needs Database)
- ❌ scanner-plugin (blocked - needs Database)
- ⚠️ core-plugin (partially blocked)

**Effort**: Low (just documentation)
**Benefit**: None for incremental compile times

#### Option C: Move database layer into library-plugin
Make library-plugin own the database types. Other plugins would depend on library-plugin for database access.

**Effort**: Medium-High
**Benefit**: Enables library-plugin, but other plugins still blocked

### Recommendation

Create a new parent task for "Extract shared types into mt-core crate" as a prerequisite for all database-dependent plugin extractions. Mark tasks 211.02-211.06, 211.08-211.10 as blocked by this new task.

### Cleanup

Delete the broken skeleton:
- `src-tauri/plugins/tauri-plugin-library/Cargo.toml`
<!-- SECTION:NOTES:END -->
