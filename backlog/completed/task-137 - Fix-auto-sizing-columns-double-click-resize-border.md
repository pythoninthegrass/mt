---
id: task-137
title: Fix auto-sizing columns (double-click resize border)
status: Done
assignee: []
created_date: '2026-01-15 21:41'
updated_date: '2026-01-15 22:09'
labels:
  - bug
  - ui
  - library-view
  - column-resize
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem
Double-clicking a column border to auto-fit the column width is not working. This feature should measure the content width of all cells in a column and resize the column to fit the widest content.

## Expected Behavior
- Double-click on a column border (resizer)
- Column should resize to fit its widest content plus padding
- Works for all columns including Title, Artist, Album, etc.

## Current Behavior
- Double-clicking doesn't resize the column
- Unknown if the `autoFitColumn` function is even being called

## Debugging Added
Console.log statements have been added to `autoFitColumn()` in `library-browser.js`:
- `[autoFit] CALLED for column: {key}` - at function entry
- `[autoFit] Column: {key}, rows found: {count}, minWidth: {min}` - after row selection
- `[autoFit] idealWidth: {width}, current: {current}` - before setting
- `[autoFit] Done. New width: {width}` - after setting

## Investigation Steps
1. Check browser console when double-clicking a column border
2. Verify if `[autoFit] CALLED` message appears
3. If not appearing: event handler issue (dblclick not firing)
4. If appearing but no resize: logic issue in width calculation

## Relevant Code
- `app/frontend/index.html` lines 364, 372 - dblclick handlers on resizers
- `app/frontend/js/components/library-browser.js` - `autoFitColumn()` function (line ~613)

## Possible Causes
1. Event not firing (mousedown/resize interference)
2. Event propagation being stopped
3. Column width set but immediately overridden
4. `data-column` attribute not matching elements
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Double-clicking column border auto-fits column to content width
- [x] #2 Auto-fit produces reasonable widths (not absurdly large)
- [x] #3 All existing Playwright tests pass
- [x] #4 Context menu functionality unaffected
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Root Cause Analysis

The auto-fit function was measuring `row.textContent` which included all whitespace from Alpine.js template markup (newlines, indentation). The canvas `measureText()` was measuring this entire string including whitespace, resulting in absurdly large widths (e.g., 756px for an index column that should be ~48px).

## Fix Applied

1. **Trim text content**: Changed `row.textContent || ''` to `(row.textContent || '').trim()` to remove whitespace from Alpine templates before measuring.

2. **Immutable state update**: Changed `this.columnWidths[col.key] = idealWidth` to `this.columnWidths = { ...this.columnWidths, [col.key]: idealWidth }` to ensure Alpine reactivity triggers properly.

3. **Removed debug logging**: Cleaned up console.log statements that were added for investigation.

## Verification

- Tested via Playwright MCP: index column now auto-fits to ~48px (was 756px before fix)
- All 50 existing Playwright tests pass with no regressions
- Context menu and library view rendering unaffected
<!-- SECTION:NOTES:END -->
