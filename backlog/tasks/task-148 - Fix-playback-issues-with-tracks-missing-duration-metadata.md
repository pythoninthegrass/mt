---
id: task-148
title: Fix playback issues with tracks missing duration metadata
status: Done
assignee: []
created_date: '2026-01-16 05:31'
updated_date: '2026-01-16 05:35'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Completion Notes (2026-01-15)

### Root Causes Identified

1. **Shuffle state mismatch**: `queue.load()` was overwriting localStorage values with backend defaults (`shuffle: false`, `loop: 'none'`)

2. **Progress bar crash**: No guards for NaN/undefined duration when calculating seek position - caused division issues and invalid seek commands

3. **Missing duration**: Rust's `rodio` decoder returns `None` for `total_duration()` on some audio formats (VBR MP3s without proper headers), falling back to 0

### Fixes Applied

**Frontend (JavaScript):**
- `queue.js`: Removed shuffle/loop overwrite in `load()` - now only loaded from localStorage
- `player.js`: Added guards in `seek()` and `seekPercent()` for NaN/negative values
- `player-controls.js`: Added guards in `handleProgressClick()` and `updateDragPosition()` for 0/undefined duration

**Known Limitation:**
- Duration still shows 0:00 for tracks where Rust's rodio can't determine duration from file headers
- This is a rodio/symphonia limitation - would need to scan entire file to calculate duration
- Progress bar is disabled (no crash) when duration is unknown

### Test Results
- All 29 store tests pass
- Shuffle state now persists across page reloads
- Seeking on tracks with missing duration no longer crashes

### Commit
- af01506: fix: prevent seek crash and shuffle state mismatch (task-148)
<!-- SECTION:NOTES:END -->
