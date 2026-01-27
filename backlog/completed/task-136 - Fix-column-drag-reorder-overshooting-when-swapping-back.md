---
id: task-136
title: Fix column drag reorder overshooting when swapping back
status: Done
assignee: []
created_date: '2026-01-15 08:38'
updated_date: '2026-01-24 22:28'
labels:
  - bug
  - frontend
  - column-customization
dependencies: []
priority: medium
ordinal: 16382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When dragging a column (e.g., Artist) to swap with an adjacent column (e.g., Album), then trying to drag it back to its original position, the drag overshoots and swaps with a different column (e.g., Time).

Example reproduction:
1. Default order: # | Title | Artist | Album | Time
2. Drag Album left to swap with Artist → # | Title | Album | Artist | Time ✓
3. Drag Artist left to swap back with Album → # | Title | Artist | Time | Album ✗ (Time got pulled in)

The issue persists despite multiple refactoring attempts to the `updateColumnDropTarget()` function.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Dragging Album left to swap with Artist works correctly
- [x] #2 Dragging Artist back right to swap with Album returns to original order (no Time involvement)
- [x] #3 Column reorder test passes: should reorder columns by dragging
- [x] #4 Sort toggle is not triggered after column drag
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Attempts Made

### 1. Original 50% midpoint threshold
- Swap triggered at column midpoint
- Issue: Required dragging too far, easy to overshoot

### 2. Changed to 30% threshold
- Reduced distance needed to trigger swap
- Issue: Still overshooting

### 3. Changed to 5% edge threshold (both sides)
- Trigger swap when entering 5% from either edge
- Issue: Logic was checking if cursor was INSIDE the zone, not entering it

### 4. Refactored to check entry from correct direction
- Dragging right: trigger at 5% from left edge of target
- Dragging left: trigger at 95% from left edge (5% from right)
- Issue: Loop continued checking ALL columns, causing distant swaps

### 5. Split into two separate loops (current state)
- One loop for columns to the right (ascending order)
- One loop for columns to the left (descending order)
- Each loop breaks when cursor doesn't pass trigger point
- Issue: Still overshooting when dragging back

## Possible Next Steps
1. Track the visual position of the dragged column element during drag (not just cursor position)
2. Only allow swapping with immediately adjacent columns (no skipping)
3. Add hysteresis - require cursor to move back past a threshold before allowing reverse swap
4. Consider using a different approach like insertion point indicator instead of live swapping
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Current Code (library-browser.js ~line 366)
```javascript
updateColumnDropTarget(x) {
  const header = document.querySelector('[data-testid="library-header"]');
  if (!header) return;

  const cells = header.querySelectorAll(':scope > div');
  const dragIdx = this.columns.findIndex(c => c.key === this.draggingColumnKey);
  let newOverIdx = dragIdx;

  const edgeThreshold = 0.05;

  for (let i = dragIdx + 1; i < cells.length; i++) {
    const rect = cells[i].getBoundingClientRect();
    const triggerX = rect.left + rect.width * edgeThreshold;
    if (x > triggerX) {
      newOverIdx = i + 1;
    } else {
      break;
    }
  }

  for (let i = dragIdx - 1; i >= 0; i--) {
    const rect = cells[i].getBoundingClientRect();
    const triggerX = rect.right - rect.width * edgeThreshold;
    if (x < triggerX) {
      newOverIdx = i;
    } else {
      break;
    }
  }

  this.dragOverColumnIdx = newOverIdx;
}
```

## Related Changes Made in This Session
- Added `wasColumnDragging` flag to prevent sort toggle after drag
- Only set flag if mouse moved >5px (so clicks still trigger sort)
- Click handler updated: `@click="if (!draggingColumnKey && !wasResizing && !wasColumnDragging) handleSort(col.key)"`

## Files Involved
- `app/frontend/js/components/library-browser.js` - updateColumnDropTarget(), finishColumnDrag(), startColumnDrag()
- `app/frontend/index.html` - column header click handler

## Solution Implemented

Fixed the overshooting bug in `updateColumnDropTarget()` function in library-browser.js:366-403.

### Root Causes Identified
1. **Both loops always ran**: Right loop ran first, then left loop could override the result
2. **Wrong insertion index**: Right loop used `newOverIdx = i + 1` instead of `newOverIdx = i`
3. **Multi-column jumping**: Loops continued checking ALL columns, allowing drag to skip over multiple columns

### Changes Made

**library-browser.js**:
- Changed `newOverIdx = i + 1` to `newOverIdx = i` in right loop (line 381)
- Added `break` immediately after setting newOverIdx in right loop (line 382)
- Added condition to only run left loop if no target found in right loop (line 389)
- Added `break` after setting newOverIdx in left loop (line 395)

This ensures:
- Only immediately adjacent columns can be swapped (no skipping)
- Only one loop sets the target (prevents conflicting updates)
- Consistent behavior: both loops use `newOverIdx = i` to target the column at index i

### Tests Added

**tests/library.spec.js**:
- Added comprehensive test case: "should not overshoot when dragging column back to original position" (lines 765-832)
- Test reproduces exact bug scenario:
  1. Drag Album left to swap with Artist
  2. Drag Album right back to original position
  3. Verify Album ends up adjacent to Artist, not overshooting to after Time

### Verification

✅ Manual testing in Tauri app - confirmed working
✅ Playwright test "should not overshoot when dragging column back to original position" - PASSED
✅ Playwright test "should reorder columns by dragging" - PASSED
✅ All acceptance criteria met
<!-- SECTION:NOTES:END -->
