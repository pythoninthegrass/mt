---
id: task-212
title: >-
  Loop doesn't jump back to start of library (first track by alphanumeric
  artist/album)
status: In Progress
assignee: []
created_date: '2026-01-27 07:36'
updated_date: '2026-01-27 07:39'
labels:
  - bug
  - playback
  - queue
  - frontend
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem

When playing the entire library with loop mode set to "all", after the last track finishes, playback does not restart from the first track in the expected order (alphanumeric by artist, then album).

## Current Behavior

When loop=all and the queue reaches the end (nextIndex >= items.length), the code in `queue.js` line 420-425:
```javascript
if (nextIndex >= this.items.length) {
  if (this.loop === 'all') {
    if (this.shuffle) {
      this._shuffleItems();
    }
    nextIndex = 0;
  }
}
```

This sets `nextIndex = 0` which plays whatever track is at index 0 of the current queue. However, the queue order depends on:
1. How tracks were added (play from library, add to queue, etc.)
2. Whether shuffle was previously toggled

## Expected Behavior

When looping the library, playback should restart from the first track in alphanumeric order by artist name, then album name, then track number - matching the library browser's default sort order.

## Root Cause Analysis Needed

Investigate:
1. Is the queue order preserved from library sort when "Play All" or similar is used?
2. Does the queue lose its original order after operations like shuffle toggle?
3. Should loop restart respect the original library ordering vs queue insertion order?

## Related Code

- `app/frontend/js/stores/queue.js` - playNext(), lines 418-430
- `app/frontend/js/components/library-browser.js` - how library adds tracks to queue
- `_originalOrder` preservation in queue store
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Loop=all restarts from first track in alphanumeric order (artist -> album -> track number)
- [ ] #2 Library order is preserved in queue when playing entire library
- [ ] #3 Test: Play library with loop=all, verify restart order matches library sort
<!-- AC:END -->
