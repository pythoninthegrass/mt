---
id: task-211.09
title: Create scanner-plugin for music scanning commands
status: To Do
assignee: []
created_date: '2026-01-27 04:22'
labels:
  - performance
  - rust
  - refactoring
  - plugin
dependencies: []
parent_task_id: '211'
priority: low
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
