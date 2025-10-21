---
id: task-062
title: Auto-resize columns on double-click separator
status: Done
assignee: []
created_date: '2025-10-21 21:29'
updated_date: '2025-10-21 21:51'
labels: []
dependencies: []
---

## Description

Add ability to double-click column separators to automatically resize columns based on longest content, similar to Excel behavior

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Double-clicking a column separator resizes that column to fit its longest content
- [x] #2 Track number column should resize to ~3 characters width
- [x] #3 Title, artist, album columns should resize to accommodate their longest strings
- [x] #4 Feature works in both library view and queue view
- [x] #5 Visual feedback indicates when hovering over resizable column separator
<!-- AC:END -->

## Implementation Notes

Implemented auto-resize on double-click column separator. Track/title/artist/album columns only expand (never shrink). Year and similar columns can shrink to fit. Works across all playlist views (Music, Liked Songs, Recently Added, etc.)

Implemented auto-resize on double-click column separator. Track/year columns can shrink to fit (track: 15-30px, year: 60-100px). Title/artist/album columns only expand, never shrink. Works across all playlist views.
