---
id: task-140
title: Fix double-click behavior to queue entire library (not filtered view)
status: To Do
assignee: []
created_date: '2026-01-16 04:03'
labels:
  - bug
  - queue
  - library
  - behavior-change
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem
Currently, double-clicking a track in the library view populates the queue with `library.filteredTracks` (the current filtered/searched view). The intended behavior is to queue the **entire library** regardless of current filters.

## Current behavior (in `library-browser.js` handleDoubleClick)
```javascript
async handleDoubleClick(track) {
  await this.queue.clear();
  await this.queue.add(this.library.filteredTracks, false);  // <-- uses filtered
  // ...
}
```

## Desired behavior
```javascript
async handleDoubleClick(track) {
  await this.queue.clear();
  await this.queue.add(this.library.tracks, false);  // <-- uses entire library
  // ...
}
```

## Why this matters
- Foundation for "Play Next" / "Play Last" context menu features
- Consistent user expectation: double-click plays from the whole library
- Search/filter is for *finding* tracks, not for *limiting* playback scope

## Files to modify
- `app/frontend/js/components/library-browser.js` - `handleDoubleClick()` method (~line 822)

## Acceptance Criteria
<!-- AC:BEGIN -->
- Double-click queues entire `library.tracks` not `filteredTracks`
- Queue index correctly points to clicked track within full library
- Existing tests pass (may need adjustment if they assumed filtered behavior)
- Manual verification: search for a track, double-click it, verify queue contains all library tracks
<!-- SECTION:DESCRIPTION:END -->

- [ ] #1 handleDoubleClick uses library.tracks instead of filteredTracks
- [ ] #2 Queue index correctly points to clicked track in full library
- [ ] #3 Existing Playwright tests pass or are updated
- [ ] #4 Manual verification passes
<!-- AC:END -->
