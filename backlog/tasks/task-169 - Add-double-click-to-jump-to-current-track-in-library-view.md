---
id: task-169
title: Add double-click to jump to current track in library view
status: Done
assignee: []
created_date: '2026-01-19 05:21'
updated_date: '2026-01-19 05:39'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement feature to jump to the currently playing track by double-clicking the track display in the bottom player bar, but only when in the music library view. Prevent text selection/highlighting when double-clicking by using select-none CSS class like playlist items. Use cursor-default to show arrow cursor.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Double-clicking track display in bottom bar scrolls to current track in library view
- [x] #2 Feature only works in library view, no action in other views
- [x] #3 Playwright test added to verify functionality
- [x] #4 Smooth scrolling behavior matches existing navigation

- [x] #5 Double-clicking does not highlight/select text in the track display

- [x] #6 Uses default arrow cursor (cursor-default)
<!-- AC:END -->
