---
id: task-211.02
title: Create library-plugin for library management commands
status: In Progress
assignee: []
created_date: '2026-01-27 04:22'
updated_date: '2026-01-27 04:23'
labels:
  - performance
  - rust
  - refactoring
  - plugin
dependencies: []
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
