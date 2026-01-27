---
id: task-213
title: Shuffle enqueues playing track as second track (plays twice)
status: In Progress
assignee: []
created_date: '2026-01-27 07:36'
updated_date: '2026-01-27 21:39'
labels:
  - bug
  - playback
  - queue
  - shuffle
  - frontend
dependencies: []
priority: medium
ordinal: 17375
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem

When enabling shuffle while a track is playing, the currently playing track appears both at index 0 (where it's moved to preserve playback) AND somewhere else in the shuffled queue, causing it to play twice.

## Current Behavior

In `queue.js` `_shuffleItems()` (lines 530-548):
```javascript
_shuffleItems() {
  if (this.items.length < 2) return;

  const currentTrack = this.currentIndex >= 0 ? this.items[this.currentIndex] : null;
  const otherTracks = currentTrack
    ? this.items.filter((_, i) => i !== this.currentIndex)
    : [...this.items];

  for (let i = otherTracks.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [otherTracks[i], otherTracks[j]] = [otherTracks[j], otherTracks[i]];
  }

  if (currentTrack) {
    this.items = [currentTrack, ...otherTracks];
    this.currentIndex = 0;
  } else {
    this.items = otherTracks;
  }
}
```

The logic correctly:
1. Filters out the current track from otherTracks using index comparison
2. Shuffles the remaining tracks
3. Prepends the current track to the shuffled list

## Suspected Issue

The bug may occur when:
1. Track reference comparison fails (different object instances for same track)
2. `currentIndex` is -1 or invalid, causing currentTrack to be null and not filtered
3. Race condition during toggle where currentIndex changes mid-operation
4. The bug might be in the backend `queue_shuffle` command rather than frontend

## Related Code

- `app/frontend/js/stores/queue.js` - `_shuffleItems()`, `toggleShuffle()`
- `src-tauri/src/commands/queue.rs` - `queue_shuffle()` (lines 173-219)
- Property tests in `queue.props.test.js` line 120: "shuffle with current track moves it to index 0"

## Reproduction Steps

1. Add multiple tracks to queue
2. Play any track
3. Enable shuffle
4. Observe queue - current track should be at index 0 only, not duplicated
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Current track appears exactly once in queue after shuffle
- [ ] #2 Current track is at index 0 after shuffle
- [ ] #3 No duplicate track IDs in shuffled queue
- [ ] #4 Test: Enable shuffle during playback, verify track count unchanged and no duplicates
<!-- AC:END -->
