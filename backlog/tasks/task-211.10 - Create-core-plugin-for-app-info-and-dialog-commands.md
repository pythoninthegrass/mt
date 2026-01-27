---
id: task-211.10
title: Create core-plugin for app info and dialog commands
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
Extract core application commands (app info, dialogs, diagnostics) into a dedicated Tauri plugin.

## Commands to migrate (6 total)
- `app_get_info`, `export_diagnostics`
- `open_file_dialog`, `open_folder_dialog`, `open_add_music_dialog`
- `get_track_metadata`, `save_track_metadata`

## Source files
- `src-tauri/src/lib.rs` (app_*, export_*)
- `src-tauri/src/dialog.rs`
- `src-tauri/src/metadata.rs`

## Benefits
- Collects miscellaneous core commands
- Final plugin to complete the refactoring
- Parallel compilation with other plugins
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Plugin compiles independently
- [ ] #2 All core commands work via plugin
- [ ] #3 No regression in app info/dialogs
- [ ] #4 Plugin registered in lib.rs with .plugin()
<!-- AC:END -->
