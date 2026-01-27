---
id: task-211.06
title: Create lastfm-plugin for Last.fm integration commands
status: Done
assignee: []
created_date: '2026-01-27 04:22'
updated_date: '2026-01-27 21:39'
labels:
  - performance
  - rust
  - refactoring
  - plugin
dependencies:
  - task-211.11
parent_task_id: '211'
priority: low
ordinal: 19375
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extract Last.fm scrobbling and integration commands into a dedicated Tauri plugin.

## Commands to migrate (10 total)
- `lastfm_get_settings`, `lastfm_update_settings`
- `lastfm_get_auth_url`, `lastfm_auth_callback`, `lastfm_disconnect`
- `lastfm_now_playing`, `lastfm_scrobble`
- `lastfm_queue_status`, `lastfm_queue_retry`, `lastfm_import_loved_tracks`

## Source files
- `src-tauri/src/commands/lastfm.rs`
- `src-tauri/src/lastfm/` module

## Benefits
- Isolated external API integration
- Optional feature candidate (could be feature-gated later)
- Parallel compilation with other plugins
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Plugin compiles independently
- [ ] #2 All Last.fm commands work via plugin
- [ ] #3 No regression in scrobbling/auth flow
- [ ] #4 Plugin registered in lib.rs with .plugin()
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Blocked by task-211.11

This task requires shared types (Database, scrobble types, etc.) to be extracted into mt-core crate first.

## Abandoned (2026-01-27)

Plugin refactoring reverted due to Tauri v2 permission complexity. See parent task-211 for details.
<!-- SECTION:NOTES:END -->
