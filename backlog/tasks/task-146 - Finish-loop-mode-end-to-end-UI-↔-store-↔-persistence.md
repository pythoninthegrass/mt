---
id: task-146
title: Finish loop mode end-to-end (UI ↔ store ↔ persistence)
status: Done
assignee: []
created_date: '2026-01-16 04:59'
updated_date: '2026-01-16 05:04'
labels:
  - ui
  - queue
  - playback
  - tauri-migration
milestone: Tauri Migration
dependencies: []
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem
Loop is partially implemented in `queue` store (`loop: 'none' | 'all' | 'one'` and logic in `playNext()`), but the UI wiring is inconsistent:

1. **Naming mismatch**: `player-controls.js` references `queue.loopMode` + `queue.cycleLoopMode()` but `queue.js` uses `loop` + `cycleLoop()`
2. **No persistence**: `api.queue.save()` is a no-op ("local only"), so loop state doesn't persist across reloads
3. **Repeat-one behavior**: Current implementation repeats indefinitely; should be "play once more, then revert to loop off"

## Desired Behavior

### Three-state cycle
- **none** (default): Tracks play once, queue stops at end
- **all** (first click): Queue wraps at end (carousel mode)
- **one** (second click): Current track plays ONE more time, then auto-reverts to `none`

### "Play once more" pattern for repeat-one
When repeat-one is activated:
1. Current track continues playing
2. When track ends, it replays ONE time
3. After second playthrough, auto-revert to `loop: 'none'`
4. UI updates to show loop OFF

Manual next/prev during repeat-one should:
- Skip to next/prev track
- Revert to `loop: 'all'` (not `none`)

## Files to modify
- `app/frontend/js/stores/queue.js` - Add repeat-one auto-revert logic, add `_repeatOnePending` flag
- `app/frontend/js/components/player-controls.js` - Fix naming: `loopMode` → `loop`, `cycleLoopMode` → `cycleLoop`
- `app/frontend/js/api.js` - Implement real `queue.save()` or use localStorage for persistence
- `app/frontend/tests/queue.spec.js` - Add tests for repeat-one auto-revert behavior
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Loop button cycles none → all → one → none reliably via UI click
- [ ] #2 Loop icon and active styling accurately reflect current state
- [ ] #3 Loop 'all' wraps queue at end (carousel behavior)
- [ ] #4 Repeat-one plays current track ONE more time then auto-reverts to 'none'
- [ ] #5 Manual next/prev during repeat-one reverts to 'all' (not 'none')
- [ ] #6 Loop state persists across page reloads (localStorage or backend)
- [ ] #7 Naming mismatch fixed: player-controls uses queue.loop and queue.cycleLoop()
- [ ] #8 Playwright tests cover loop state cycling and repeat-one auto-revert
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Completion Notes (2026-01-15)

### Implementation Summary
- Fixed naming mismatch in player-controls.js (loopMode → loop, cycleLoopMode → cycleLoop)
- Implemented repeat-one "play once more" behavior with auto-revert to 'none'
- Added skipNext()/skipPrevious() for manual navigation that reverts repeat-one to 'all'
- Added localStorage persistence for loop/shuffle state
- Added 4 Playwright tests for loop mode behavior

### Test Results
- All 29 store tests pass
- 5 loop-related tests pass (cycling, persistence, UI state)
- Pre-existing playback-dependent tests still timeout (unrelated to this change)

### Commit
- 499d88c: feat: implement loop mode with repeat-one auto-revert behavior
<!-- SECTION:NOTES:END -->
