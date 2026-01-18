---
id: task-166
title: >-
  Add back/forward navigation arrows to metadata editor for sequential track
  editing
status: Done
assignee: []
created_date: '2026-01-18 00:21'
updated_date: '2026-01-18 03:28'
labels:
  - feature
  - ui
  - metadata
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add left/right arrow navigation to the metadata editor modal that allows sequential editing of tracks in library order.

## Background
When editing metadata for multiple tracks (e.g., 20 tracks on an album missing title info), users currently must close the modal and reselect each track individually. This feature enables "assembly line" editing by adding navigation arrows.

## Requirements

### UI Changes
- Add ◀ / ▶ arrow buttons in the metadata modal header
- Show arrows when modal is opened from multi-select (and keep them available after collapsing to single-track)
- Add track position indicator (e.g., "2 / 1470" showing position in library view)
- Add data-testid attributes: `metadata-nav-prev`, `metadata-nav-next`, `metadata-nav-indicator`

### Navigation Behavior
- ArrowLeft/ArrowRight keys navigate to previous/next track in `library.filteredTracks` order
- Plain arrow keys always navigate (even when focused in input fields - intentionally overrides cursor movement)
- Navigation deselects other tracks in library UI, selecting only the adjacent track
- Modal switches from batch edit to single-track edit on first navigation
- Arrows remain available for continued sequential navigation after collapse to single-track

### Auto-save on Navigation
- Auto-save current edits (batch or single) before navigating
- If save fails, show error toast and block navigation
- Silent success (no toast spam on each arrow press)

### Edge Cases
- Disable prev arrow at first track in library
- Disable next arrow at last track in library
- Scroll library view to keep current track visible

## Technical Implementation

### Files to modify
- `app/frontend/js/components/metadata-modal.js` - Add navigation state, methods, keyboard handling
- `app/frontend/js/components/library-browser.js` - Pass `anchorTrackId` when opening modal
- `app/frontend/index.html` - Add arrow buttons and indicator to modal header
- `app/frontend/tests/library.spec.js` - Add Playwright tests for navigation

### Key changes
1. Refactor `save()` to support `{ close: boolean }` for save-without-closing
2. Add `navigationEnabled` state (true when opened from multi-select)
3. Add `currentTrackId` to track position in library
4. Add `navigate(delta)` method with auto-save logic
5. Update library selection from modal via Alpine.$data()
6. Add ArrowLeft/ArrowRight handling in `handleKeydown()`
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Multi-select tracks and open metadata modal shows navigation arrows in header
- [x] #2 ArrowRight key navigates to next track in library order (auto-saves first)
- [x] #3 ArrowLeft key navigates to previous track in library order (auto-saves first)
- [x] #4 Navigation deselects other tracks, leaving only the navigated-to track selected
- [x] #5 Arrow keys work even when cursor is in an input field
- [x] #6 Track position indicator shows current position (e.g., '5 / 20')
- [ ] #7 Prev arrow disabled at first track, Next arrow disabled at last track
- [ ] #8 Library view scrolls to keep current track visible during navigation
- [ ] #9 Save failure blocks navigation and shows error toast
- [x] #10 Playwright tests cover multi-select navigation workflow
<!-- AC:END -->
