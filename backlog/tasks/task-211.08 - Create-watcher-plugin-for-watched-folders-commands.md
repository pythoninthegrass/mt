---
id: task-211.08
title: Create watcher-plugin for watched folders commands
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
Extract watched folders and filesystem monitoring commands into a dedicated Tauri plugin.

## Commands to migrate (7 total)
- `watched_folders_list`, `watched_folders_get`, `watched_folders_add`
- `watched_folders_update`, `watched_folders_remove`
- `watched_folders_rescan`, `watched_folders_status`

## Source files
- `src-tauri/src/watcher/mod.rs`

## Benefits
- Isolated filesystem watching logic
- Clear separation of folder monitoring concerns
- Parallel compilation with other plugins
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Plugin compiles independently
- [ ] #2 All watcher commands work via plugin
- [ ] #3 No regression in folder watching/scanning
- [ ] #4 Plugin registered in lib.rs with .plugin()
<!-- AC:END -->
