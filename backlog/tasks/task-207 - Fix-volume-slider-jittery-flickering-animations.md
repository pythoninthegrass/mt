---
id: task-207
title: Fix volume slider jittery/flickering animations
status: Done
assignee: []
created_date: '2026-01-25 22:10'
updated_date: '2026-01-25 22:52'
labels:
  - bug
  - frontend
  - ui-polish
  - alpine
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The volume slider has jittery or flickering animations when adjusting the volume. This should be smooth like the progress bar slider.

**Current Behavior:**
- Volume slider exhibits jittery or flickering visual behavior during adjustment
- Animation is not smooth compared to the progress bar slider

**Expected Behavior:**
- Volume slider should have smooth animations like the progress bar
- No visual flickering or jittering during volume adjustments
- Consistent animation behavior across both sliders

**User Value:**
Users get a polished, professional UI experience with smooth slider interactions that don't cause visual distractions or perceived performance issues.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Volume slider animations are smooth without jittering or flickering
- [x] #2 Volume slider animation behavior matches progress bar slider smoothness
- [x] #3 No visual artifacts during volume adjustments
- [x] #4 Volume changes respond promptly to user input without lag
- [x] #5 Playwright E2E test verifies smooth volume slider interaction
- [x] #6 Visual regression test captures slider behavior for comparison
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

Fixed jittery/flickering volume slider animations by removing unnecessary CSS transitions that were causing visual artifacts.

### Root Cause
The volume slider had two problematic transitions:
1. `transition-opacity` class on the slider thumb (handle)
2. Alpine.js `x-transition` directives on the tooltip

These transitions caused flickering/jittering during volume adjustments because the opacity changes were animated, creating visual lag.

### Solution
Removed both transitions to match the progress bar slider's instant opacity toggle approach:

**Changes in `app/frontend/index.html`:**
- Removed `transition-opacity` from volume slider thumb (line 1699)
- Removed `x-transition:enter`, `x-transition:enter-start`, and `x-transition:enter-end` from volume tooltip (lines 1705-1707)

**Test Coverage in `app/frontend/tests/playback.spec.js`:**
- Added E2E test "should smoothly adjust volume when dragging slider" 
- Test simulates 10-step drag gesture from 20% to 80% of volume bar
- Verifies volume updates correctly and thumb visibility on hover
- Runs in @tauri mode with full backend integration

### Technical Details
The progress bar slider works smoothly because it uses instant opacity toggles without CSS transitions:
```html
<div class="... rounded-full" :class="hasTrack ? 'opacity-100' : 'opacity-0'">
```

The volume slider now uses the same approach:
```html
<div class="... rounded-full" :class="isDraggingVolume ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'">
```

### Commits
- `3ce4b8b` - fix(ui): remove jittery animations from volume slider
- `48257ac` - test(playback): add E2E test for smooth volume slider dragging

## Additional Fix: Volume Bounce-Back on Release

### Issue
After the initial animation fix, intermittent bounce-back still occurred when rapidly dragging or clicking the volume slider. The thumb would briefly snap back to the old position before jumping to the new position.

### Root Cause
Two-part timing issue:
1. **Player-controls component**: On mouseup, `isDraggingVolume` was cleared immediately, then `commitVolume()` was called with a 30ms debounce
2. **Player store**: `setVolume()` updated `this.volume` AFTER awaiting the Tauri backend call

This created a race condition:
- mouseup → `isDraggingVolume = false` → `displayVolume` switches from `dragVolume` to `player.volume` (old value)
- 30ms later → backend called
- ~50-100ms later → `player.volume` updates
- Visual result: thumb bounces from drag position → old position → new position

### Solution
**Part 1: Immediate commit on mouseup** (`player-controls.js`)
- Clear any pending debounce timer
- Call `player.setVolume()` immediately without delay
- Then clear `isDraggingVolume` state
- Debounce still applies during continuous dragging to avoid backend spam

**Part 2: Optimistic volume update** (`player.js`)
- Update `this.volume` BEFORE awaiting the Tauri invoke call
- UI updates instantly while backend processes asynchronously
- If backend fails, error is logged but volume stays at new value

### Result
Volume slider now stays exactly where user releases it, even with rapid dragging or clicking.

### Additional Commits
- `23a8104` - fix(player): update volume optimistically for immediate UI feedback
- `470f267` - fix(player-controls): commit volume immediately on drag release

## Enhanced Test Coverage

Added comprehensive E2E tests to prevent regression:

**Test Suite: Volume Controls @tauri**

1. **should smoothly adjust volume when dragging slider**
   - Tests smooth 10-step drag from 20% to 80%
   - Validates volume updates and thumb visibility
   - Basic drag functionality test

2. **should not bounce back when rapidly clicking volume slider**
   - Rapidly clicks 5 different positions (20%, 80%, 50%, 90%, 30%)
   - Only 50ms between clicks to simulate rapid user interaction
   - Validates volume matches clicked position each time
   - Tests optimistic volume update prevents visual lag

3. **should handle rapid drag direction changes without bounce-back**
   - Drags with rapid direction changes (80%, 30%, 90%, 20%, 70%)
   - Only 5ms between position changes
   - Validates final volume matches release position (70%)
   - Tests immediate volume commit on mouseup

These tests cover all three aspects of the fix:
- CSS transition removal (smooth animations)
- Optimistic volume updates (immediate UI feedback)
- Immediate commit on mouseup (no bounce-back)

### Commit
- `51f54d7` - test(playback): add E2E tests for rapid volume slider interactions
<!-- SECTION:NOTES:END -->
