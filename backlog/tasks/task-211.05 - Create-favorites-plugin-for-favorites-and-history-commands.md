---
id: task-211.05
title: Create favorites-plugin for favorites and history commands
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
Extract favorites and listening history commands into a dedicated Tauri plugin.

## Commands to migrate (7 total)
- `favorites_get`, `favorites_check`, `favorites_add`, `favorites_remove`
- `favorites_get_top25`, `favorites_get_recently_played`, `favorites_get_recently_added`

## Source files
- `src-tauri/src/commands/favorites.rs`

## Benefits
- Small, focused plugin
- Isolated favorites/history logic
- Parallel compilation with other plugins
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Plugin compiles independently
- [ ] #2 All favorites commands work via plugin
- [ ] #3 No regression in favorites/history features
- [ ] #4 Plugin registered in lib.rs with .plugin()
<!-- AC:END -->
