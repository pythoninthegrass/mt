---
id: task-211.07
title: Create settings-plugin for application settings commands
status: Done
assignee: []
created_date: '2026-01-27 04:22'
updated_date: '2026-01-27 07:17'
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
- [x] #1 Plugin compiles independently
- [x] #2 All settings commands work via plugin
- [x] #3 No regression in settings persistence
- [x] #4 Plugin registered in lib.rs with .plugin()
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Complete (2026-01-27)

### Files Created
- `src-tauri/plugins/tauri-plugin-settings/Cargo.toml` - Plugin manifest
- `src-tauri/plugins/tauri-plugin-settings/build.rs` - Permission generation
- `src-tauri/plugins/tauri-plugin-settings/permissions/default.toml` - Default permissions
- `src-tauri/plugins/tauri-plugin-settings/src/lib.rs` - Plugin init with command registration
- `src-tauri/plugins/tauri-plugin-settings/src/commands.rs` - 5 settings commands
- `src-tauri/plugins/tauri-plugin-settings/src/models.rs` - Data models

### Files Modified
- `src-tauri/Cargo.toml` - Added plugin to workspace and dependencies
- `src-tauri/src/lib.rs` - Registered plugin, removed settings commands from invoke_handler
- `src-tauri/src/commands/mod.rs` - Removed settings module and exports

### Files Deleted
- `src-tauri/src/commands/settings.rs` - Moved to plugin

### Verification
- Plugin compiles independently: `cargo check --package tauri-plugin-settings` - PASS
- Main app compiles: `cargo check` - PASS
- Plugin tests pass: 2 tests passed
- No new clippy warnings in plugin
- Pre-existing db::compat_test failures (6 tests) unrelated to changes
<!-- SECTION:NOTES:END -->
