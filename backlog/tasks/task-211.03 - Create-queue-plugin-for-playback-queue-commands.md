---
id: task-211.03
title: Create queue-plugin for playback queue commands
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
ordinal: 15375
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extract playback queue commands into a dedicated Tauri plugin.

## Commands to migrate (11 total)
- `queue_get`, `queue_add`, `queue_add_files`, `queue_remove`, `queue_clear`
- `queue_reorder`, `queue_shuffle`, `queue_get_playback_state`
- `queue_set_current_index`, `queue_set_shuffle`, `queue_set_loop`

## Source files
- `src-tauri/src/commands/queue.rs`

## Benefits
- Queue is a core feature with frequent changes
- Isolated state management
- Parallel compilation with other plugins
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Plugin compiles independently
- [ ] #2 All queue commands work via plugin
- [ ] #3 No regression in queue/shuffle/loop behavior
- [ ] #4 Plugin registered in lib.rs with .plugin()
<!-- AC:END -->
