---
id: task-118
title: Fix playback controls wiring - method names and track shape mismatches
status: Done
assignee: []
created_date: '2026-01-13 23:44'
updated_date: '2026-01-13 23:45'
labels:
  - frontend
  - bug
  - playback
  - tauri-migration
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Playback controls (play/pause, prev, next, double-click to play) are not working due to several wiring issues between UI components, Alpine stores, and backend track data shape.

## Root Causes

### 1. Track shape mismatch (`filepath` vs `path`)
- Backend API returns tracks with `filepath` property
- Player store's `playTrack()` expects `track.path`
- Result: `track.path` is undefined → early return → no playback

### 2. Method name mismatches
- `playerControls.togglePlay()` calls `player.togglePlay()` but store method is `toggle()`
- `playerControls.previous()` calls `player.previous()` which doesn't exist
- `playerControls.next()` calls `player.next()` which doesn't exist
- Queue store calls `player.play(track)` but method is `playTrack(track)`

## Implementation Plan (Two Atomic Commits)

### Commit 1: Fix track shape - normalize filepath to path
- Update `playTrack()` in player store to use `track.filepath || track.path`
- Ensures backward compatibility if any code uses `path`

### Commit 2: Fix method name mismatches
- Rename `player.toggle()` to `player.togglePlay()` (or update component call)
- Add `player.previous()` that delegates to `queue.playPrevious()`
- Add `player.next()` that delegates to `queue.playNext()`
- Fix queue store to call `playTrack()` instead of `play()`

## Verification
After fix:
- Double-click track in library → plays immediately
- Play button → toggles play/pause
- Prev/Next buttons → navigate queue and play correct track
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Double-clicking a track in the library starts playback
- [x] #2 Play/pause button toggles playback state
- [x] #3 Previous button plays previous track (or restarts if >3s into track)
- [x] #4 Next button plays next track in queue
- [x] #5 All playback controls work with shuffle and loop modes
<!-- AC:END -->
