---
id: task-211.01
title: Create audio-plugin for audio and media key commands
status: Done
assignee: []
created_date: '2026-01-27 04:22'
updated_date: '2026-01-27 21:39'
labels:
  - performance
  - rust
  - refactoring
  - plugin
dependencies: []
parent_task_id: '211'
priority: medium
ordinal: 13375
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extract audio playback and media key commands into a dedicated Tauri plugin.

## Commands to migrate (12 total)
- `audio_load`, `audio_play`, `audio_pause`, `audio_stop`, `audio_seek`
- `audio_set_volume`, `audio_get_volume`, `audio_get_status`
- `media_set_metadata`, `media_set_playing`, `media_set_paused`, `media_set_stopped`

## Source files
- `src-tauri/src/commands/audio.rs`
- `src-tauri/src/lib.rs` (media_* commands)

## Benefits
- Isolated monomorphization for audio IPC serialization
- Parallel compilation with other plugins
- Clear separation of audio concerns
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Plugin compiles independently
- [ ] #2 All audio commands work via plugin
- [ ] #3 No regression in audio playback functionality
- [ ] #4 Plugin registered in lib.rs with .plugin()
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Abandoned (2026-01-27)

Plugin refactoring reverted due to Tauri v2 permission complexity. See parent task-211 for details.
<!-- SECTION:NOTES:END -->
