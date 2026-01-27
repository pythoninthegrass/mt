---
id: task-211.09
title: Create scanner-plugin for music scanning commands
status: Done
assignee: []
created_date: '2026-01-27 04:22'
updated_date: '2026-01-27 21:40'
labels:
  - performance
  - rust
  - refactoring
  - plugin
dependencies:
  - task-211.11
parent_task_id: '211'
priority: low
ordinal: 21375
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extract music file scanning and metadata extraction commands into a dedicated Tauri plugin.

## Commands to migrate (5 total)
- `scan_paths_to_library`, `scan_paths_metadata`
- `extract_file_metadata`
- `get_track_artwork`, `get_track_artwork_url`

## Source files
- `src-tauri/src/scanner/commands.rs`
- `src-tauri/src/scanner/` module

## Benefits
- Isolated scanning/metadata logic (uses lofty heavily)
- Clear separation of import concerns
- Parallel compilation with other plugins
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Plugin compiles independently
- [ ] #2 All scanner commands work via plugin
- [ ] #3 No regression in music importing/scanning
- [ ] #4 Plugin registered in lib.rs with .plugin()
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Blocked by task-211.11

This task requires shared types (Database, Track, ArtworkCache, etc.) to be extracted into mt-core crate first.

## Abandoned

This task was abandoned as part of the plugin refactoring revert. See task-211 for full explanation. The Tauri v2 permission/capabilities system complexity made the plugin architecture impractical.
<!-- SECTION:NOTES:END -->
