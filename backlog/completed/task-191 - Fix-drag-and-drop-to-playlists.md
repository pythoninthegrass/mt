---
id: task-191
title: Fix drag and drop to playlists
status: Done
assignee: []
created_date: '2026-01-22 01:14'
updated_date: '2026-01-22 16:20'
labels:
  - bug
  - frontend
  - playlists
  - drag-drop
dependencies: []
priority: medium
ordinal: 328.125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Drag and drop tracks to playlists in the sidebar is not working correctly. The context menu "Add to playlist" functionality works as expected, so the issue is isolated to the drag and drop interaction.

**Current Behavior:**
- Context menu > Add to playlist: Works correctly
- Drag and drop tracks to playlist in sidebar: Not working

**Expected Behavior:**
- Dragging tracks from the library browser to a playlist in the sidebar should add those tracks to the playlist

**Investigation Areas:**
- Check drag event handlers in sidebar playlist items
- Verify drop zone detection and highlighting
- Check if playlist_add_tracks command is being called on drop
- Review drag data transfer format compatibility
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Drag and drop tracks from library to sidebar playlists works
- [x] #2 Visual feedback shown when dragging over valid drop target
- [x] #3 Multiple track selection drag and drop works
- [ ] #4 E2E test coverage for playlist drag and drop
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Root Cause

In Tauri webview, `event.dataTransfer.getData()` may return empty during drag-drop operations, even though `setData()` was called in `dragstart`. A global variable workaround (`window._mtDraggedTrackIds`) was already being set in `handleTrackDragStart` but was not being used in the sidebar's drop handlers.

## Fix

Modified `app/frontend/js/components/sidebar.js`:

1. **`handlePlaylistDragOver`**: Check both `dataTransfer.types` AND `window._mtDraggedTrackIds` to detect valid track drags for visual feedback

2. **`handlePlaylistDrop`**: Fall back to `window._mtDraggedTrackIds` if `dataTransfer.getData()` returns empty

## Visual Feedback

Visual feedback (ring highlight) was already implemented in the HTML template:
```
isPlaylistDragOver(playlist.playlistId) ? 'ring-2 ring-primary ring-inset bg-primary/10' : ''
```

It wasn't working because `dragOverPlaylistId` wasn't being set when `dataTransfer.types` was empty.
<!-- SECTION:NOTES:END -->
