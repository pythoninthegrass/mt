---
id: task-200
title: Fix shuffle navigation regression - prev button should traverse play history
status: In Progress
assignee: []
created_date: '2026-01-25 04:49'
updated_date: '2026-01-25 05:40'
labels:
  - bug
  - regression
  - queue
  - shuffle
  - Phase 2
dependencies: []
priority: high
ordinal: 500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem

After Phase 2 implementation, hitting the prev button twice no longer goes back to previously played tracks when shuffle is enabled. The current behavior decrements `currentIndex` in the shuffled queue array, which gives the previous track in shuffled order rather than the previously *played* track.

**Expected behavior:** Maintain a play history so that prev button traverses backward through the actual playback history, regardless of shuffle mode.

**Current behavior:** `playPrevious()` in queue.js (lines 394-415) simply does `prevIndex = currentIndex - 1`, which navigates through the shuffled array position rather than play history.

## Root Cause

The queue store maintains tracks in play order (physically reordered when shuffle is enabled) but doesn't track which tracks were actually played. This breaks the expected "back button" behavior that users rely on.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Add play history tracking to queue store (array of previously played indices/track IDs)
- [x] #2 Update playPrevious() to pop from history when available
- [x] #3 Update playNext() to push current track to history before advancing
- [x] #4 Clear history appropriately (on shuffle toggle, queue clear, manual queue jumps)
- [x] #5 Handle edge cases: restart track >3s, loop modes, empty queue
- [ ] #6 Verify with manual testing: play 5 shuffled tracks, hit prev 5 times, should go back through same 5 tracks
- [x] #7 Add Playwright test for shuffle navigation history

## Technical Approach

1. Add `_playHistory: []` to queue store state
2. Push `currentIndex` to history in `playNext()` before advancing
3. In `playPrevious()`: if history exists, pop and play that index; otherwise fall back to `currentIndex - 1`
4. Clear history on: `toggleShuffle()`, `clear()`, manual `playIndex()` calls
5. Limit history size (e.g., last 100 tracks) to prevent memory issues

## Files to Modify

- `app/frontend/js/stores/queue.js` - Add history tracking and update navigation methods
- `app/frontend/tests/queue.spec.js` - Add tests for history navigation

## Related

This is a regression introduced after implementing Phase 2 state consolidation. The original Python/Tkinter implementation maintained play history correctly.
<!-- SECTION:DESCRIPTION:END -->

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Complete

### Changes Made

**queue.js store:**
- Added `_playHistory` array and `_maxHistorySize: 100` to track play order
- Modified `playNext()` to push current index to history before advancing
- Modified `playPrevious()` to pop from history when available (with >3s restart logic)
- Added `_pushToHistory()` and `_popFromHistory()` helper methods
- Clear history on: shuffle toggle, queue clear, manual `playIndex()` calls
- Updated `_initPlaybackState()` to reset history on app start

**queue.spec.js tests:**
- Added comprehensive test suite for shuffle navigation history
- Tests cover: history traversal, clearing on shuffle toggle, clearing on manual selection, clearing on queue clear, >3s restart behavior, 100-track limit

### Commits
- `7dcad78` - feat: add play history tracking for shuffle navigation
- `30ab5c9` - test: add Playwright tests for shuffle navigation history

### Manual Testing Required

The Playwright tests require the full Tauri runtime with an actual music library loaded. To verify AC #6:

1. Run `task tauri:dev` to start the application
2. Load a music library with multiple tracks
3. Enable shuffle mode
4. Play through 5-10 tracks (click next repeatedly)
5. Hit prev button repeatedly
6. **Expected:** Should traverse back through the exact same tracks in reverse order
7. **Expected:** After going back through history, hitting next should go forward again

### Edge Cases to Test Manually

1. **Restart track >3s:** Seek >3s into a track, hit prev → should restart track, not use history
2. **Shuffle toggle:** Enable shuffle, play tracks, toggle shuffle off → history should be cleared
3. **Manual track selection:** Build history, click a track in queue → history should be cleared
4. **Queue clear:** Build history, clear queue → history should be cleared
5. **Loop modes:** Verify history works correctly with loop=all and loop=one
<!-- SECTION:NOTES:END -->
