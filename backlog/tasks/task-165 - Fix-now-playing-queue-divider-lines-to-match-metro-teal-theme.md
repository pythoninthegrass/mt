---
id: task-165
title: Fix now playing queue divider lines to match metro-teal theme
status: Done
assignee: []
created_date: '2026-01-18 00:05'
updated_date: '2026-01-24 22:28'
labels:
  - ui
  - styling
  - bug
dependencies: []
priority: low
ordinal: 1382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The "up next" now playing queue currently has white dividing lines between tracks, but these should be #323232 to match the rest of the metro-teal theme.

**Current behavior:**
- White divider lines between tracks in the now playing queue

**Expected behavior:**
- Divider lines should use #323232 (theme-consistent gray)

**Location:**
- Component: Now playing queue / "up next" view
- Likely file: Look in `src/` directory for queue/now-playing related components
- CSS/styling: Check for border colors, divider elements in the relevant component
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Divider lines between tracks in the now playing queue use #323232 color
- [ ] #2 Visual consistency with the rest of the metro-teal theme is maintained
- [ ] #3 Changes are tested in both light and normal viewing conditions
- [ ] #4 No other styling regressions in the now playing queue component
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Updated the queue item divider border color in app/frontend/index.html:801 to be theme-aware:
- Light theme: border-[#E5E5E5]
- Dark theme: dark:border-[#323232]

Previously used border-border/50 which was too bright/white. Now uses specific hex colors that match the metro-teal theme for both light and dark modes.
<!-- SECTION:NOTES:END -->
