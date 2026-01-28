---
id: task-228
title: 'E2E: Progress bar seeking tests'
status: Done
assignee: []
created_date: '2026-01-28 05:40'
updated_date: '2026-01-28 05:46'
labels:
  - e2e
  - playback
  - P1
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add Playwright E2E tests for progress bar seeking interactions. Currently tests verify progress display but not click-to-seek or drag-scrubbing interactions.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Click on progress bar seeks to position
- [x] #2 Drag scrubbing updates position in real-time
- [x] #3 Seek while paused doesn't auto-play
- [x] #4 Seek near end of track behavior
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

Added comprehensive E2E tests for progress bar seeking interactions in `app/frontend/tests/playback.spec.js`.

### Test Suite: "Progress Bar Seeking Tests (task-228) @tauri"

**5 new tests added:**

1. **Click-to-seek at multiple positions** (AC #1)
   - Tests seeking to 25%, 50%, and 75% positions
   - Verifies position accuracy within tolerance
   - Confirms playback continues after seek

2. **Real-time drag scrubbing** (AC #2)
   - Tests drag from 20% to 80% in steps
   - Verifies `dragPosition` updates during drag (real-time tracking)
   - Confirms final position matches drag target
   - Ensures playback continues after drag

3. **Seek while paused doesn't auto-play** (AC #3)
   - Tests both click-to-seek and drag-to-seek while paused
   - Verifies position changes but playback remains paused
   - Critical for preserving user intent

4. **Seek near end of track** (AC #4)
   - Tests seeking to 95% and 99% positions
   - Verifies position accuracy at track boundaries
   - Handles edge cases (auto-advance vs. stay at end)

5. **Rapid seek operations** (bonus robustness test)
   - Tests rapid clicking at different positions
   - Verifies player state remains consistent
   - Ensures no race conditions or state corruption

### Test Configuration

- Tagged with `@tauri` (requires Tauri runtime for audio playback)
- Runs in E2E_MODE=tauri only (excluded from fast/full modes)
- Tests run across all 3 browsers: chromium, webkit, firefox
- Total: 15 test cases (5 tests × 3 browsers)

### Running the Tests

```bash
# List the new tests
E2E_MODE=tauri npx playwright test tests/playback.spec.js --grep "Progress Bar Seeking Tests" --list

# Run with all browsers (requires Tauri running)
E2E_MODE=tauri npx playwright test tests/playback.spec.js --grep "Progress Bar Seeking Tests"

# Run with webkit only (faster)
E2E_MODE=tauri npx playwright test tests/playback.spec.js --grep "Progress Bar Seeking Tests" --project=webkit
```

### Technical Details

**Progress bar implementation** (app/frontend/js/components/player-controls.js):
- `handleProgressClick()` - Click-to-seek implementation
- `handleProgressDragStart()` - Initiates drag scrubbing
- `handleProgressDrag()` - Updates drag position in real-time
- `updateDragPosition()` - Calculates position from mouse coordinates
- Mouseup event listener - Finalizes seek on drag release

**Player store** (app/frontend/js/stores/player.js):
- `seek(positionMs)` - Seeks to position without changing play/pause state
- Debounced for performance (50ms delay)
- Preserves play/pause state (critical for AC #3)

All acceptance criteria have been implemented and verified.
<!-- SECTION:NOTES:END -->
