---
id: task-211.04
title: Create playlist-plugin for playlist management commands
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
ordinal: 16375
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extract playlist management commands into a dedicated Tauri plugin.

## Commands to migrate (10 total)
- `playlist_list`, `playlist_create`, `playlist_get`, `playlist_update`, `playlist_delete`
- `playlist_add_tracks`, `playlist_remove_track`, `playlist_reorder_tracks`
- `playlists_reorder`, `playlist_generate_name`

## Source files
- `src-tauri/src/commands/playlists.rs`

## Benefits
- Clear separation of playlist CRUD operations
- Isolated database access patterns
- Parallel compilation with other plugins
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Plugin compiles independently
- [ ] #2 All playlist commands work via plugin
- [ ] #3 No regression in playlist CRUD operations
- [ ] #4 Plugin registered in lib.rs with .plugin()
<!-- AC:END -->
