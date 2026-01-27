---
id: task-195
title: Fix 6 failing E2E tests in library.spec.js and sidebar.spec.js
status: Done
assignee: []
created_date: '2026-01-23 05:20'
updated_date: '2026-01-24 22:28'
labels:
  - testing
  - e2e
  - playwright
  - bug
dependencies: []
priority: medium
ordinal: 48382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
There are 6 pre-existing failing E2E tests related to playlist drag reordering and metadata editor navigation. These tests fail consistently and need investigation and fixes.

**Failing Tests:**

1. `library.spec.js:1770` - Playlist Feature Parity - Library Browser (task-150) › AC#6: drag reorder in playlist view shows drag handle and sets state
2. `library.spec.js:2156` - Metadata Editor Navigation (task-166) › should show track position indicator with correct format
3. `library.spec.js:2181` - Metadata Editor Navigation (task-166) › should navigate to next track with ArrowRight key
4. `library.spec.js:2313` - Metadata Editor Navigation (task-166) › should navigate using arrow buttons
5. `library.spec.js:2375` - Metadata Editor Navigation (task-166) › arrow keys should work even when input is focused
6. `sidebar.spec.js:644` - Playlist Feature Parity (task-150) › dragging playlist should show opacity change

**Common Failure Pattern:**

The sidebar.spec.js test expects `opacity-50` class during drag but the element has different classes:
```
Expected substring: "opacity-50"
Received string: "w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-all duration-150 select-none hover:bg-muted/70 text-foreground/80 bg-card shadow-lg z-10 relative"
```

**Investigation Needed:**
- Check if drag state is being properly set in the sidebar component
- Verify the opacity class is conditionally applied based on drag state
- Review if the metadata editor navigation implementation matches test expectations
- Check if tests need updating vs implementation needs fixing
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All 6 failing tests pass
- [x] #2 No regressions in other tests
- [x] #3 Root cause documented in implementation notes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Root Causes and Fixes

### Test Failures

**1. sidebar.spec.js:644 - "dragging playlist should show opacity change"**
- **Root Cause**: Test error - checking wrong playlist
- **Details**: Test set `reorderDraggingIndex = 0` and then checked `sidebar-playlist-1`, which is at index 0 (the playlist being dragged). The opacity-50 class is applied to OTHER playlists via `isOtherPlaylistDragging(index)`, not the dragged playlist.
- **Fix**: Changed test to check `sidebar-playlist-2` (at index 1) instead of `sidebar-playlist-1`
- **File**: `app/frontend/tests/sidebar.spec.js:652-656`

**2. library.spec.js:1770 - "drag reorder in playlist view shows drag handle and sets state"**
- **Root Cause**: Test error - clicking wrong element
- **Details**: Test verified drag handle was visible but then clicked at a general position in the track row (`track1Box.x + 10`), not on the drag handle itself. The drag handle has `@mousedown="startPlaylistDrag(index, $event)"` which only triggers when the handle is clicked.
- **Fix**: Changed test to get drag handle's bounding box and click directly on it
- **File**: `app/frontend/tests/library.spec.js:1788-1791`

**3. library.spec.js:2156, 2181, 2313, 2375 - metadata editor navigation tests**
- **Root Cause**: Implementation bug - `currentTrackId` never initialized
- **Details**: When opening metadata editor with multiple tracks, `currentTrackId` was set to `null` and never initialized. This caused `currentBatchIndex` to return -1, which made `navIndicator` display "2 tracks" instead of "1 / 2".
- **Fix**: Initialize `currentTrackId` to first track in selection order after `loadMetadata()` completes
- **File**: `app/frontend/js/components/metadata-modal.js:110-113`

### Additional Fixes (Discovered During Testing)

**4. canNavigatePrev/canNavigateNext logic**
- **Root Cause**: Implementation bug - buttons didn't check current position
- **Details**: The getter methods only checked if navigation was enabled and batch had multiple tracks, but didn't check if we were at the first/last track. This caused prev button to be enabled at first track and next button to be enabled at last track.
- **Fix**: Updated getters to check `currentBatchIndex` position
  - `canNavigatePrev`: Check `currentBatchIndex > 0`
  - `canNavigateNext`: Check `currentBatchIndex < length - 1`
- **File**: `app/frontend/js/components/metadata-modal.js:70-76`

## Test Results

All 6 originally failing tests now pass:
- ✅ sidebar.spec.js:644 - dragging playlist should show opacity change
- ✅ library.spec.js:1770 - drag reorder in playlist view shows drag handle
- ✅ library.spec.js:2156 - should show track position indicator with correct format
- ✅ library.spec.js:2181 - should navigate to next track with ArrowRight key
- ✅ library.spec.js:2313 - should navigate using arrow buttons
- ✅ library.spec.js:2375 - arrow keys should work even when input is focused

Full test suite: **149/149 tests passing** (0 failures)
<!-- SECTION:NOTES:END -->
