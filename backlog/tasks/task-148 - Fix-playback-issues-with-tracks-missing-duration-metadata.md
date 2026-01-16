---
id: task-148
title: Fix playback issues with tracks missing duration metadata
status: To Do
assignee: []
created_date: '2026-01-16 05:31'
labels:
  - bug
  - playback
  - critical
  - tauri-migration
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem
Tracks 182-185 (including "Une Vie à Peindre" at 11:00) exhibit multiple issues:

1. **No total track time displayed** - Duration shows as empty/0 instead of actual length (e.g., 11:00)
2. **Shuffle state mismatch** - Shuffle is enabled even when icon shows toggled off
3. **Progress bar seek crashes app** - Manually clicking ahead on progress bar clears playback and freezes the entire app intermittently
4. **Root cause identified** - Issues only occur with tracks missing duration metadata

## Reproduction Steps
1. Navigate to tracks 182-185 in library
2. Observe missing duration in track list
3. Play one of these tracks
4. Try to seek using progress bar → app freezes

## Investigation Areas
- Check how duration is read from audio files (mutagen/backend)
- Check how missing duration is handled in frontend player store
- Check progress bar seek handler for division by zero or NaN issues
- Check shuffle state initialization vs UI binding
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Tracks display correct duration even if metadata is missing (fallback to audio element duration)
- [ ] #2 Shuffle icon state matches actual shuffle state
- [ ] #3 Seeking on progress bar works without crashing for all tracks
- [ ] #4 No app freeze when interacting with tracks missing metadata
<!-- AC:END -->
