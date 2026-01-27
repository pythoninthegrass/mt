---
id: task-211.07
title: Create settings-plugin for application settings commands
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
Extract application settings commands into a dedicated Tauri plugin.

## Commands to migrate (5 total)
- `settings_get_all`, `settings_get`, `settings_set`, `settings_update`, `settings_reset`

## Source files
- `src-tauri/src/commands/settings.rs`

## Benefits
- Small, focused plugin
- Isolated settings persistence
- Parallel compilation with other plugins
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Plugin compiles independently
- [ ] #2 All settings commands work via plugin
- [ ] #3 No regression in settings persistence
- [ ] #4 Plugin registered in lib.rs with .plugin()
<!-- AC:END -->
