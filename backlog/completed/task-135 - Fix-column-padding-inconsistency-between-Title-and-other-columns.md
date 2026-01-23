---
id: task-135
title: Fix column padding inconsistency between Title and other columns
status: Done
assignee: []
created_date: '2026-01-15 06:24'
updated_date: '2026-01-15 21:40'
labels:
  - ui
  - css
  - polish
  - library-view
dependencies: []
priority: low
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem
The Title column visually appears to have more space between its left border and text content compared to Artist, Album, and Time columns. Users expect consistent padding across all columns.

## Current Implementation
- All non-index columns use `px-4` (16px) padding on both left and right sides
- Index (#) column uses `px-2` (8px) padding
- Header cells have `border-r border-border` for vertical column dividers
- Data rows use CSS Grid with `grid-template-columns` from `getGridTemplateColumns()`
- Title column uses `minmax(320px, 1fr)` to fill available space; other columns use fixed pixel widths

## What Has Been Tried
1. **Changed padding from px-3 to px-4** - Increased padding for all non-index columns, but visual inconsistency persists
2. **Removed gap-2 from title flex container** - Changed to `mr-2` on play indicator to avoid spacing when indicator is hidden
3. **Verified same padding classes** - Both header and data rows use identical padding logic (`col.key === 'index' ? 'px-2' : 'px-4'`)

## Suspected Causes
1. **Visual illusion from column width differences** - Title column expands with `1fr`, making the same 16px padding appear proportionally smaller compared to narrower fixed-width columns
2. **Nested flex container in Title** - Title data cells have `<span class="flex items-center">` wrapper that other columns don't have
3. **Border positioning** - Borders are on the RIGHT side of each column (`border-r`), which may create different visual perception

## Relevant Files
- `app/frontend/index.html` - Header and data row templates (lines ~297-320 for header, ~420-458 for data)
- `app/frontend/js/components/library-browser.js` - `getGridTemplateColumns()` function (lines ~121-130)

## Suggested Investigation
1. Use browser DevTools to measure actual rendered padding values
2. Consider using `pl-X pr-Y` (asymmetric padding) instead of `px-X`
3. Test removing the flex wrapper from Title column to see if it affects alignment
4. Consider adding left border to columns instead of right border to change visual anchor point
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Solution Implemented

Fixed the excessive whitespace between Time column text and scrollbar, and standardized padding across all columns.

### Root Cause

The Time (duration) column had two issues:
1. **1fr expansion**: As the last column, it used `minmax(${actualWidth}px, 1fr)` in the CSS Grid, causing it to expand to fill all remaining space
2. **Inconsistent padding**: Duration column used `px-3` (12px) while other columns used `px-4` (16px)

### Changes Made

**library-browser.js**:
- Removed `1fr` expansion from `getGridTemplateColumns()` - all columns now use fixed widths
- Increased duration default width from 56px to 68px to account for increased padding
- Updated comment to clarify that all columns use fixed widths for consistent spacing

**index.html**:
- Changed duration column padding from `px-3` to `px-4` for consistency (2 locations: header line 346, data rows line 485)
- All non-index columns now use uniform `px-4` padding

### Result

- Time column now has appropriate width (68px) without excessive expansion
- Consistent 16px padding across all columns (except index which uses 8px)
- No more ~50px of wasted space between time text and scrollbar
- Text content: 68px - 32px padding = 36px for "99:59" display

### Files Modified
- `app/frontend/js/components/library-browser.js` (lines 12, 138-147)
- `app/frontend/index.html` (lines 346, 485)

## Additional Fixes (continued)

### Fine-tuning Time Column Width
- Measured actual content width: 30px (not 25px)
- Updated duration width to 40px (30px content + 10px right padding)
- Padding: `pl-[3px] pr-[10px]` (3px left, 10px right)

### Fixed Horizontal Whitespace Issue
- **Problem**: Empty whitespace appearing past the table on the right side
- **Solution**: Made Title column use `minmax(320px, 1fr)` to expand and fill remaining space
- This pushes Time column to the right edge while keeping it at fixed 40px width
- Excel-style resizing still works because resize handles update `columnWidths` with specific pixel values

### Made Column Headers Sticky
- **Problem**: Headers disappeared when scrolling down, making it hard to identify columns
- **Solution**: Added `sticky top-0 z-10` classes to `.library-header-container`
- Headers now remain visible at the top while scrolling through track list

### Final Configuration
- Time column: **40px total** (30px content + 3px left + 10px right padding)
- Title column: Flexible with `minmax(320px, 1fr)` - expands to fill available space
- All other columns: Fixed widths for Excel-style independent resizing
- Headers: Sticky positioned for always-visible column labels

## Header Context Menu Fix

- Changed context menu background from `hsl(var(--popover))` to `hsl(var(--background))` for opaque background
- Replaced `.context-menu` CSS class with explicit Tailwind classes (`bg-card`, `z-100`, etc.)
- Changed `@click.outside` to `@click.away` for proper Alpine.js v3 click-outside behavior
- Added guards in `handleSort()` and `startColumnDrag()` to prevent actions while context menu is open
- Clicking outside now only closes the menu without triggering sort/drag operations
<!-- SECTION:NOTES:END -->
