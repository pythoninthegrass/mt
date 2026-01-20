---
id: task-178
title: Fix drag-and-drop from library to playlist (broken drop + premature cursor)
status: To Do
assignee: []
created_date: '2026-01-20 07:24'
labels:
  - bug
  - frontend
  - playlists
  - drag-drop
  - ux
dependencies:
  - task-150
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Bug Report

Drag-and-drop from music library to sidebar playlists is broken despite being marked complete in task-150.

### Observed Behavior

1. **Premature copy cursor**: The green plus sign (copy cursor) appears immediately when drag begins, before hovering over any playlist. It should only appear when hovering over a valid drop target (playlist).

2. **Drop doesn't append tracks**: When a track is dropped onto a playlist, it is NOT added to the playlist. The drop handler either isn't triggering or the API call is failing silently.

### Expected Behavior

1. Drag cursor should show default/move cursor during drag
2. Copy cursor (green plus) should only appear when hovering over a playlist in sidebar
3. Dropping on a playlist should call `api.playlists.addTracks()` and show success toast
4. Playlist should refresh to show the newly added track(s)

### Root Cause Analysis

**Issue 1 - Premature cursor:**
In `library-browser.js` line 854:
```js
event.dataTransfer.effectAllowed = 'copy';
```
This sets the allowed effect globally at drag start. The cursor appearance is controlled by `dropEffect` which should only be set to `'copy'` in `handlePlaylistDragOver` when over a valid target. However, browsers may show the copy cursor based on `effectAllowed` alone.

**Potential fix:** Use `effectAllowed = 'copyMove'` or `'all'` at drag start, then set `dropEffect = 'copy'` only in valid drop zones, and `dropEffect = 'none'` elsewhere.

**Issue 2 - Drop not working:**
Possible causes:
- `handlePlaylistDrop` not being called (event not reaching handler)
- `event.dataTransfer.getData()` returning empty string
- `playlist.playlistId` is undefined/wrong format
- API call failing silently (no error logging)
- `reorderDraggingIndex !== null` guard blocking the handler

### Current Implementation

**Drag start** (`library-browser.js:846-865`):
```js
handleTrackDragStart(event, track) {
  // Select track if not already selected
  if (!this.selectedTracks.has(track.id)) {
    this.selectedTracks.clear();
    this.selectedTracks.add(track.id);
  }
  
  const trackIds = Array.from(this.selectedTracks);
  event.dataTransfer.setData('application/json', JSON.stringify(trackIds));
  event.dataTransfer.effectAllowed = 'copy';  // <-- Issue: sets cursor too early
  
  // Custom drag image
  const dragEl = document.createElement('div');
  // ...
}
```

**Drop handler** (`sidebar.js:279-302`):
```js
async handlePlaylistDrop(event, playlist) {
  if (this.reorderDraggingIndex !== null) return;  // <-- Could block if state is stale
  event.preventDefault();
  this.dragOverPlaylistId = null;
  
  const trackIdsJson = event.dataTransfer.getData('application/json');
  if (!trackIdsJson) return;  // <-- Silent return, no logging
  
  try {
    const trackIds = JSON.parse(trackIdsJson);
    if (!Array.isArray(trackIds) || trackIds.length === 0) return;  // <-- Silent return
    
    const result = await api.playlists.addTracks(playlist.playlistId, trackIds);
    // ... toast on success
  } catch (error) {
    console.error('Failed to add tracks to playlist:', error);
    // ...
  }
}
```

**HTML binding** (`index.html:364-366`):
```html
@dragover="handlePlaylistDragOver($event, playlist)"
@dragleave="handlePlaylistDragLeave()"
@drop="handlePlaylistDrop($event, playlist)"
```

### Test Gap

The existing test (`sidebar.spec.js:560-573`) uses Playwright's `dragTo()`:
```js
await trackRow.dragTo(playlistButton);
const addTracksCalls = findApiCalls(playlistState, 'POST', '/playlists/1/tracks');
expect(addTracksCalls.length).toBeGreaterThan(0);
```

This test may pass because Playwright's synthetic drag events don't perfectly match browser behavior. The test doesn't verify:
- The actual dataTransfer content is correct
- The drop handler receives the data
- The API response is handled correctly
- The UI updates after the drop

### Files to Modify

| File | Changes |
|------|---------|
| `app/frontend/js/components/library-browser.js` | Fix `effectAllowed`, add logging to drag handlers |
| `app/frontend/js/components/sidebar.js` | Add comprehensive logging to drop handler, verify `playlist.playlistId` |
| `app/frontend/tests/sidebar.spec.js` | Add more granular drag-drop tests with manual event dispatch |
| `app/frontend/tests/library.spec.js` | Add tests for drag start data format |

### Debugging Steps

1. Add `console.log` at each step of drag-drop flow:
   - `handleTrackDragStart`: Log track IDs being set
   - `handlePlaylistDragOver`: Log when hover detected
   - `handlePlaylistDragLeave`: Log when hover ends  
   - `handlePlaylistDrop`: Log received data, playlist ID, API call result

2. Check browser DevTools Network tab for API call when dropping

3. Verify `playlist.playlistId` matches what backend expects (number vs string?)

4. Test with manual drag-drop in Tauri app (not just Playwright)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Drag cursor shows default/move icon when dragging starts (not copy/plus)
- [ ] #2 Copy cursor (green plus) appears ONLY when hovering over a sidebar playlist
- [ ] #3 Dropping track(s) on playlist successfully adds them via API
- [ ] #4 Success toast appears after drop confirming tracks were added
- [ ] #5 Playlist track count updates after successful drop
- [ ] #6 Console logs added to all drag-drop handlers for debugging
- [ ] #7 Playwright test verifies actual dataTransfer content, not just API mock
- [ ] #8 Manual testing in Tauri confirms end-to-end functionality works
<!-- AC:END -->
