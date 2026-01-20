---
id: task-179
title: Repurpose track number column for playlist ordering
status: In Progress
assignee: []
created_date: '2026-01-20 09:30'
updated_date: '2026-01-20 09:55'
labels:
  - enhancement
  - frontend
  - playlists
  - ux
dependencies: []
priority: medium
ordinal: 750
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Feature Request

The track number column (#) currently shows the track number from album metadata. In playlist view, this column should instead show the track's position within the playlist (1, 2, 3, etc.) to reflect the user-defined ordering.

### Current Behavior
- Track number column shows album track number (e.g., track 5 of an album shows "5")
- This is confusing in playlist context where order is user-defined

### Expected Behavior
- In **library view** (All, Artists, Albums): Show album track number from metadata
- In **playlist view**: Show playlist position (1-indexed sequential order)

### Implementation Notes
- The `library-browser.js` component needs to detect when viewing a playlist vs. library
- Column renderer for track number should check context and display appropriate value
- Playlist position should update after drag-reorder operations

### Related
- Playlist drag-reorder already exists (task-150)
- This enhances the UX by making playlist order visible
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Track number column shows album metadata track number in library view
- [ ] #2 Track number column shows sequential position (1, 2, 3...) in playlist view
- [ ] #3 Position numbers update correctly after drag-reorder in playlist
- [ ] #4 Column header tooltip/label reflects context ("#" vs "Position")
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- The `library-browser.js` component needs to detect when viewing a playlist vs. library
- Column renderer for track number should check context and display appropriate value
- Playlist position should update after drag-reorder operations

### Related
- Playlist drag-reorder already exists (task-150)
- This enhances the UX by making playlist order visible
<!-- SECTION:DESCRIPTION:END -->

## Implementation Progress (2026-01-20)

### Completed: Drag-and-Drop Visual Feedback for Playlist Tracks

Implemented smooth drag-and-drop reorder animation for tracks within playlist views, matching the sidebar playlist reorder behavior:

**State Variables Added** (`library-browser.js` ~line 47-50):
- `dragY: 0` - current cursor Y position during drag
- `dragStartY: 0` - initial center Y of dragged row

**Helper Functions Added** (`library-browser.js` ~line 1450-1465):
- `isOtherTrackDragging(index)` - returns true if another track is being dragged
- `getTrackDragTransform(index)` - returns `translateY(offset)` for dragged track to follow cursor

**HTML Track Row Styling** (`index.html` ~line 621-631):
- Dragged track: `bg-card shadow-lg z-10 relative` (highlighted with shadow)
- Other tracks: `opacity-50` (dimmed)
- Inline transform style for dragged track to follow cursor with `transition: none`

**CSS Transition** (`styles.css`):
```css
[data-track-id] {
  transition: transform 0.15s ease-out;
}
```

**Pattern Matches Sidebar Playlist Reorder:**
1. On drag start: capture `startY` = element center, set `dragY` = cursor position
2. On move: update `dragY`, calculate drop target index
3. Transform calculation: `offsetY = dragY - dragStartY` (simple delta)
4. Dragged item: highlighted + follows cursor (inline transform)
5. Other items: dimmed + shift with CSS transition

### Bug Identified: Incorrect Default Sort Column

**Issue:** When opening a playlist view, the Title column is being activated as the sort column. 

**Expected:** Playlist tracks should be sorted by timestamp order (the order they were added/arranged) until the user manually rearranges tracks via drag-and-drop. The track position column should reflect this ordering.

**To Investigate:**
- Check what triggers column sort activation when switching to playlist view
- Playlist tracks should maintain their stored order, not default to title sort
- May need to disable auto-sort or use a "custom order" sort mode for playlists
<!-- SECTION:NOTES:END -->
