---
id: task-130
title: Fix shuffle playback previous track navigation getting stuck
status: Done
assignee: []
created_date: '2026-01-14 06:10'
updated_date: '2026-01-24 22:28'
labels:
  - bug
  - playback
  - shuffle
  - queue
dependencies: []
priority: medium
ordinal: 73382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Shuffle playback has issues navigating to previous tracks. The shuffled queue appears to be non-deterministic, causing the "previous track" functionality to get stuck at certain shuffled tracks.

**Problem**: When shuffle is enabled and the user navigates backwards through previously played tracks, the navigation eventually gets stuck at a shuffled track and cannot go further back.

**Expected Behavior**: Users should be able to navigate backwards through all previously played tracks in the order they were actually played, regardless of shuffle mode.

**Actual Behavior**: After skipping forward a few times with shuffle enabled, attempting to go back through the history eventually gets stuck at a certain track.

## Reproduction Steps

1. Start playing a track from the library
2. Enable shuffle mode
3. Skip forward 1-3 times using the "Next" button
4. Attempt to go back using the "Previous" button repeatedly
5. **Bug**: Navigation gets stuck at a shuffled track and cannot go further back

## Technical Notes

The issue suggests the shuffle implementation may be:
- Regenerating the shuffle order on each navigation instead of maintaining a history
- Not properly tracking the playback history stack
- Using a non-deterministic shuffle that doesn't preserve the "played" order
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Previous track navigation works correctly through entire playback history when shuffle is enabled
- [x] #2 Shuffle history is deterministic - the order of previously played tracks is preserved
- [x] #3 User can navigate back to the first track played in the session
- [x] #4 Forward navigation (next) after going back maintains correct shuffle behavior
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Root Cause Analysis

The bug was in the interaction between `playPrevious()` and `playIndex()` in `queue.js`:

1. `playPrevious()` correctly popped the current track from `_shuffleHistory` and got the previous index
2. But then it called `playIndex(prevIndex)` which **pushed the previous index back onto the history**
3. This created a loop where going back would keep bouncing between the same two tracks

**Example of the bug:**
- History: [0, 5, 3, 7] (current = 7)
- User presses "Previous"
- `playPrevious()` pops 7, history becomes [0, 5, 3], prevIndex = 3
- `playIndex(3)` pushes 3 back: history becomes [0, 5, 3, 3]
- User presses "Previous" again → gets stuck at index 3

## Solution

Added an `addToHistory` parameter to `playIndex()` (default: true) and pass `false` when calling from `playPrevious()` during shuffle mode backward navigation.
<!-- SECTION:PLAN:END -->
