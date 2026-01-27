---
id: task-192
title: Add delay before playlist reorder activation
status: Done
assignee: []
created_date: '2026-01-22 16:31'
updated_date: '2026-01-24 22:28'
labels:
  - frontend
  - playlists
  - ux
dependencies: []
priority: low
ordinal: 49382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Playlists in the sidebar trigger reorder mode immediately on mousedown, which causes accidental reordering when users just want to click to select a playlist.

**Solution:**
Add a delay/threshold before reorder mode activates:
- 150ms hold time OR 5px movement distance required
- Quick clicks pass through to normal playlist selection
- Global flags track reorder state to prevent click handler conflicts
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Quick clicks select playlists without triggering reorder
- [x] #2 Hold or movement activates reorder mode
- [x] #3 Reorder functionality still works as expected
<!-- AC:END -->
