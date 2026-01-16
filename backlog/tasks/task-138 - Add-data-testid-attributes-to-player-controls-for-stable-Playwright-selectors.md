---
id: task-138
title: Add data-testid attributes to player controls for stable Playwright selectors
status: Done
assignee: []
created_date: '2026-01-16 04:03'
updated_date: '2026-01-16 04:08'
labels:
  - testing
  - ui
  - playwright
  - foundation
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem
Current Playwright tests rely on fragile selectors like `button[title="Next"]` and CSS class selectors. These break easily during UI refactoring.

## Solution
Add `data-testid` attributes to key player control elements in `app/frontend/index.html`:

### Player controls footer (~line 717+)
- `data-testid="player-prev"` - Previous button
- `data-testid="player-playpause"` - Play/Pause button  
- `data-testid="player-next"` - Next button
- `data-testid="player-progressbar"` - Progress bar container (the clickable area)
- `data-testid="player-time"` - Time display element
- `data-testid="player-volume"` - Volume slider
- `data-testid="player-mute"` - Mute button
- `data-testid="player-shuffle"` - Shuffle button
- `data-testid="player-loop"` - Loop button

### Queue view (~line 556+)
- `data-testid="queue-clear"` - Clear queue button
- `data-testid="queue-shuffle"` - Shuffle queue button (in queue view header)
- `data-testid="queue-count"` - Track count display

## Acceptance Criteria
<!-- AC:BEGIN -->
- All listed testids are added to index.html
- Existing Playwright tests still pass
- No visual or functional changes to the UI
<!-- SECTION:DESCRIPTION:END -->

- [ ] #1 All player control testids added to index.html
- [ ] #2 All queue view testids added
- [ ] #3 Existing Playwright tests pass
- [ ] #4 No visual or functional UI changes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Completed: Added data-testid attributes to all player controls and queue view elements in index.html. Fixed duration width tests to expect 52px (matching new MIN_DURATION_WIDTH). All 67 library tests pass.
<!-- SECTION:NOTES:END -->
