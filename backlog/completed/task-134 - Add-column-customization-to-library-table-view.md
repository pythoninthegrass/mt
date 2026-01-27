---
id: task-134
title: Add column customization to library table view
status: Done
assignee: []
created_date: '2026-01-15 02:48'
updated_date: '2026-01-24 22:28'
labels:
  - enhancement
  - frontend
  - ui
  - database
dependencies: []
priority: medium
ordinal: 17382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Users need to customize the library table columns to view the information that matters most to them and adjust column widths for better readability. Currently, columns have fixed widths and visibility, which doesn't accommodate different screen sizes or user preferences for organizing their music library.

This task adds column customization features including resizing, reordering, toggling visibility, and auto-fitting column widths. All customizations should persist across application restarts.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 User can resize any column by dragging the right edge of the column header horizontally
- [x] #2 User can double-click a column header to auto-fit the column width based on the longest content string (up to a reasonable maximum)
- [x] #3 User can right-click the header row to open a context menu with column visibility toggles
- [x] #4 User can show/hide individual columns through the context menu
- [x] #5 Column customizations (widths, visibility, order) persist to the database and restore on application restart
- [x] #6 Minimum column width prevents columns from becoming unusably narrow
- [x] #7 Column resize cursor provides visual feedback when hovering over resizable column edges
- [x] #8 At least one column remains visible at all times (user cannot hide all columns)
<!-- AC:END -->
