---
id: task-211.06
title: Create lastfm-plugin for Last.fm integration commands
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
